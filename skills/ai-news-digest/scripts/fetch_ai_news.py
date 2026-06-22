#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    enabled: bool = True
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Item:
    source: str
    source_tags: tuple[str, ...]
    title: str
    link: str
    published: Optional[datetime]
    summary: str


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _canonicalize_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception:
        return url
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    drop_prefixes = ("utm_", "mc_", "ref", "source")
    query = [(k, v) for (k, v) in query if not any(k.lower().startswith(p) for p in drop_prefixes)]
    query.sort()
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment))


def _parse_since(since: str, now: datetime) -> datetime:
    since = since.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", since):
        return datetime.fromisoformat(since).replace(tzinfo=now.tzinfo)
    m = re.fullmatch(r"(\d+)(h|d)", since.lower())
    if not m:
        raise ValueError("Invalid --since. Use like 72h, 3d, or YYYY-MM-DD.")
    n = int(m.group(1))
    unit = m.group(2)
    delta = timedelta(hours=n) if unit == "h" else timedelta(days=n)
    return now - delta


def _parse_datetime(text: str) -> Optional[datetime]:
    text = (text or "").strip()
    if not text:
        return None
    # RFC 822 / RFC 1123 (common in RSS)
    try:
        dt = parsedate_to_datetime(text)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    # ISO 8601 (common in Atom)
    try:
        cleaned = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _fetch_bytes(url: str, timeout_s: int) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ai-news-digest/0.1 (+https://openai.com)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


def _text(elem: Optional[ET.Element]) -> str:
    if elem is None:
        return ""
    return (elem.text or "").strip()


def _find_first(elem: ET.Element, candidates: Iterable[str]) -> Optional[ET.Element]:
    for tag in candidates:
        found = elem.find(tag)
        if found is not None:
            return found
    return None


def _atom_link(entry: ET.Element) -> str:
    for link in entry.findall("{*}link"):
        rel = link.attrib.get("rel", "alternate")
        href = link.attrib.get("href")
        if href and rel in ("alternate", ""):
            return href.strip()
    # fallback to text link
    link = entry.find("{*}link")
    return _text(link)


def _parse_rss(root: ET.Element, source: Source, max_items: int) -> list[Item]:
    channel = root.find("channel")
    if channel is None:
        channel = root.find("{*}channel")
    if channel is None:
        return []

    items: list[Item] = []
    for it in channel.findall("item") + channel.findall("{*}item"):
        title = _strip_html(_text(_find_first(it, ["title", "{*}title"])))
        link = _text(_find_first(it, ["link", "{*}link"]))
        guid = _text(_find_first(it, ["guid", "{*}guid"]))
        if not link and guid.startswith("http"):
            link = guid

        pub = _parse_datetime(_text(_find_first(it, ["pubDate", "{*}pubDate", "date", "{*}date"])))
        summary = _strip_html(
            _text(
                _find_first(
                    it,
                    [
                        "description",
                        "{*}description",
                        "{http://purl.org/rss/1.0/modules/content/}encoded",
                        "{*}encoded",
                    ],
                )
            )
        )

        if title and link:
            items.append(
                Item(
                    source=source.name,
                    source_tags=source.tags,
                    title=title,
                    link=_canonicalize_url(link),
                    published=pub,
                    summary=summary,
                )
            )
        if len(items) >= max_items:
            break
    return items


def _parse_atom(root: ET.Element, source: Source, max_items: int) -> list[Item]:
    items: list[Item] = []
    for entry in root.findall("{*}entry"):
        title = _strip_html(_text(_find_first(entry, ["{*}title"])))
        link = _atom_link(entry)
        updated = _text(_find_first(entry, ["{*}updated", "{*}published"]))
        pub = _parse_datetime(updated)
        summary = _strip_html(
            _text(
                _find_first(
                    entry,
                    [
                        "{*}summary",
                        "{*}content",
                    ],
                )
            )
        )
        if title and link:
            items.append(
                Item(
                    source=source.name,
                    source_tags=source.tags,
                    title=title,
                    link=_canonicalize_url(link),
                    published=pub,
                    summary=summary,
                )
            )
        if len(items) >= max_items:
            break
    return items


def _parse_feed(xml_bytes: bytes, source: Source, max_items: int) -> list[Item]:
    # Some feeds start with a BOM or whitespace
    xml_bytes = xml_bytes.lstrip()
    root = ET.fromstring(xml_bytes)
    tag = root.tag.lower()
    if tag.endswith("rss") or tag.endswith("rdf"):
        return _parse_rss(root, source, max_items=max_items)
    if tag.endswith("feed"):
        return _parse_atom(root, source, max_items=max_items)
    # Try RSS as fallback
    return _parse_rss(root, source, max_items=max_items)


def _load_sources(path: str) -> list[Source]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sources = []
    for s in data.get("sources", []):
        name = (s.get("name") or "").strip()
        url = (s.get("url") or "").strip()
        enabled = bool(s.get("enabled", True))
        tags = tuple((t or "").strip() for t in (s.get("tags") or []) if (t or "").strip())
        if name and url:
            sources.append(Source(name=name, url=url, enabled=enabled, tags=tags))
    if not sources:
        raise ValueError(f"No sources found in {path}")
    return sources


def _items_to_json(items: list[Item]) -> list[dict[str, Any]]:
    out = []
    for it in items:
        out.append(
            {
                "source": it.source,
                "source_tags": list(it.source_tags),
                "title": it.title,
                "link": it.link,
                "published": it.published.isoformat() if it.published else None,
                "summary": it.summary,
            }
        )
    return out


def _split_csv_repeat(values: Optional[list[str]]) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for v in values:
        for part in (v or "").split(","):
            p = part.strip()
            if p:
                out.append(p)
    return out


def _matches_any(text: str, needles: list[str]) -> bool:
    if not needles:
        return True
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)


def _matches_none(text: str, needles: list[str]) -> bool:
    if not needles:
        return True
    t = (text or "").lower()
    return not any(n.lower() in t for n in needles)


def _normalize_title(title: str) -> str:
    t = (title or "").lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _render_markdown(items: list[Item], generated_at: datetime, window_start: datetime, limit: int) -> str:
    def fmt_dt(dt: Optional[datetime]) -> str:
        if not dt:
            return "unknown date"
        local = dt.astimezone(generated_at.tzinfo or timezone.utc)
        return local.strftime("%Y-%m-%d %H:%M")

    lines: list[str] = []
    lines.append(f"# AI News Digest ({window_start.date().isoformat()} → {generated_at.date().isoformat()})")
    lines.append("")
    lines.append(f"- Generated: {generated_at.strftime('%Y-%m-%d %H:%M %Z')}".rstrip())
    lines.append(f"- Window start: {window_start.strftime('%Y-%m-%d %H:%M %Z')}".rstrip())
    shown = len(items) if limit <= 0 else min(len(items), limit)
    lines.append(f"- Items: {shown}")
    lines.append("")

    for it in (items if limit <= 0 else items[:limit]):
        lines.append(f"- [{it.title}]({it.link}) — {it.source} ({fmt_dt(it.published)})")
        if it.summary:
            lines.append(f"  - {it.summary[:240].rstrip()}"+("…" if len(it.summary) > 240 else ""))
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fetch AI news items from RSS/Atom feeds.")
    default_sources = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "references", "sources.json"))
    parser.add_argument("--sources", default=default_sources, help="Path to sources.json")
    parser.add_argument("--since", default="24h", help="Look back window: 24h, 72h, 3d, or YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=0, help="Max items to output (after filtering/dedup). 0 means no limit.")
    parser.add_argument("--max-per-source", type=int, default=0, help="Max items to read per feed. 0 means no limit.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    parser.add_argument("--output", default="-", help="Output file path, or - for stdout")
    parser.add_argument("--timezone", choices=["utc", "local"], default="local")
    parser.add_argument("--keywords", action="append", help="Include if title/summary contains any keyword (repeatable, comma-separated)")
    parser.add_argument("--exclude-keywords", action="append", help="Exclude if title/summary contains any keyword (repeatable, comma-separated)")
    parser.add_argument("--include-tags", action="append", help="Only include items from sources with any tag (repeatable, comma-separated)")
    parser.add_argument("--exclude-tags", action="append", help="Exclude items from sources with any tag (repeatable, comma-separated)")
    parser.add_argument("--require-date", action="store_true", help="Drop items missing published/updated date")
    parser.add_argument("--dedup-by-title", action="store_true", help="Also dedup by normalized title (in addition to link)")
    args = parser.parse_args(argv)

    now = _now_utc()
    if args.timezone == "local":
        generated_at = datetime.now().astimezone()
        now = generated_at.astimezone(timezone.utc)
    else:
        generated_at = now

    try:
        window_start_utc = _parse_since(args.since, now)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    sources = _load_sources(args.sources)
    sources = [s for s in sources if s.enabled]

    all_items: list[Item] = []
    failures: list[dict[str, str]] = []
    for src in sources:
        try:
            xml_bytes = _fetch_bytes(src.url, timeout_s=args.timeout)
            max_items = 10_000_000 if args.max_per_source <= 0 else args.max_per_source
            items = _parse_feed(xml_bytes, src, max_items=max_items)
            all_items.extend(items)
        except Exception as e:
            failures.append({"source": src.name, "url": src.url, "error": f"{type(e).__name__}: {e}"})

        # be polite to feed hosts
        time.sleep(0.15)

    # Filter + sort
    include_keywords = _split_csv_repeat(args.keywords)
    exclude_keywords = _split_csv_repeat(args.exclude_keywords)
    include_tags = [t.lower() for t in _split_csv_repeat(args.include_tags)]
    exclude_tags = [t.lower() for t in _split_csv_repeat(args.exclude_tags)]

    seen_links: set[str] = set()
    seen_titles: set[str] = set()
    filtered: list[Item] = []
    for it in all_items:
        if it.link in seen_links:
            continue
        seen_links.add(it.link)

        if args.dedup_by_title:
            nt = _normalize_title(it.title)
            if nt and nt in seen_titles:
                continue
            if nt:
                seen_titles.add(nt)

        if args.require_date and it.published is None:
            continue

        if it.published and it.published.astimezone(timezone.utc) < window_start_utc:
            continue

        if include_tags and not any(t.lower() in include_tags for t in it.source_tags):
            continue
        if exclude_tags and any(t.lower() in exclude_tags for t in it.source_tags):
            continue

        haystack = f"{it.title}\n{it.summary}"
        if include_keywords and not _matches_any(haystack, include_keywords):
            continue
        if exclude_keywords and not _matches_none(haystack, exclude_keywords):
            continue

        filtered.append(it)

    filtered.sort(key=lambda x: (x.published is not None, x.published or datetime.fromtimestamp(0, tz=timezone.utc)), reverse=True)

    counts_by_source: dict[str, int] = {}
    counts_by_tag: dict[str, int] = {}
    for it in filtered:
        counts_by_source[it.source] = counts_by_source.get(it.source, 0) + 1
        for t in it.source_tags:
            counts_by_tag[t] = counts_by_tag.get(t, 0) + 1

    payload: Any
    if args.format == "json":
        limit = len(filtered) if args.limit <= 0 else args.limit
        payload = {
            "generated_at": generated_at.isoformat(),
            "window_start": window_start_utc.isoformat(),
            "total_items_raw": len(all_items),
            "total_items": min(len(filtered), limit),
            "counts_by_source": dict(sorted(counts_by_source.items(), key=lambda kv: (-kv[1], kv[0]))),
            "counts_by_tag": dict(sorted(counts_by_tag.items(), key=lambda kv: (-kv[1], kv[0]))),
            "failures": failures,
            "items": _items_to_json(filtered if args.limit <= 0 else filtered[: args.limit]),
        }
        out_text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        out_text = _render_markdown(
            filtered,
            generated_at=generated_at,
            window_start=window_start_utc.astimezone(generated_at.tzinfo or timezone.utc),
            limit=args.limit,
        )
        if failures:
            out_text += "\n## Failures\n"
            for f in failures:
                out_text += f"- {f['source']}: {f['error']} ({f['url']})\n"

    if args.output == "-" or not args.output:
        print(out_text)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_text)
            if not out_text.endswith("\n"):
                f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

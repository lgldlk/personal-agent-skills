#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class TrendingRepo:
    full_name: str
    url: str
    description: str
    language: str
    stars: Optional[int]
    forks: Optional[int]
    stars_delta: Optional[int]


def _read_json(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_int(s: str) -> Optional[int]:
    s = (s or "").strip()
    if not s:
        return None
    s = s.replace(",", "")
    try:
        return int(s)
    except Exception:
        return None


def _strip_html(text: str) -> str:
    text = (text or "")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _http_get(url: str, timeout_s: int, token: Optional[str] = None, accept: str = "application/vnd.github+json") -> tuple[int, dict[str, str], bytes]:
    headers = {
        "User-Agent": "ai-news-digest/0.1",
        "Accept": accept,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read()
        headers_out = {k.lower(): v for k, v in resp.headers.items()}
        return resp.status, headers_out, body


def _http_get_json(url: str, timeout_s: int, token: Optional[str] = None, accept: str = "application/vnd.github+json") -> Any:
    status, headers_out, body = _http_get(url, timeout_s=timeout_s, token=token, accept=accept)
    if status < 200 or status >= 300:
        raise RuntimeError(f"HTTP {status} for {url}")
    try:
        return json.loads(body.decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Invalid JSON from {url}: {e}") from e


def _parse_trending(html_bytes: bytes, since: str, limit: int) -> list[TrendingRepo]:
    html_text = html_bytes.decode("utf-8", errors="replace")
    articles = re.findall(r"(?is)<article\\b.*?</article>", html_text)
    out: list[TrendingRepo] = []

    delta_pattern = r"(?i)([0-9][0-9,]*)\\s+stars\\s+(?:today|this\\s+week|this\\s+month)"
    for art in articles:
        # Repo path is usually in the first <h2> link.
        m_repo = re.search(r'(?is)<h2\\b[^>]*>.*?href=\"(/[^\"/]+/[^\"/]+)\"', art)
        if not m_repo:
            continue
        path = m_repo.group(1).strip()
        full_name = path.strip("/").split("?")[0]
        if full_name.count("/") != 1:
            continue
        url = urllib.parse.urljoin("https://github.com", path.split("?")[0])

        # Description
        desc = ""
        m_desc = re.search(r'(?is)<p\\b[^>]*class=\"[^\"]*col-9[^\"]*\"[^>]*>(.*?)</p>', art)
        if m_desc:
            desc = _strip_html(m_desc.group(1))

        # Language
        lang = ""
        m_lang = re.search(r'(?is)itemprop=\"programmingLanguage\"[^>]*>\\s*([^<]+)\\s*<', art)
        if m_lang:
            lang = _strip_html(m_lang.group(1))

        # Stars and forks (approx from page)
        stars = None
        forks = None
        m_stars = re.search(r'(?is)href=\"' + re.escape(path) + r'/stargazers\"[^>]*>\\s*([^<]+)\\s*<', art)
        if m_stars:
            stars = _to_int(_strip_html(m_stars.group(1)))
        m_forks = re.search(r'(?is)href=\"' + re.escape(path) + r'/forks\"[^>]*>\\s*([^<]+)\\s*<', art)
        if m_forks:
            forks = _to_int(_strip_html(m_forks.group(1)))

        stars_delta = None
        m_delta = re.search(delta_pattern, _strip_html(art))
        if m_delta:
            stars_delta = _to_int(m_delta.group(1))

        out.append(
            TrendingRepo(
                full_name=full_name,
                url=url,
                description=desc,
                language=lang,
                stars=stars,
                forks=forks,
                stars_delta=stars_delta,
            )
        )
        if len(out) >= limit:
            break
    return out


def _get_repo_details(full_name: str, timeout_s: int, token: Optional[str]) -> dict[str, Any]:
    owner, repo = full_name.split("/", 1)
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
    return _http_get_json(url, timeout_s=timeout_s, token=token)

def _get_repo_topics(full_name: str, timeout_s: int, token: Optional[str]) -> list[str]:
    owner, repo = full_name.split("/", 1)
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/topics"
    # Topics historically required a preview accept header; keep it for compatibility.
    data = _http_get_json(
        url,
        timeout_s=timeout_s,
        token=token,
        accept="application/vnd.github+json, application/vnd.github.mercy-preview+json",
    )
    names = data.get("names") or []
    return [n for n in names if isinstance(n, str)]


def _get_community_profile(full_name: str, timeout_s: int, token: Optional[str]) -> Optional[dict[str, Any]]:
    owner, repo = full_name.split("/", 1)
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/community/profile"
    try:
        # Should work with modern accept headers; if not, return None gracefully.
        return _http_get_json(url, timeout_s=timeout_s, token=token)
    except Exception:
        return None


def _search_issues_count(query: str, timeout_s: int, token: Optional[str]) -> Optional[int]:
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": query, "per_page": 1})
    try:
        data = _http_get_json(url, timeout_s=timeout_s, token=token)
        return int(data.get("total_count", 0))
    except Exception:
        return None


def _search_top_issues(full_name: str, since_date: str, timeout_s: int, token: Optional[str], limit: int = 3) -> list[dict[str, Any]]:
    query = f"repo:{full_name} is:issue created:>={since_date}"
    params = {"q": query, "sort": "comments", "order": "desc", "per_page": limit}
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(params)
    try:
        data = _http_get_json(url, timeout_s=timeout_s, token=token)
        items = data.get("items", []) or []
        out = []
        for it in items[:limit]:
            out.append(
                {
                    "title": it.get("title"),
                    "url": it.get("html_url"),
                    "comments": it.get("comments"),
                    "state": it.get("state"),
                    "created_at": it.get("created_at"),
                }
            )
        return out
    except Exception:
        return []


def _format_repo_md(row: dict[str, Any]) -> str:
    name = row.get("full_name", "")
    html_url = row.get("html_url") or row.get("url") or ""
    stars = row.get("stargazers_count")
    forks = row.get("forks_count")
    pushed_at = row.get("pushed_at")
    lang = row.get("language") or ""
    delta = row.get("trending", {}).get("stars_delta")

    parts = []
    parts.append(f"- [{name}]({html_url})")
    meta = []
    if isinstance(stars, int):
        meta.append(f"⭐ {stars:,}")
    if isinstance(forks, int):
        meta.append(f"🍴 {forks:,}")
    if isinstance(delta, int):
        meta.append(f"Δ⭐ {delta:,}")
    if lang:
        meta.append(lang)
    if pushed_at:
        meta.append(f"pushed {pushed_at[:10]}")
    if meta:
        parts[-1] += " — " + " · ".join(meta)

    desc = (row.get("description") or "").strip()
    if desc:
        parts.append(f"  - {desc}")

    health = row.get("community_profile", {})
    if isinstance(health, dict) and health:
        hp = health.get("health_percentage")
        if isinstance(hp, int):
            parts.append(f"  - Community health: {hp}%")

    fb = row.get("feedback", {})
    if isinstance(fb, dict) and fb:
        s = []
        for key, label in [
            ("open_issues_30d", "open issues (30d)"),
            ("closed_issues_30d", "closed issues (30d)"),
            ("open_prs", "open PRs"),
            ("good_first_issue_open", "good first issues"),
        ]:
            val = fb.get(key)
            if isinstance(val, int):
                s.append(f"{label}: {val}")
        if s:
            parts.append("  - Feedback: " + " · ".join(s))
        top = fb.get("top_issues_30d") or []
        if top:
            parts.append("  - Most discussed (30d):")
            for it in top[:3]:
                t = it.get("title") or ""
                u = it.get("url") or ""
                c = it.get("comments")
                if t and u:
                    parts.append(f"    - [{t}]({u}) ({c} comments)")

    return "\n".join(parts)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fetch GitHub trending repos and enrich with community heat/feedback.")
    parser.add_argument("--since", choices=["daily", "weekly", "monthly"], default="daily", help="Trending window")
    parser.add_argument("--language", default="", help="Trending language filter (e.g. python). Empty means all.")
    parser.add_argument("--trending-scan", type=int, default=50, help="How many repos to scan from Trending before filtering to AI")
    parser.add_argument("--limit", type=int, default=0, help="Max repos to return. 0 means no limit (within trending-scan/search fallback).")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout seconds")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    parser.add_argument("--output", default="-", help="Output file path, or - for stdout")
    parser.add_argument("--window-days", type=int, default=30, help="Feedback lookback window in days")
    parser.add_argument("--keywords-path", default=os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "references", "github_ai_topics.json")))
    parser.add_argument("--keywords", action="append", help="Extra AI keywords (repeatable, comma-separated). If omitted, use keywords from github_ai_topics.json.")
    parser.add_argument("--no-topic-filter", action="store_true", help="Do not use GitHub topics to decide if a repo is AI-related")
    parser.add_argument("--no-search-fallback", action="store_true", help="Do not use Search API fallback if too few AI repos found in Trending")
    parser.add_argument("--no-profile", action="store_true", help="Skip community profile endpoint")
    parser.add_argument("--no-feedback", action="store_true", help="Skip issue/PR feedback endpoints (faster, fewer API calls)")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    now = _now_utc()
    since_date = (now - timedelta(days=max(1, args.window_days))).date().isoformat()

    # Fetch trending HTML (no API key needed)
    lang_path = f"/trending/{urllib.parse.quote(args.language)}" if args.language else "/trending"
    trending_url = f"https://github.com{lang_path}?{urllib.parse.urlencode({'since': args.since})}"
    status, _, html_bytes = _http_get(trending_url, timeout_s=args.timeout, token=None, accept="text/html,application/xhtml+xml")
    if status != 200:
        print(f"error: trending fetch failed HTTP {status}", file=sys.stderr)
        return 2
    trending = _parse_trending(html_bytes, since=args.since, limit=max(args.trending_scan, args.limit, 1))

    # Optional keyword filter (AI-ish)
    keywords_cfg = {}
    try:
        keywords_cfg = _read_json(args.keywords_path)
    except Exception:
        keywords_cfg = {}

    def split_csv(vals: Optional[list[str]]) -> list[str]:
        if not vals:
            return []
        out: list[str] = []
        for v in vals:
            for p in (v or "").split(","):
                p = p.strip()
                if p:
                    out.append(p)
        return out

    kw = split_csv(args.keywords) or [k for k in (keywords_cfg.get("keywords") or []) if isinstance(k, str)]
    topics_allow = [t for t in (keywords_cfg.get("topics") or []) if isinstance(t, str)]

    # Determine which trending repos are AI-related.
    # Start with keyword hits (no API calls), then (optionally) fill via topics until enough.
    ai_candidates: list[TrendingRepo] = []
    remaining: list[TrendingRepo] = []
    for r in trending:
        hay = f"{r.full_name}\n{r.description}".lower()
        kw_hit = any(k.lower() in hay for k in kw) if kw else False
        if kw_hit:
            ai_candidates.append(r)
        else:
            remaining.append(r)

    # If we still need more, try topics for the remaining repos in "most trending" order.
    target = 10_000_000 if args.limit <= 0 else args.limit

    if not args.no_topic_filter and topics_allow and len(ai_candidates) < target:
        remaining.sort(key=lambda r: (r.stars_delta or 0, r.stars or 0), reverse=True)
        for r in remaining:
            try:
                names = _get_repo_topics(r.full_name, timeout_s=args.timeout, token=token)
                if any(n in topics_allow for n in names):
                    ai_candidates.append(r)
            except Exception:
                pass
            if len(ai_candidates) >= target:
                break

    # Rank by trending delta (if present) else stars (page) else keep order.
    def rank_key(r: TrendingRepo) -> tuple[int, int]:
        return (r.stars_delta or 0, r.stars or 0)

    ai_candidates.sort(key=rank_key, reverse=True)
    selected: list[TrendingRepo] = ai_candidates if args.limit <= 0 else ai_candidates[: args.limit]

    # If too few, optionally fallback to Search API using topics (approx "hot", recently pushed).
    if len(selected) < target and not args.no_search_fallback and topics_allow:
        need = target - len(selected)
        pushed_since = (now - timedelta(days=14)).date().isoformat()
        seen = {r.full_name for r in selected}
        for topic in topics_allow[:5]:
            q = f"topic:{topic} pushed:>={pushed_since}"
            params = {"q": q, "sort": "stars", "order": "desc", "per_page": min(need, 10)}
            url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(params)
            try:
                data = _http_get_json(url, timeout_s=args.timeout, token=token)
                items = data.get("items") or []
                for it in items:
                    full = it.get("full_name")
                    html_url = it.get("html_url")
                    if not isinstance(full, str) or not full or full in seen:
                        continue
                    seen.add(full)
                    selected.append(
                        TrendingRepo(
                            full_name=full,
                            url=html_url if isinstance(html_url, str) else f"https://github.com/{full}",
                            description=(it.get("description") or "") if isinstance(it.get("description"), str) else "",
                            language=(it.get("language") or "") if isinstance(it.get("language"), str) else "",
                            stars=int(it.get("stargazers_count", 0)) if isinstance(it.get("stargazers_count"), int) else None,
                            forks=int(it.get("forks_count", 0)) if isinstance(it.get("forks_count"), int) else None,
                            stars_delta=None,
                        )
                    )
                    if len(selected) >= target:
                        break
            except Exception:
                pass
            if len(selected) >= target:
                break

    trending = selected if args.limit <= 0 else selected[: args.limit]

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for r in trending:
        row: dict[str, Any] = {
            "full_name": r.full_name,
            "url": r.url,
            "description": r.description,
            "language": r.language,
            "trending": dataclasses.asdict(r),
        }
        try:
            details = _get_repo_details(r.full_name, timeout_s=args.timeout, token=token)
            for k in [
                "html_url",
                "stargazers_count",
                "forks_count",
                "watchers_count",
                "open_issues_count",
                "created_at",
                "updated_at",
                "pushed_at",
                "license",
                "archived",
                "disabled",
                "has_discussions",
            ]:
                if k in details:
                    row[k] = details[k]
        except Exception as e:
            failures.append({"repo": r.full_name, "error": f"{type(e).__name__}: {e}"})

        if not args.no_profile:
            prof = _get_community_profile(r.full_name, timeout_s=args.timeout, token=token)
            if prof is not None:
                row["community_profile"] = {
                    "health_percentage": prof.get("health_percentage"),
                    "description": prof.get("description"),
                    "documentation": prof.get("documentation"),
                    "files": prof.get("files"),
                    "updated_at": prof.get("updated_at"),
                }

        if not args.no_feedback:
            fb: dict[str, Any] = {}
            fb["open_prs"] = _search_issues_count(f"repo:{r.full_name} is:pr is:open", timeout_s=args.timeout, token=token)
            fb["open_issues_30d"] = _search_issues_count(f"repo:{r.full_name} is:issue is:open created:>={since_date}", timeout_s=args.timeout, token=token)
            fb["closed_issues_30d"] = _search_issues_count(f"repo:{r.full_name} is:issue closed:>={since_date}", timeout_s=args.timeout, token=token)
            fb["good_first_issue_open"] = _search_issues_count(f"repo:{r.full_name} is:issue is:open label:\"good first issue\"", timeout_s=args.timeout, token=token)
            fb["help_wanted_open"] = _search_issues_count(f"repo:{r.full_name} is:issue is:open label:\"help wanted\"", timeout_s=args.timeout, token=token)
            fb["top_issues_30d"] = _search_top_issues(r.full_name, since_date=since_date, timeout_s=args.timeout, token=token, limit=3)
            row["feedback"] = fb

        results.append(row)
        time.sleep(0.2)

    payload: Any
    if args.format == "json":
        payload = {
            "generated_at": now.isoformat(),
            "trending_url": trending_url,
            "since": args.since,
            "language": args.language,
            "window_days": args.window_days,
            "repos": results,
            "failures": failures,
            "note": "Set GITHUB_TOKEN (or GH_TOKEN) to increase API rate limits.",
        }
        out_text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        lines = []
        lines.append(f"# GitHub AI Trending ({args.since})")
        lines.append("")
        lines.append(f"- Generated (UTC): {now.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"- Trending page: {trending_url}")
        lines.append(f"- Feedback window: past {args.window_days} days (since {since_date})")
        lines.append("")
        for row in results:
            lines.append(_format_repo_md(row))
        if failures:
            lines.append("")
            lines.append("## Failures")
            for f in failures:
                lines.append(f"- {f.get('repo')}: {f.get('error')}")
        out_text = "\n".join(lines).rstrip() + "\n"

    if args.output == "-" or not args.output:
        sys.stdout.write(out_text)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

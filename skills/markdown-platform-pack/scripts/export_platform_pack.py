#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Songti.ttc",
]

MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
]


@dataclass
class Block:
    kind: str
    start: int
    end: int
    text: str
    fence_lang: str = ""


def load_font(size: int, mono: bool = False):
    candidates = MONO_CANDIDATES if mono else FONT_CANDIDATES
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_text(text: str, width: int) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        if not raw.strip():
            out.append("")
            continue
        buf = ""
        for ch in raw:
            cand = buf + ch
            if len(cand) <= width:
                buf = cand
            else:
                if buf:
                    out.append(buf)
                buf = ch
        if buf:
            out.append(buf)
    return out


def parse_table_rows(table_md: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in table_md.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    return rows


def render_text_block(text: str, out: Path, title: str = "伪代码") -> None:
    font = load_font(28)
    title_font = load_font(34)
    lines = wrap_text(text, 74)
    width = 1600
    margin = 44
    title_h = 58
    line_h = 44
    height = margin * 2 + title_h + line_h * max(1, len(lines))
    img = Image.new("RGB", (width, height), "#f7f8fb")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((22, 22, width - 22, height - 22), radius=22, fill="#ffffff", outline="#d8dde6", width=3)
    draw.text((margin, margin), title, fill="#17233a", font=title_font)
    y = margin + title_h
    for line in lines:
        draw.text((margin, y), line, fill="#1f2937", font=font)
        y += line_h
    img.save(out)


def render_table_block(table_md: str, out: Path) -> None:
    rows = parse_table_rows(table_md)
    if not rows:
        raise SystemExit("no table rows found")

    title_font = load_font(34)
    sub_font = load_font(18)
    body_font = load_font(22)
    header_font = load_font(24)

    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]
    widths = [180, 430, 994] if col_count == 3 else [160] + [440] * max(0, col_count - 2) + [500]
    widths = widths[:col_count]

    def fit(text: str, max_chars: int) -> list[str]:
        if not text:
            return [""]
        lines: list[str] = []
        cur = ""
        for ch in text:
            cand = cur + ch
            if len(cand) <= max_chars:
                cur = cand
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
        return lines

    wrapped: list[list[list[str]]] = []
    heights: list[int] = []
    for row in rows:
        row_lines: list[list[str]] = []
        max_lines = 1
        for c, txt in enumerate(row):
            lines = fit(txt, 18 if c == 0 else (28 if c == 1 else 58))
            row_lines.append(lines)
            max_lines = max(max_lines, len(lines))
        row_h = max(76, max_lines * 34 + 28)
        wrapped.append(row_lines)
        heights.append(row_h)

    width = sum(widths) + 72
    height = 36 + 52 + 28 + sum(heights) + 36
    img = Image.new("RGB", (width, height), "#f7f8fb")
    draw = ImageDraw.Draw(img)
    x0 = 36
    y = 36
    draw.text((x0, y), "普通 Agent 调用记录 vs 高并发治理", fill="#17233a", font=title_font)
    draw.text((x0, y + 44), "把“有没有记录”和“能不能稳定执行”分开", fill="#5b6777", font=sub_font)
    y += 80

    header_bg = "#17263f"
    header_fg = "#ffffff"
    grid = "#d7dde8"
    alt = "#eef3f8"
    body = "#1f2937"

    x = x0
    for c, w in enumerate(widths):
        draw.rectangle((x, y, x + w, y + 110), fill=header_bg, outline=grid, width=1)
        draw.text((x + 16, y + 32), rows[0][c], fill=header_fg, font=header_font)
        x += w
    y += 110

    for r_idx, row in enumerate(wrapped[1:], start=1):
        row_h = heights[r_idx]
        bg = "#ffffff" if r_idx % 2 else alt
        x = x0
        for c, lines in enumerate(row):
            w = widths[c]
            draw.rectangle((x, y, x + w, y + row_h), fill=bg, outline=grid, width=1)
            ty = y + 24
            for line in lines:
                draw.text((x + 16, ty), line, fill=body, font=body_font)
                ty += 32
            x += w
        y += row_h

    draw.rectangle((x0, 116, x0 + sum(widths), y), outline="#b9c4d2", width=2)
    draw.text((x0, height - 26), "来源：文章中的对比表，已转成图片以适配小红书导入", fill="#6a7482", font=load_font(14))
    img.save(out)


def parse_blocks(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        fence_match = re.match(r"^(```|~~~)\s*(.*)$", line)
        if fence_match:
            fence_marker = fence_match.group(1)
            fence = fence_match.group(2).strip()
            start = i
            i += 1
            body: list[str] = []
            while i < len(lines) and not lines[i].startswith(fence_marker):
                body.append(lines[i])
                i += 1
            end = i if i < len(lines) else len(lines) - 1
            blocks.append(Block(kind="code", start=start, end=end, text="\n".join(body), fence_lang=fence))
            i += 1
            continue

        if line.lstrip().startswith("|"):
            start = i
            body = [line]
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                body.append(lines[i])
                i += 1
            end = i - 1
            blocks.append(Block(kind="table", start=start, end=end, text="\n".join(body)))
            continue

        i += 1

    return blocks


def looks_like_table(block: Block) -> bool:
    rows = parse_table_rows(block.text)
    return len(rows) >= 2 and any(len(row) >= 2 for row in rows)


def build_replacement_map(source: Path, out_md_dir: Path, blocks: list[Block], assets_dir: Path) -> dict[int, list[str]]:
    replacements: dict[int, list[str]] = {}
    table_index = 0
    code_index = 0
    rel_assets_dir = Path(os.path.relpath(assets_dir, out_md_dir)).as_posix()

    for block in blocks:
        if block.kind == "table" and looks_like_table(block):
            table_index += 1
            asset = assets_dir / f"{source.stem}-table-{table_index}.png"
            render_table_block(block.text, asset)
            replacements[block.start] = [f"![table-{table_index}]({rel_assets_dir}/{asset.name})"]
            for line_no in range(block.start + 1, block.end + 1):
                replacements[line_no] = []
            continue

        if block.kind == "code":
            code_index += 1
            asset = assets_dir / f"{source.stem}-code-{code_index}.png"
            title = "伪代码" if not block.fence_lang else f"伪代码 · {block.fence_lang}"
            render_text_block(block.text, asset, title=title)
            replacements[block.start] = [f"![code-{code_index}]({rel_assets_dir}/{asset.name})"]
            for line_no in range(block.start + 1, block.end + 1):
                replacements[line_no] = []

    return replacements


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown special blocks to image-backed import Markdown")
    parser.add_argument("markdown", help="Source Markdown file")
    parser.add_argument("--output-md", help="Temporary Markdown output path")
    parser.add_argument("--output-dir", help="Output directory for generated PNGs", default=None)
    args = parser.parse_args()

    source = Path(args.markdown).resolve()
    md_text = source.read_text(encoding="utf-8")
    out_md = Path(args.output_md).resolve() if args.output_md else source.with_suffix(".xiaohongshu.tmp.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.output_dir).resolve() if args.output_dir else source.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    lines = md_text.splitlines()
    blocks = parse_blocks(lines)
    replacements = build_replacement_map(source, out_md.parent, blocks, assets_dir)

    out_lines: list[str] = []
    skip_until = -1
    for idx, line in enumerate(lines):
        if idx < skip_until:
            continue
        if idx in replacements:
            out_lines.extend(replacements[idx])
            block = next((b for b in blocks if b.start == idx), None)
            if block:
                skip_until = block.end + 1
            continue
        out_lines.append(line)

    out_md.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

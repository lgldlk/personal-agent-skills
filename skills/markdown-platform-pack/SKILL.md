---
name: markdown-platform-pack
description: Convert Markdown into platform-ready Word output for Xiaohongshu or WeChat by rasterizing tables and fenced code blocks into images, rewriting a temporary Markdown file, and exporting a Word document.
---

# Markdown Platform Pack

Use this skill when a Markdown article must be imported into a platform that does not handle Markdown tables or code blocks well, especially Xiaohongshu or WeChat Word import flows.

## Workflow

1. Find unsupported Markdown blocks by block range, not by global string replace.
   - Tables
   - Fenced code blocks
   - Any block that must survive as an image

2. Render each unsupported block to a PNG.
   - Keep Chinese text readable.
   - Use platform-safe fonts.
   - Prefer a single block per image.

3. Create a temporary Markdown file.
   - Replace each original block with the PNG reference.
   - Keep normal paragraphs unchanged.
   - Preserve the original article order.

4. Export the temporary Markdown to Word.
   - Keep headings, lists, quotes, links, and images.
   - Use a local temporary environment if the default toolchain drops images or mangles Chinese glyphs.
   - Keep the environment beside the article or task folder, not in a global location.
   - Prefer `python-docx` when the normal export path strips images or breaks Chinese text.

5. Deliver the Word file plus the generated images.

## Export Notes

- Use Chinese-capable fonts for both image rendering and Word export.
- Keep image paths relative to the temporary Markdown file.
- Preserve the original article order and section structure.
- Leave inline Markdown, headings, quotes, and lists intact unless the platform breaks them.
- Do not convert inline code spans unless the platform specifically requires it.
- Do not leave raw table syntax or fenced code blocks in the import-ready Markdown.

## Validation

Before handing off, check:

1. The temporary Markdown has no raw tables or fenced code blocks.
2. The generated images open correctly and Chinese text renders cleanly.
3. The Word file contains the images, not just image links.
4. The Word file preserves headings, lists, quotes, and links in readable form.

## Local Script

Use `scripts/export_platform_pack.py` for the repeatable path.

Typical flow:

```bash
python3 scripts/export_platform_pack.py input.md --output-md input.xiaohongshu.tmp.md
```

Then export the temporary Markdown to Word with the project's local docx pipeline.

If the user needs a Xiaohongshu-specific file, replace every table and code fence first.

## Rules

- Do not leave raw tables or fenced code blocks in the import version.
- Do not use fonts that cannot render Chinese.
- Keep the temporary Markdown beside the source article.
- Write image paths relative to the temporary Markdown file.
- Keep the Word export pipeline local to the task folder when a temporary venv is needed.
- If a block is too wide, shorten the picture-only version before rendering.
- If the Word export path drops images, switch to a local Python `python-docx` pipeline.

## Outputs

Preferred outputs, in order:

- `*.tmp.md` for the import-ready intermediate file
- PNGs for tables and code blocks
- `*.docx` for the platform import file

## When to use

- User asks to convert Markdown into a Word document for Xiaohongshu or WeChat
- User asks to preserve Markdown structure while removing unsupported blocks
- User asks to make a document import-safe for a platform with limited formatting

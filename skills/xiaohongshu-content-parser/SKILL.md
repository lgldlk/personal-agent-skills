---
name: xiaohongshu-content-parser
description: Parse public Xiaohongshu share URLs through the BugPk xhsjx API, download post media locally, and generate a markdown report with title,正文, author, images, video links, and response metadata. Use when a user wants to extract Xiaohongshu public post content into files, and prefer a Node script entrypoint with a shell fallback if Node is unavailable.
---

# Xiaohongshu Content Parser

## Use the real input shape

- Call `https://api.bugpk.com/api/xhsjx` with a `url` query parameter.
- The `url` value must be the full Xiaohongshu share URL, including its query string when present.
- Treat the official `key=value` examples as templates only.

## Output contract

Produce, in one output directory:

- `xiaohongshu-notes/`: default root folder under the current working directory
- `report.md`: human-readable summary
- `normalized.json`: normalized fields used by the report
- `raw.json`: exact API response
- `media/`: downloaded avatar, cover, images, and optional video files

Include in the report:

- title
- author
- 正文 / desc
- image count
- video URL or backup URL when present
- download location
- response metadata such as `cache_status` and `bktip`

## Preferred workflow

1. Use the Node script entrypoint.
2. If Node is not available, use the shell wrapper, which should only print a clear failure or invoke Node when present.
3. Accept either a live URL or a saved raw JSON file for offline validation.
4. Preserve missing or unsupported fields as absent; do not invent engagement metrics.

## Notes

- `desc` is the正文.
- `images` may contain one or many image URLs.
- `video_backup` may be a string or a list depending on the response.
- If the API returns `520`, treat it as a transport failure and retry once with browser-like headers in the script.
- Default the root download folder to `./xiaohongshu-notes/`, then create one subfolder per note using `标题-日期-链接ID`.

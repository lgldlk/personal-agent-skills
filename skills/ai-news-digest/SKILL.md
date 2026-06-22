---
name: ai-news-digest
description: Fetch and summarize the latest AI news from reputable sources (via RSS/Atom feeds) and produce a dated digest with links. Use when the user asks for “latest AI news”, “AI 新闻汇总/简报”, “本周/今日 AI 动态”, or when you need to gather up-to-date AI announcements, research highlights, and industry coverage from known sites.
---

# AI News Digest

## Workflow (required)

**强制要求**：在生成 AI 新闻汇总/简报前，必须先运行脚本获取最新数据。不要凭记忆或直接编写新闻摘要。若脚本失败，先重试一次；仍失败再使用 `web.run` 作为兜底，并在结果中标注“数据来源与时间窗口”。

1) 必须抓取最新新闻

默认抓取过去 24 小时；如果用户指定“本周”“过去 72 小时”“今天”等范围，调整 `--since`。Use a task-local output path such as `./ai-news.json`, `./ai-news.md`, or a file under a temporary working directory. From the skill directory, run:

```bash
python3 scripts/fetch_ai_news.py --since 24h --limit 0 --max-per-source 0 --format json --output ./ai-news.json
```

Or generate Markdown directly (mandatory alternative):

```bash
python3 scripts/fetch_ai_news.py --since 24h --limit 0 --max-per-source 0 --format md --output ./ai-news.md
```

1b) 需要时补充 X + 非 RSS 站点

- Use `web.run.search_query` with `references/x_watchlist.json` and `references/non_rss_sources.json`.
- Keep only items within the same time window (e.g. past 72 hours), and prefer links to the canonical announcement/blog/paper.

1c) 需要时补充 GitHub “热门上榜项目” + 社区热度/反馈

Run:

```bash
python3 scripts/fetch_github_ai_trending.py --since daily --limit 0 --format md --output ./github-ai.md
```

Notes:

- This uses GitHub Trending (HTML) for the “up榜热门” list, then enriches repos via GitHub API for heat/feedback signals.
- Set `GITHUB_TOKEN` (or `GH_TOKEN`) to avoid low rate limits.
- Feedback signals include: open PRs, open/closed issues in the past N days, “good first issue/help wanted”, and top discussed issues.
- If you only need “hot list”, run faster with `--no-feedback` (and/or `--no-profile`).

2) 生成中文汇总（必须）

- Output in Chinese unless the user asked for English.
- Always include **specific dates** (e.g. “2026-02-04”) for “today / latest / yesterday”.
- For each item: *发生了什么* + *为什么重要* + link（必要时 2 links）.
- If items conflict across sources, mention uncertainty and cite multiple links.
- End with a **Chinese wrap-up** section: “趋势与建议” (3–7 bullets). For 24h digests, title it “24小时趋势与建议”.

3) If the user wants only certain outlets/topics

- Edit `references/sources.json` (add/remove feeds, or toggle `"enabled": true/false`), then re-run the script.
- Use filters when you only need a subset:
  - Keywords: `--keywords agent,benchmark,open-source`
  - Source tags: `--include-tags vendor,research` / `--exclude-tags community`

## Output templates

### Short digest (default)

- Title: `AI News Digest — <DATE RANGE>`
- Sections (optional): Product/Company, Research, Policy/Safety, Market/Business
- 8–15 bullets total, each with 1 link (2 links if needed)
  - If there are many items within 24h, cluster by theme and summarize each cluster; do not drop items silently.

### Long digest

- Add 1–2 sentence summaries per item, grouped by section
- Include a “Notable trends” section at the end (3–5 bullets)

## Notes

- Prefer RSS/Atom feeds over scraping HTML for reliability.
- If a target site has no public feed, use `web.run` (search + open) as a fallback and still include dated links.
- For non-RSS “known sites”, use `references/non_rss_sources.json` query templates with `web.run.search_query`.
- For X (Twitter) news, prefer `web.run` search (no scraping): use `references/x_watchlist.json` handles + templates, and set a clear time window (e.g. past 72 hours).
- For GitHub trending, prefer `scripts/fetch_github_ai_trending.py` (no scraping beyond the Trending listing page).
- If a feed is down, retry once, then skip and report which sources failed.
- Do not claim anything is “latest” without a date/time window (e.g. “past 72 hours”).

## X (Twitter) quick recipe (web.run)

Use `web.run.search_query` with `recency` (days) and queries like:

- `site:x.com/OpenAI (announce OR released OR launch OR model OR paper)`
- `site:x.com (OpenAI OR AnthropicAI OR GoogleDeepMind OR MistralAI OR xai) (released OR launch OR model)`

Then: extract only posts that link to an official announcement/blog/paper, and include both the X link and the canonical source link when possible.

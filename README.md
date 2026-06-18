# Personal Agent Skills

Public agent skills maintained by `lgldlk`.

This repository contains self-owned skills for research and implementation workflows. Each skill is designed to be installable, inspectable, and useful on its own.

![API Data Research capability matrix](assets/screenshots/api-data-research-matrix.png)

## What's Inside

| Skill | What it does | Best for | Included resources |
|---|---|---|---|
| [`api-data-research`](skills/api-data-research/SKILL.md) | Verifies official and third-party API capabilities from docs, schemas, examples, pricing pages, and stability/community signals. | API vendor comparison, social/content data access research, field-level capability matrices, cited Markdown reports, table-to-image exports. | `SKILL.md`, OpenAI UI metadata, and a PNG renderer for Markdown capability tables. |
| [`miniapp-figma-alignment`](skills/miniapp-figma-alignment/SKILL.md) | Aligns mini-program, uni-app, Taro, and other mini-app pages to Figma with correct frame-width scaling, rpx conversion, platform chrome handling, and visual QA. | Fixing mini-program screens that look too small, too large, or misaligned after translating Figma designs into code. | `SKILL.md` and OpenAI UI metadata. |

## API Data Research

Use this skill when you need to answer questions like:

- Which API can retrieve full article text, images, links, likes, views, comments, shares, or bookmarks?
- Is the data available through an official API, a third-party API, a scraping workflow, or only an authorized-account analytics endpoint?
- What are the exact documented response fields?
- What is the pricing model: subscription, per request, per credit, custom quote, or app-review based?
- How stable and credible is a vendor based on docs, examples, status pages, GitHub/community signals, and operating-year basis?
- Can the comparison matrix be exported as a PNG for sharing?

The skill is intentionally evidence-first. It avoids vague labels like "social listening API" unless the source docs expose concrete search, monitoring, or alerting functions. It also separates `docs confirmed`, `sample confirmed`, and `live tested` capability levels.

## Example Output

The screenshot above was generated from [`examples/api-data-research-example.md`](examples/api-data-research-example.md) with the bundled renderer:

```bash
python3 skills/api-data-research/scripts/render_markdown_table_png.py \
  --input examples/api-data-research-example.md \
  --heading "数据维度能力矩阵" \
  --output assets/screenshots/api-data-research-matrix.png \
  --title "API Data Research Example" \
  --subtitle "Capability Matrix"
```

Typical Markdown output includes:

- 3-6 concise conclusions
- a capability matrix
- field-level alignment tables
- vendor detail sections
- source links and evidence levels
- pricing, access scope, stability, and operating-year basis

## Miniapp Figma Alignment

Use this skill when a mini-program UI needs to match Figma precisely. It helps the agent avoid common mobile mini-app mistakes:

- treating Figma pixels as CSS pixels
- assuming every Figma frame is `750` wide
- mixing final `rpx` values with Taro `pxtransform`
- forgetting that JS inline styles are not transformed by compile-time plugins
- redrawing native status bars, menu capsules, or platform chrome
- ignoring safe-area and fixed-bottom layout behavior

It starts by detecting the framework and unit pipeline, then computes the correct scale:

```text
scale = targetDesignWidth / figmaFrameWidth
targetValue = figmaPx * scale
```

For example, if the Figma frame is `390px` wide and the target mini-program design width is `750rpx`, the scale is:

```text
750 / 390 = 1.9231
```

See [`examples/miniapp-figma-alignment-example.md`](examples/miniapp-figma-alignment-example.md) for the expected reasoning and report shape.

## Install

List available skills:

```bash
npx skills add lgldlk/personal-agent-skills --list
```

Install with an Agent Skills compatible installer:

```bash
npx skills add lgldlk/personal-agent-skills --skill api-data-research -g -a codex -y
npx skills add lgldlk/personal-agent-skills --skill miniapp-figma-alignment -g -a codex -y
```

Or copy skill folders manually:

```bash
cp -R skills/api-data-research ~/.codex/skills/
cp -R skills/miniapp-figma-alignment ~/.codex/skills/
```

Then start a new Codex session so the skill metadata is loaded.

## Repository Layout

```text
personal-agent-skills/
├── assets/
│   └── screenshots/
│       └── api-data-research-matrix.png
├── examples/
│   ├── api-data-research-example.md
│   └── miniapp-figma-alignment-example.md
├── skills/
│   ├── index.json
│   ├── api-data-research/
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   └── scripts/
│   │       └── render_markdown_table_png.py
│   └── miniapp-figma-alignment/
│       ├── SKILL.md
│       └── agents/
│           └── openai.yaml
├── scripts/
│   └── validate-skills.sh
├── docs/
│   ├── authoring.md
│   ├── install.md
│   └── release-checklist.md
└── templates/
    └── SKILL.template.md
```

## Quality Standard

- Every skill lives at `skills/<skill-name>/SKILL.md`.
- `SKILL.md` frontmatter contains only `name` and `description`.
- `name` must match the skill directory.
- Long references belong in `references/`.
- Repeatable deterministic logic belongs in `scripts/`.
- Public skills must not contain API keys, tokens, cookies, private URLs, or local-only absolute paths.

Run:

```bash
scripts/validate-skills.sh
```

Current validation result:

```text
OK: validated 2 skill(s)
```

## License

MIT

# Personal Agent Skills

Public agent skills maintained by `lgldlk`.

This repository currently contains one self-owned skill: **API Data Research**. It helps an agent compare official and third-party data APIs by reading documentation, extracting exact fields, checking access limits, and producing decision-ready capability matrices.

![API Data Research capability matrix](assets/screenshots/api-data-research-matrix.png)

## What's Inside

| Skill | What it does | Best for | Included resources |
|---|---|---|---|
| [`api-data-research`](skills/api-data-research/SKILL.md) | Verifies official and third-party API capabilities from docs, schemas, examples, pricing pages, and stability/community signals. | API vendor comparison, social/content data access research, field-level capability matrices, cited Markdown reports, table-to-image exports. | `SKILL.md`, OpenAI UI metadata, and a PNG renderer for Markdown capability tables. |

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

## Install

Install with an Agent Skills compatible installer:

```bash
npx skills add lgldlk/personal-agent-skills --skill api-data-research -g -a codex -y
```

Or copy the skill folder manually:

```bash
cp -R skills/api-data-research ~/.codex/skills/
```

Then start a new Codex session so the skill metadata is loaded.

## Repository Layout

```text
personal-agent-skills/
├── assets/
│   └── screenshots/
│       └── api-data-research-matrix.png
├── examples/
│   └── api-data-research-example.md
├── skills/
│   ├── index.json
│   └── api-data-research/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       └── scripts/
│           └── render_markdown_table_png.py
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
OK: validated 1 skill(s)
```

## License

MIT

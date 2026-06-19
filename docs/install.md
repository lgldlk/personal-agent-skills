# Install

List available skills:

```bash
npx skills add lgldlk/lgldlk-agent-skills --list
```

Install one skill:

```bash
npx skills add lgldlk/lgldlk-agent-skills --skill api-data-research -g -a codex -y
npx skills add lgldlk/lgldlk-agent-skills --skill miniapp-figma-alignment -g -a codex -y
npx skills add lgldlk/lgldlk-agent-skills --skill xiaohongshu-content-parser -g -a codex -y
```

Manual install:

```bash
mkdir -p ~/.codex/skills
cp -R skills/api-data-research ~/.codex/skills/
cp -R skills/miniapp-figma-alignment ~/.codex/skills/
cp -R skills/xiaohongshu-content-parser ~/.codex/skills/
```

Then start a new Codex session so the skill metadata is reloaded.

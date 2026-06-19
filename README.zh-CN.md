# lgldlk Agent Skills

[English](README.md)

这是 `lgldlk` 维护的公开个人 Agent Skills 仓库。

这些技能来自真实、反复出现的工作流：API 数据能力调研、小程序 UI 对齐 Figma，以及把公开小红书笔记解析成本地文档。这个仓库可以作为个人技能库安装，也可以单独查看和复制某一个技能。

## 技能列表

| 技能 | 用途 | 主要产物 |
|---|---|---|
| [`api-data-research`](skills/api-data-research/SKILL.md) | 从文档、响应样例、价格页、稳定性和社区信号中对比官方及第三方 API 数据能力。 | 带引用的调研笔记、字段级能力矩阵、PNG 表格导出。 |
| [`miniapp-figma-alignment`](skills/miniapp-figma-alignment/SKILL.md) | 修正或实现小程序、uni-app、Taro 页面，让它们和 Figma 尺寸及平台行为对齐。 | 单位换算判断、实现建议、视觉 QA 清单。 |
| [`xiaohongshu-content-parser`](skills/xiaohongshu-content-parser/SKILL.md) | 解析公开小红书分享链接，保存正文和元数据，并下载图文媒体。 | `report.md`、`normalized.json`、`raw.json` 和本地媒体文件。 |

## 快速安装

查看可安装技能：

```bash
npx skills add lgldlk/lgldlk-agent-skills --list
```

安装单个技能：

```bash
npx skills add lgldlk/lgldlk-agent-skills --skill api-data-research -g -a codex -y
npx skills add lgldlk/lgldlk-agent-skills --skill miniapp-figma-alignment -g -a codex -y
npx skills add lgldlk/lgldlk-agent-skills --skill xiaohongshu-content-parser -g -a codex -y
```

手动安装：

```bash
mkdir -p ~/.codex/skills
cp -R skills/api-data-research ~/.codex/skills/
cp -R skills/miniapp-figma-alignment ~/.codex/skills/
cp -R skills/xiaohongshu-content-parser ~/.codex/skills/
```

安装后重启 Codex，让技能元数据重新加载。

## 结果示例

### API Data Research

这个技能用于做有证据链的 API 横向对比，而不是只看厂商宣传或 SEO 排名。典型结果包括简短结论、能力矩阵、字段对齐、价格/访问范围和信度标注。

![API Data Research 能力矩阵](assets/screenshots/api-data-research-matrix.png)

源示例：[`examples/api-data-research-example.md`](examples/api-data-research-example.md)

### Miniapp Figma Alignment

这个技能会从真实 Figma 画布宽度和目标小程序单位体系出发，给出可落地的换算和检查项。

最小结果形态：

```text
Figma frame width: 390px
Target design width: 750rpx
Scale: 750 / 390 = 1.9231

Example conversion:
- 16px padding -> 30.77rpx
- 338px card width -> 650.00rpx
- 14px font size -> 26.92rpx

Checks:
- 不要重画原生状态栏或胶囊。
- 固定底部按钮要保留 safe-area padding。
- 同一布局区域不要混用最终 rpx 和 Taro pxtransform。
```

源示例：[`examples/miniapp-figma-alignment-example.md`](examples/miniapp-figma-alignment-example.md)

### Xiaohongshu Content Parser

这个技能把公开小红书分享链接转成本地笔记包。

命令：

```bash
node skills/xiaohongshu-content-parser/scripts/parse_xhs.mjs \
  --url "https://www.xiaohongshu.com/explore/..."
```

结果结构：

```text
xiaohongshu-notes/
└── <标题>-<YYYY-MM-DD>-<笔记ID>/
    ├── report.md
    ├── normalized.json
    ├── raw.json
    └── media/
        ├── author-avatar.jpg
        ├── cover.jpg
        └── image-01.jpg
```

示例摘要：

```text
Title: Demo note title
Author: Demo Author
Images: 1
Downloads: 3
Report: xiaohongshu-notes/demo-note-2026-06-19-demoid/report.md
```

接口样例：[`examples/xiaohongshu-content-parser-sample.json`](examples/xiaohongshu-content-parser-sample.json)

## 仓库结构

```text
lgldlk-agent-skills/
├── assets/
│   └── screenshots/
├── docs/
├── examples/
├── scripts/
│   └── validate-skills.sh
├── skills/
│   ├── index.json
│   ├── api-data-research/
│   ├── miniapp-figma-alignment/
│   └── xiaohongshu-content-parser/
└── templates/
```

## 质量规则

- 每个技能放在 `skills/<skill-name>/SKILL.md`。
- `SKILL.md` frontmatter 只保留 `name` 和 `description`。
- `name` 必须和技能目录名一致。
- 长参考资料放到 `references/`。
- 可重复执行的确定性逻辑放到 `scripts/`。
- 公开技能不能包含 API key、token、cookie、私有 URL 或本地专属绝对路径。

校验仓库：

```bash
scripts/validate-skills.sh
```

## License

MIT

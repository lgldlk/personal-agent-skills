# lgldlk Agent Skills

[English](README.md)

这是 `lgldlk` 维护的公开个人 Agent Skills 仓库。

这些技能来自真实、反复出现的工作流：API 数据能力调研、小程序 UI 对齐 Figma、Markdown 打包导出，以及多 agent 流水线协作。这个仓库可以作为个人技能库安装，也可以单独查看和复制某一个技能。

## 技能列表

| 技能 | 用途 | 主要产物 |
|---|---|---|
| [`api-data-research`](skills/api-data-research/SKILL.md) | 从文档、响应样例、价格页、稳定性和社区信号中对比官方及第三方 API 数据能力。 | 带引用的调研笔记、字段级能力矩阵、PNG 表格导出。 |
| [`agent-pipeline-orchestration`](skills/agent-pipeline-orchestration/SKILL.md) | 把工作拆成非阻塞的多 agent 流水线，包含实现、评审、QA 和下一阶段映射。 | 流水线分工、worker 提示词和集成说明。 |
| [`miniapp-figma-alignment`](skills/miniapp-figma-alignment/SKILL.md) | 修正或实现小程序、uni-app、Taro 页面，让它们和 Figma 尺寸及平台行为对齐。 | 单位换算判断、实现建议、视觉 QA 清单。 |
| [`markdown-platform-pack`](skills/markdown-platform-pack/SKILL.md) | 把 Markdown 转成适合导入的 Word 包，先把表格和代码块转成图片。 | `*.tmp.md`、PNG 块图片、`*.docx` 导入文件。 |
| [`social-content-parser`](skills/social-content-parser/SKILL.md) | 解析公开短视频和社交分享链接，提供 20+ 平台兜底层，包括小红书、抖音、哔哩哔哩，生成本地报告和媒体包。 | `report.md`、`normalized.json`、`raw.json` 和本地媒体文件。 |

## 快速安装

查看可安装技能：

```bash
npx skills add lgldlk/lgldlk-agent-skills --list
```

安装单个技能：

```bash
npx skills add lgldlk/lgldlk-agent-skills --skill api-data-research -g -y
npx skills add lgldlk/lgldlk-agent-skills --skill agent-pipeline-orchestration -g -y
npx skills add lgldlk/lgldlk-agent-skills --skill miniapp-figma-alignment -g -y
npx skills add lgldlk/lgldlk-agent-skills --skill markdown-platform-pack -g -y
npx skills add lgldlk/lgldlk-agent-skills --skill social-content-parser -g -y
```

手动安装：

```bash
mkdir -p ~/.skills
cp -R skills/api-data-research ~/.skills/
cp -R skills/agent-pipeline-orchestration ~/.skills/
cp -R skills/miniapp-figma-alignment ~/.skills/
cp -R skills/markdown-platform-pack ~/.skills/
cp -R skills/social-content-parser ~/.skills/
```

安装后重启你的 agent，让技能元数据重新加载。

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

### Social Content Parser

这个技能把公开短视频和社交分享链接转成本地笔记包。它的兜底层覆盖 20+ 平台，包括抖音、快手、小红书、bilibili、油管、TikTok、西瓜视频、好看视频、微视、梨视频、a站（acfun）、知乎、绿洲、美拍、全民、虎牙、推特、ins、豆包、即梦ai、视频号等。它会先清理分享链接里的跟踪参数，抖音主页和作品会分开处理；当平台专用解析器漏掉内容时，还会用聚合解析做兜底。

命令：

```bash
node skills/social-content-parser/scripts/parse_social.mjs \
  --url "https://www.xiaohongshu.com/explore/..."
node skills/social-content-parser/scripts/parse_social.mjs \
  --url "https://v.douyin.com/..."
node skills/social-content-parser/scripts/parse_social.mjs \
  --url "https://www.douyin.com/user/..." --kind profile --count 10
node skills/social-content-parser/scripts/parse_social.mjs \
  --url "https://b23.tv/..."
```

结果结构：

```text
social-notes/
└── <平台>-<标题>-<YYYY-MM-DD>-<ID>/
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
Platform: xiaohongshu
Title: Demo note title
Author: Demo Author
Images: 1
Downloads: 3
Report: social-notes/xiaohongshu-demo-note-2026-06-19-demoid/report.md
```

接口样例：

- [`examples/social-content-parser-xhs-sample.json`](examples/social-content-parser-xhs-sample.json)
- [`examples/social-content-parser-douyin-sample.json`](examples/social-content-parser-douyin-sample.json)
- [`examples/social-content-parser-douyin-profile-sample.json`](examples/social-content-parser-douyin-profile-sample.json)
- [`examples/social-content-parser-bilibili-sample.json`](examples/social-content-parser-bilibili-sample.json)

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
│   ├── agent-pipeline-orchestration/
│   ├── markdown-platform-pack/
│   ├── miniapp-figma-alignment/
│   └── social-content-parser/
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

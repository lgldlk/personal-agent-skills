---
name: miniapp-figma-alignment
description: Align native mini-program, uni-app, Taro, and other mini-app framework pages to Figma designs with correct frame-width scaling, rpx/designWidth conversion, platform chrome handling, asset reuse, and visual QA. Use when implementing or fixing any mini-program UI from Figma links, screenshots, image-to-ui output, or user reports that a mini-program layout is too small, too large, misaligned, or not 1:1 with Figma.
---

# Miniapp Figma Alignment

## Official Baselines

Use these facts before applying project-specific rules:

- WeChat WXSS adds `rpx` as a responsive unit and defines the screen width as `750rpx`.
- uni-app supports `px` and `rpx`; for normal Vue page layout, treat `750rpx` as the full screen width unless the project has an explicit alternate unit system. Use `upx` only when maintaining older code that already uses it.
- uni-app `nvue`/`uvue`, App `titleNView`, plus APIs, canvas, and native APIs can have different unit rules. Verify before converting those values to `rpx`.
- Taro recommends writing design dimensions as `px` only when the project `designWidth` matches the design draft width. Taro's default `designWidth` is `750`, and `pxtransform` converts eligible lowercase `px`.
- Taro JS inline styles are not rewritten by compile-time `pxtransform`; convert values to final `rpx` or use the project's runtime helper.

Primary docs to check when uncertain:

- WeChat WXSS: `https://developers.weixin.qq.com/miniprogram/dev/framework/view/wxss.html`
- uni-app CSS and units: `https://uniapp.dcloud.net.cn/tutorial/syntax-css.html`
- Taro design and size units: `https://docs.taro.zone/docs/size`
- Taro compile config: `https://docs.taro.zone/docs/config`

## Core Rule

Treat Figma measurements as design-canvas pixels, not web CSS pixels. Always identify the target unit pipeline before writing dimensions.

General formula:

```text
scale = targetDesignWidth / figmaFrameWidth
targetValue = figmaPx * scale
```

Common targets:

- Native WeChat/Alipay/Douyin/QQ-style mini-program styles: usually `targetDesignWidth = 750`; verify the target platform's style language and then write `targetValue rpx` unless the platform or codebase uses another responsive unit.
- uni-app mini-program target: `targetDesignWidth = 750`, write `targetValue rpx` in page/component styles.
- Taro mini-program target with global `designWidth = 750`: choose one strategy per layout region. Either write final scaled `rpx`, or write project-design `px` that will be converted by `pxtransform`.
- Taro project whose `designWidth` equals the Figma frame width: stylesheet `px` may be 1:1, but still verify `pxtransform`, selector blacklists, and inline style behavior.

Do not assume `figmaFrameWidth = 750`. Designers may use `375`, `390`, `393`, `402`, `414`, `430`, `750`, or another frame width inside the same product.

## Inputs to Confirm

Before editing, establish:

- `framework`: native mini-program, uni-app, Taro, or another framework.
- `targetPlatform`: WeChat, Alipay, Douyin, QQ, Baidu, Kuaishou, DingTalk, Feishu, or mixed.
- `figmaFrameWidth`: read from Figma metadata/design context or the screenshot dimensions.
- `targetDesignWidth`: usually `750` for direct `rpx`; for Taro, read `designWidth`.
- `unitPipeline`: native stylesheet, uni-app style block, SCSS/Less, CSS modules, Tailwind/UnoCSS, inline style, or canvas/API pixel values.
- `runtimeChrome`: native/custom navigation, tab bar, capsule/menu button, status bar, safe area, popup, and fixed footer behavior.

## Platform Review Rules

Use this quick check before choosing a conversion pattern:

| Branch | Good default | Main exception |
| --- | --- | --- |
| Native mini-program | Convert Figma px to final `rpx` with `750 / figmaFrameWidth`. | Confirm platform file extensions and style-unit support; keep true hairlines and API pixel values as `px` when required. |
| uni-app | In Vue page styles, convert Figma px to `rpx` with `750 / figmaFrameWidth`. | `nvue`/`uvue`, App `titleNView`, plus APIs, canvas, and native modules can require `px` or have special semantics. |
| Taro | Prefer the existing project convention: final `rpx` helper or `pxtransform` via `designWidth`. | Do not mix final `rpx` and transformable `px` for the same Figma values in one layout region. Inline styles need runtime conversion. |

## First-Pass Investigation

Run targeted searches before editing:

```bash
rg -n "designWidth|deviceRatio|pxtransform|selectorBlackList|postcss-pxtransform" . --glob '!**/node_modules/**'
rg -n "toRpx|upx2px|pxTransform|px\\(|rpx\\(|750 /|designWidth" . --glob '!**/node_modules/**'
rg -n "navigationStyle|navigationBar|usingComponents|tabBar|pages.json|manifest.json|app.json" . --glob '!**/node_modules/**'
rg --files . --glob '*.wxml' --glob '*.wxss' --glob '*.axml' --glob '*.acss' --glob '*.ttml' --glob '*.ttss' --glob '*.qml' --glob '*.qss' --glob '*.vue' --glob '*.tsx' --glob '*.scss' --glob '*.less' --glob '!**/node_modules/**'
```

Then inspect:

- The exact page/component files and nearby sibling pages.
- The exact Figma node width, screenshot width, and intended phone model if given.
- Existing unit helpers, global SCSS variables, and project conventions.
- Whether static layout is in stylesheets and dynamic values are in inline style objects.
- The app/page navigation configuration and real mini-program chrome.

## Framework Detection

Use file/config shape to choose the branch:

- **Native WeChat**: `app.json`, `project.config.json`, `.wxml`, `.wxss`, `.js`, `.ts`.
- **Native Alipay**: `app.json`, `.axml`, `.acss`, `mini.project.json`.
- **Native Douyin/ByteDance**: `.ttml`, `.ttss`, platform project config.
- **Native QQ/Baidu/Kuaishou/DingTalk/Feishu**: platform templates plus style files similar to WXSS/CSS.
- **uni-app**: `pages.json`, `manifest.json`, `.vue` pages, `uni.scss`, `uni_modules`.
- **Taro**: `config/index.*`, `src/app.config.*`, `@tarojs/*`, `.tsx`/`.jsx` pages.
- **Other cross-frameworks**: identify their unit transform plugin and generated mini-program output before changing dimensions.

If the framework is ambiguous, inspect `package.json`, app config, and page extensions before assuming Taro.

## Workflow

1. Inspect the Figma node or screenshot before editing.
   - Use Figma design context for layout, text, colors, assets, and frame width.
   - If using image-to-ui output, load `image-to-ui-skill` first and separate code-rendered UI from bitmap assets.

2. Identify implementation context.
   - Confirm framework, target platform, and page route.
   - Read app/page config for navigation, tab bar, component registration, and safe-area behavior.
   - Check nearby pages for the established unit convention.

3. Choose the scaling strategy.
   - Direct `rpx` projects: write scaled `rpx` from the real Figma frame width.
   - Existing Taro project: do not change global `designWidth` for one page; use a local helper unless the whole project is moving to a new design system.
   - New Taro project: align `designWidth` and `deviceRatio` to the design draft if that is the product-wide standard.
   - Mixed design widths: keep path/package-specific helpers; only use Taro `designWidth(input)` when the project intentionally supports that pattern.
   - API/canvas/native pixels: convert `rpx` to device pixels with the platform/framework helper at runtime.

4. Compute scale from actual values.
   - Native/uni-app target: `scale = 750 / figmaFrameWidth`.
   - Taro target: `scale = taroDesignWidth / figmaFrameWidth` when converting to project design units, or `750 / figmaFrameWidth` when writing final `rpx` directly.
   - Keep the helper near the page styles or reuse an existing shared helper.

5. Convert dimensions consistently.
   - Convert width, height, padding, margin, gap, top, left, right, border-radius, font-size, line-height, and border widths.
   - Prefer flex, percentage, or `calc()` only where the design is genuinely responsive.
   - For safe-area spacing, combine scaled spacing with `env(safe-area-inset-bottom)` using the project's style syntax.
   - Avoid `vw` for fixed mobile Figma matching unless the existing codebase deliberately uses it.

6. Respect mini-program chrome and platform behavior.
   - Do not redraw battery, signal, status bar, or the platform capsule/menu button in a real mini-program page.
   - For custom navigation, use the project's navigation component or platform menu-button metrics.
   - For tab pages, do not add a back button unless the product flow requires one.
   - Verify fixed bottom buttons do not cover scroll content or safe-area padding.

7. Use real assets and configuration.
   - Prefer Figma-exported assets, configured remote assets, or backend/OSS content over CSS approximations.
   - Do not hard-code configurable examples, icons, prompts, limits, copy, or button text if the backend already owns them.
   - Keep route params, event channels, and page callbacks compatible with callers.

## Native Mini-Program Pattern

Use direct scaled `rpx` for Figma-derived layout:

```scss
/* frame width 390, target screen 750rpx */
$scale: 1.9231rpx; // 750 / 390

@function fp($value) {
  @return $value * $scale;
}

.card {
  width: fp(338);
  height: fp(296);
  padding: fp(16) fp(24);
  border-radius: fp(12);
  font-size: fp(14);
}
```

For plain `.wxss` or platform styles without Sass, either write computed `rpx` values or add a project-approved preprocessor. Avoid raw Figma `px` for layout.

```css
.card {
  width: 650rpx; /* 338 * 750 / 390 */
  border-radius: 23rpx;
}
```

For dynamic inline style:

```ts
const FIGMA_WIDTH = 390;
const toRpx = (value: number) => `${(value * 750 / FIGMA_WIDTH).toFixed(2)}rpx`;
```

Keep platform-required fixed pixels as `px`, especially 1px hairlines, canvas dimensions, and values passed to native APIs that explicitly require physical or logical pixels.

## uni-app Pattern

In `.vue` pages/components, prefer the existing `rpx` style convention:

```scss
$figma-width: 390;
$scale: 750rpx / $figma-width;

@function fp($value) {
  @return $value * $scale;
}

.action-panel {
  width: fp(338);
  padding: fp(20);
  border-radius: fp(12);
}
```

For runtime device pixels, convert responsive units through uni-app APIs/helpers only when a native API, canvas, or measurement call requires physical pixels. Do not replace stylesheet `rpx` with JS-calculated pixels for normal layout.

For `nvue`/`uvue`, App `titleNView`, plus APIs, or modules that are not regular Vue page CSS, read the local docs/config and nearby code first. In those contexts, `px` may be fixed, dynamic, or required depending on renderer and target platform.

## Taro Pattern

Read `designWidth`, `deviceRatio`, and `pxtransform` before editing. If the project uses `designWidth: 750` and Figma width is `402`, write scaled final `rpx`:

```scss
$scale: 1.8657rpx; // 750 / 402

@function fp($value) {
  @return $value * $scale;
}

.example-card {
  width: fp(338);
  height: fp(296);
  padding: fp(16) fp(32) fp(32);
  border-radius: fp(12);
  font-size: fp(14);
}
```

For TSX inline style objects:

```ts
const FIGMA_WIDTH = 402;
const toRpx = (value: number) => `${(value * 750 / FIGMA_WIDTH).toFixed(2)}rpx`;
```

If the codebase standardizes on `Taro.pxTransform`, pass values after converting Figma pixels to the project's design unit:

```ts
const figmaToProjectPx = (value: number) => value * (taroDesignWidth / figmaFrameWidth);
const width = Taro.pxTransform(figmaToProjectPx(338));
```

Do not call `Taro.pxTransform(338)` directly unless `figmaFrameWidth === taroDesignWidth`.

Two Taro strategies are valid; pick one and keep it consistent:

- **Final rpx strategy:** compute `figmaPx * 750 / figmaFrameWidth` and write `rpx` strings. This bypasses `pxtransform` for those values and works well for Figma-matched mini-program-only screens.
- **pxtransform strategy:** compute `figmaPx * taroDesignWidth / figmaFrameWidth`, write that as lowercase `px` in stylesheets or pass it to `Taro.pxTransform` at runtime. This keeps Taro's multi-end conversion behavior.

Do not write raw Figma `px` in Taro styles when `figmaFrameWidth !== taroDesignWidth`, and do not multiply a value into final `rpx` and then pass it through `Taro.pxTransform`.

## Scale Quick Reference

For `750rpx` target:

- Figma `375`: `2rpx`
- Figma `390`: `1.9231rpx`
- Figma `393`: `1.9084rpx`
- Figma `402`: `1.8657rpx`
- Figma `414`: `1.8116rpx`
- Figma `430`: `1.7442rpx`
- Figma `750`: `1rpx`

For other targets, recompute `targetDesignWidth / figmaFrameWidth`.

## Utility Class and Inline Style Notes

- Verify whether Tailwind/UnoCSS/arbitrary values are transformed before using arbitrary `px` classes.
- For Figma-matched screens, prefer a small SCSS/helper function over long arbitrary utility values.
- Search changed files for raw Figma numbers in inline styles and convert them through `toRpx`, `fp`, final `rpx` strings, or the local equivalent as appropriate.
- Keep 1px hairlines intentional; do not scale them blindly if the platform/component expects a physical border.
- Do not use `uni.upx2px`, `Taro.pxTransform`, or platform pixel APIs for normal stylesheet layout unless the codebase already uses that runtime path.

## Visual QA Checklist

Before reporting completion:

- State framework, target platform, Figma frame width, target design width, and scale/helper used.
- Run `rg -n "[0-9]+px" <changed-style-files>` and justify remaining CSS `px`.
- Search inline styles in changed TS/JS/Vue/TSX files for raw design numbers.
- Run the project’s scoped type check or build command for the changed mini-program app.
- Compare the page against the Figma screenshot at the same phone width.
- Check width, top spacing, tab underline, primary button size, card width, image aspect ratio, and fixed bottom placement.
- Check custom navigation, capsule/menu-button clearance, tab bar, and safe-area spacing on real target platform assumptions.
- Check text overflow with real configured/backend copy.

## Common Failure Modes

- **Everything is half-size:** Figma `px` was written directly into a `750rpx` mini-program layout. Convert with `750 / figmaFrameWidth`.
- **Everything is too large:** the Figma frame was already `750` wide, but values were multiplied again.
- **Only one design matches:** the scale was hard-coded for one frame width. Re-read the actual Figma node each time.
- **Inline styles ignore compile transforms:** JS/Vue style objects need explicit `rpx` strings or runtime helpers.
- **Native page shows duplicated chrome:** system status/capsule UI was drawn manually. Use platform navigation metrics instead.
- **Looks correct in H5 but wrong in WeChat/Alipay/Douyin:** verify in mini-program units and target runtime, not only browser CSS.
- **Assets differ from Figma/app config:** use exported or configured assets instead of approximations.

## Completion Report Template

When finishing a mini-program/Figma alignment task, report:

- Framework/platform:
- Figma node/frame width:
- Target design width:
- Scale/helper used:
- Files changed:
- Remaining raw `px` and why:
- Verification command:
- Known visual risks:

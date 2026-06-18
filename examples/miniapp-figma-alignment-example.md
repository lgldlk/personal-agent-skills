# Miniapp Figma Alignment Example

This is a compact example of the reasoning shape produced by `miniapp-figma-alignment`.

## Input

- Framework: Taro
- Target platform: WeChat Mini Program
- Figma frame width: `390`
- Project design width: `750`
- Reported issue: UI appears half-size after copying Figma values directly into styles.

## Alignment Plan

| Checkpoint | Result |
|---|---|
| Framework branch | Taro mini-program |
| Unit pipeline | SCSS stylesheets plus TSX inline styles |
| Scale | `750 / 390 = 1.9231` |
| Static layout | Convert Figma px to final `rpx` via `fp(value)` |
| Inline styles | Convert runtime values with `toRpx(value)` |
| Platform chrome | Do not redraw status bar or capsule; use existing navigation component |
| QA | Compare against Figma at same phone width; justify remaining raw `px` |

## Example Conversion

```scss
$scale: 1.9231rpx; // 750 / 390

@function fp($value) {
  @return $value * $scale;
}

.card {
  width: fp(338);
  padding: fp(16) fp(24);
  border-radius: fp(12);
}
```

## Completion Report Shape

- Framework/platform: Taro / WeChat Mini Program
- Figma node/frame width: `390`
- Target design width: `750`
- Scale/helper used: `fp(value) = value * 750 / 390 rpx`
- Remaining raw `px`: only intentional 1px hairlines
- Verification command: project-specific build/typecheck
- Known visual risks: real device capsule/menu-button clearance and safe-area spacing

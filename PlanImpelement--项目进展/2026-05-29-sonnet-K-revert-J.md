# 2026-05-29 sonnet K — 删除 ! 恢复等比 resize

## 起因
sonnet J (9a31a91) 加 `!` 强拉 410×502 后, sheng 真机看到纵向被拉长 1.9x, 身体严重变形 (横 0.52x / 纵 0.996x 非等比), 比修复前 410×262 等比缩放的画面更差。

## 改动
- `gen_pngseq.sh:75`: `-resize 410x502!` → `-resize 410x502` (删 1 个 `!` 字符)
- 9 action × 247 帧全部重烘, .h 502 → 262

## 验证 grep
- 改前: `grep "resize 410"` → `410x502!`
- 改后: `grep "resize 410"` → `410x502` (无 !)
- `grep -c "410x502!"` → 0
- walk/jump/idle/hit/roll _00 全部 410×262 ✅
- build_assets.sh exit 0 ✅

## git
- pipeline commit: `61f274f` pushed to origin/main
- lvgl commit: `658b950` pushed to origin/master

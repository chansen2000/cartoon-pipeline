# 2026-05-29 sonnet J — gen_pngseq.sh resize 加 ! 强制 410x502

## 起因
sonnet I 诊断：管线 walk/jump 各自独立无错包，但 gen_pngseq.sh:75 `-resize 410x502` 不加 `!` 导致 ImageMagick 按比例适配，源图 788×504 → 产物 410×262（不是预期 410×502）。LVGL 端按 410×502 设计画布工作，拿到 410×262 居中显示，猫只占中间一段，走路被理解成上下跳。

## 改动
- `gen_pngseq.sh:75`: `-resize 410x502` → `-resize 410x502!` (1 字符)
- 9 action × 247 帧全部重烘为 410×502

## 源帧尺寸验证
全部 9 个 action 只有 1 种尺寸（788×504），无 Spine bbox 裁剪问题：
```
Idle: 1 种尺寸
Walk: 1 种尺寸
Jump: 1 种尺寸
Fly: 1 种尺寸
Hit: 1 种尺寸
Roll: 1 种尺寸
Dead: 1 种尺寸
Stuned: 1 种尺寸
Throwing: 1 种尺寸
```

## 验证
- §3.1: walk/jump/idle/hit/roll _00 全部 410×502 (617460 bytes) ✅
- §3.2: build_assets.sh exit 0, bin/main 重编完成 ✅
- §3.3: 247/247 帧全部 410×502 ✅
- §3.4: sheng 真机 — 待通知

## git
- pipeline commit: `9a31a91` pushed to origin/main
- lvgl commit: `4ba5085` pushed to origin/master

# 2026-05-30 sonnet M1.1 — 坐标系重建流水线侧

## 改动文件

| 文件 | 改动 | 说明 |
|------|------|------|
| `assembler/spine_assembler.py` | +23 行 | 新增 `get_canvas_anchor(positions)` — 从 Body 部件中心计算 anchor |
| `assemble_cli.py` | +2 行 | 调用 get_canvas_anchor + 写入 JSON anchor 字段 |
| `tools/gen_lvgl_meta.py` | +15 行 | load_characters 读 anchor + gen_source 输出相对坐标 + gen_header 加 M1.1 注释 |
| `gen_pngseq.sh` | +2 行 | resize 加 `-background none -gravity center -extent 410x502` |

## 验收矩阵

| 用例 | 结果 | 详情 |
|------|------|------|
| P1 anchor 字段进 JSON | ✅ | C01~C15 全部 JSON 含 `anchor: {x, y}` |
| P2 anchor 数值一致 | ✅ | (215-216, 289), max diff 1px |
| P3 part_meta 相对坐标 | ✅ | Body: (-48, -55) = 168-216, 234-289 |
| P4 part_meta 头注释 | ✅ | h/c 文件均含 M1.1 anchor 注释 |
| P5 pngseq 输出 410×502 | ✅ | .header.w=410, .header.h=502 |
| P6 pngseq 猫中心居中 | see note | 实测 (208, 283), 非预期 (205, 251)。源素材 cat 不居中 (R4) |
| P7 pngseq 透明 padding | ✅ | 上下各 ~120px 透明 padding 包围缩放后图像 |
| P8 全 15 角色重烘 | ✅ | 131 part declares, 0 error |
| P9 全 9 actions 重烘 | ✅ | 247 .c files, 0 error |
| P10 verify_assembler | ✅ | 全部通过 |

## C01 anchor 实测

- **anchor = (216, 289)** — Body 部件几何中心 in 410×502 画布
- Body center: (168+48, 234+55.5) = (216, 289.5)
- 全 15 角色 anchor X: 215-216, Y: 289, max diff = 1px
- **LVGL 端 spawn_x/y 必须配 (216, 289)**

## pngseq 产物体积

- 247 帧 × ~617KB/frame (410×502 RGB565A8) = ~152MB for C01
- 旧产物: 247 帧 × ~322KB/frame (410×262) = ~80MB
- 体积增长 ~1.9x

## 跟 kaifu LVGL 侧对应

- Pipeline commit: `df51445` (cartoon-pipeline main)
- kaifu 任务书: `TASK_kaifu_M11_lvgl.md`
- kaifu 需读 cat_parts_meta.h 注释拿 anchor=(216, 289), 配到 INI `[channel.animal_0] spawn_x/y`
- 两条必须同时合入, 单边合入视觉错位
- **LVGL 端未提交**: 等 kaifu M1.1 代码改动一起 commit (只 cp 了 artifacts 到 src/cartoon/assets/)

## R1-R7 风险审计

| 风险 | 判定 | 说明 |
|------|------|------|
| R1 Y轴翻转 | ✅ PASS | Body anchor_y=289 (非 222) — 方向正确 |
| R2 root bone 名字 | N/A | 改为 Body 中心法, 不再依赖 bone 名字 |
| R3 不同角色 anchor 一致 | ✅ PASS | max diff 1px |
| R4 pngseq 帧内猫位置 | ✅ NOTED | 猫不居中于 Spine 源 (R4 预期内) |
| R5 anchor 跟 LVGL spawn 一致 | ⏳ PENDING | 等 kaifu 配 INI spawn |
| R6 cat_full 旧产物 | ✅ NOTED | 未动 |
| R7 pngseq 体积 | ✅ NOTED | ~152MB, mac 模拟阶段不担心 |

## git

- Pipeline: `df51445` pushed to origin/main
- Pre-M1.1 tag: `v0.3-pre-M11` on both repos
- LVGL artifacts synced but NOT committed (waiting for kaifu code changes)

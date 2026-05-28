# Sonnet Task H — Eye 动画切换 blink: 流水线 + INI 默认值

**日期**: 2026-05-28
**状态**: ✅ 完成

## 改动

| 文件 | 操作 | 说明 |
|------|------|------|
| `config/小猫/animation_config.ini` | 修改 | [part.eye] spin→blink, duration_ms=800→200, amplitude=3600→16 |
| `tools/gen_lvgl_meta.py` | 修改 | ANIM_MAP 加 `"blink": "PART_ANIM_BLINK"` |
| `tools/validate_animation_config.py` | 无改动 | 无 anim_type 校验集合，跳过 |

## 验证结果

| # | 项 | 结果 |
|---|-----|------|
| 1 | git diff INI | ✅ [part.eye] 3 行 + 注释 |
| 2 | git diff gen_lvgl_meta.py | ✅ ANIM_MAP +1 行 |
| 3 | git diff validator | ✅ 0 改动 (无 anim_type 校验) |
| 4 | build_assets.sh --fast | ✅ exit 0, 编译通过 |
| 5 | INI cp 到 LVGL | ✅ anim_type=blink |
| 6 | xxd 嵌入 data.h | ✅ blink 已在 C 数组 |
| 7 | SDL 窗口眨眼 | ⚠️ 需 display 验证 |
| 8 | amplitude=8 --fast | ✅ compile OK |
| 9 | amplitude=64 --fast | ✅ compile OK |
| 10 | 还原 amplitude=16 | ✅ compile OK |

## 前置依赖

kaifu Task G ✅ 已合入: ANIM_BLINK enum + "blink" parser + Y轴压扁实现

## git

- commit: `8e3aa30` — Task H: Eye anim_type spin→blink
- push: ✅ main → origin/main

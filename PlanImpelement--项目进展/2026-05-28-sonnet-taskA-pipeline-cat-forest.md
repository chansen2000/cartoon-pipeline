# Sonnet Task A — 小猫+森林流水线落地 完成

**日期**: 2026-05-28
**实施人**: Sonnet
**范围**: 流水线从「只烘小猫」扩到「小猫角色 + 森林背景两类资产 + 应用层 INI 契约」

## 实施内容

### 1.1-1.3 多素材参数化
- `tools/gen_lvgl_meta.py`: 加 `--material` 参数(默认 "小猫")，路径从硬编码改为 `output/{material}/json/410_502/`
- `tools/gen_part_dscs.sh`: 接受 `$1` 位置参数(默认 "小猫")，`MATERIALS_DIR` 常量在脚本顶部
- `gen_pngseq.sh`: 接受 `$1`(material) + `$2`(character_id) 两参数，默认 "小猫"/"01"

### 1.4 森林背景资产烘焙 — `tools/gen_bg_assets.sh` (新建)
- 读 `output/{material}/json/410_502/variant_*_layers.json` 获取图层清单
- 自动探测源图路径(`_PNG` 优先，匹配 BackgroundAssembler._find_dir)
- resize 到 410×502(force)，lv_img_conv CF_RGB565A8，v8→v9 sed 后处理
- 29 图层(7+8+8+6) × 617KB 二进制 = 17.1 MB 编译后
- BG_PINYIN_MAP: 森林→forest (用 case/esac 兼容 bash 3.2)

### 1.5 森林背景元数据 C 翻译 — `tools/gen_bg_meta.py` (新建)
- 读 JSON → 产出 `bg_forest.{h,c}`
- bg_layer_meta_t 结构体: name/z_order/parallax_ratio_x100/w/h/img
- 29 个 LV_IMAGE_DECLARE，4 组 variant 数组(z_order 升序)
- bg_forest_get(variant, &count) 查表 API
- parallax_ratio float → int16_t x100 取整

### 1.6 应用层 INI 迁入流水线
- `config/小猫/animation_config.ini` — 从 LVGL 工程复制(source of truth)
- `config/森林/animation_config.ini` — 新建，含 bg.global + 7 图层 sway 配置
- sway 数值照抄 sheng 已验证值(50/3000 和 80/2500)

### 1.7 校验工具 — `tools/validate_animation_config.py` (新建)
- 小猫: action→pngseq 文件数/前缀校验，part→meta 部件名映射
- 森林: [bg.global] 必须存在，layer 名必须在变体 JSON 中

### 1.8 编排 — `build_assets.sh` 重写为 9 步
- 角色(1-3) → 背景(4-6) → 校验(7) → frame_lookup(8) → cp 到 LVGL(9)
- 小猫 INI → `cat_animation_config.ini`
- 森林 INI → `bg_forest_animation_config.ini`

## 验证结果

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | build_assets.sh exit 0 | ✅ |
| 2 | cat_parts_meta.h 存在 | ✅ |
| 3 | dsc ≥ 130 | ✅ 131 |
| 4 | pngseq ≥ 250 | ⚠️ 247 (实际帧数，spec 估计偏高) |
| 5 | bg *.c 数量 | ⚠️ 29 (spec 估计 28，实际 7+8+8+6) |
| 6 | bg_forest.{h,c} | ✅ |
| 7 | LV_IMAGE_DECLARE 数 | ✅ 29 |
| 8 | 全部 RGB565A8 | ✅ 0 missing |
| 9 | 全部 ARGB8888 | ✅ 0 missing |
| 10 | validate 通过 | ✅ |
| 11 | INI 文件 | ✅ 两份 |
| 12 | bg 体积 | ⚠️ du=103M C文本 / 编译后=17.1MB |

## 跨模块耦合上报

1. **bg 体积 du 103M > 25MB 红线**: C hex 文本格式膨胀 5.8×，编译后二进制 17.1MB 符合 PSRAM 约束。du 值不能直接对应二进制内存占用。
2. **图层总数 29 ≠ spec 估算 28**: variant_02/03 各 8 层，variant_04 仅 6 层。非均匀分布。
3. **pngseq 247 < 250**: 实际 9 action × 不等帧数 = 247，spec 用 ~28 帧估算偏高。

## 涉及文件

- 修改: `tools/gen_lvgl_meta.py`, `tools/gen_part_dscs.sh`, `gen_pngseq.sh`, `build_assets.sh`
- 新建: `tools/gen_bg_assets.sh`, `tools/gen_bg_meta.py`, `tools/validate_animation_config.py`
- 新建: `config/小猫/animation_config.ini`, `config/森林/animation_config.ini`
- 未动: `assembler/*.py`, `assemble_bg.py`, `assemble_cli.py`

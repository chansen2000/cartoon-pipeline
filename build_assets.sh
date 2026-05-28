#!/bin/bash
# TVCartoon 素材流水线 → LVGL 工程 资产生成 & 拷贝
#
# 用法: bash build_assets.sh
#
# 产出:
#   output/小猫/lvgl_export/  — 角色资产 (meta + dsc + pngseq)
#   output/森林/lvgl_export/  — 背景资产 (meta + bg)
#   config/小猫/animation_config.ini → LVGL cat_animation_config.ini
#   config/森林/animation_config.ini → LVGL bg_forest_animation_config.ini
#
# LVGL 工程零修改 — 产物由本脚本拷入,CMake 自动 GLOB

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 配置变量 ──────────────────────────────────────────
LVGL_PROJECT_DIR="/Users/chansen2000/Downloads/lv_port_pc_vscode"
LVGL_ASSETS_DIR="$LVGL_PROJECT_DIR/src/cartoon/assets"
LVGL_BG_DIR="$LVGL_ASSETS_DIR/bg"
LVGL_CONFIG_DIR="$LVGL_PROJECT_DIR/src/cartoon/config"
# ───────────────────────────────────────────────────────

echo "=== TVCartoon build_assets ==="
echo ""

# ── 角色: 小猫 ────────────────────────────────────────

echo "[1/9] gen_lvgl_meta --material 小猫"
python3 tools/gen_lvgl_meta.py --material 小猫
echo ""

echo "[2/9] gen_part_dscs 小猫"
bash tools/gen_part_dscs.sh 小猫
echo ""

echo "[3/9] gen_pngseq 小猫 01"
bash gen_pngseq.sh 小猫 01
echo ""

# ── 背景: 森林 ────────────────────────────────────────

echo "[4/9] assemble_bg --material 森林 --all --target 410x502 --export-lvgl"
python3 assemble_bg.py --material 森林 --all --target 410x502 --export-lvgl
echo ""

echo "[5/9] gen_bg_assets 森林"
bash tools/gen_bg_assets.sh 森林
echo ""

echo "[6/9] gen_bg_meta 森林"
python3 tools/gen_bg_meta.py --material 森林
echo ""

# ── 校验 ──────────────────────────────────────────────

echo "[7/9] validate_animation_config"
python3 tools/validate_animation_config.py
echo ""

# ── frame_lookup (LVGL 端工具, 先 cp pngseq 再调) ─────

echo "[8/9] gen_frame_lookup"
mkdir -p "$LVGL_ASSETS_DIR/pngseq"
cp -v output/小猫/lvgl_export/pngseq/pngseq_C01_*.c "$LVGL_ASSETS_DIR/pngseq/"
python3 "$LVGL_PROJECT_DIR/tools/gen_frame_lookup.py" \
    "$LVGL_ASSETS_DIR/pngseq" \
    "$LVGL_ASSETS_DIR/frame_lookup.c"
echo ""

# ── 拷贝产物到 LVGL 工程 ──────────────────────────────

echo "[9/9] cp assets → LVGL"
cp -v output/小猫/lvgl_export/meta/cat_parts_meta.{h,c} "$LVGL_ASSETS_DIR/"
cp -v output/小猫/lvgl_export/dsc/cat_C*.c "$LVGL_ASSETS_DIR/"

mkdir -p "$LVGL_BG_DIR/森林"
cp -v output/森林/lvgl_export/bg/bg_forest_*.c "$LVGL_BG_DIR/森林/"
cp -v output/森林/lvgl_export/meta/bg_forest.{h,c} "$LVGL_BG_DIR/森林/"

cp -v config/小猫/animation_config.ini "$LVGL_CONFIG_DIR/cat_animation_config.ini"
cp -v config/森林/animation_config.ini "$LVGL_CONFIG_DIR/bg_forest_animation_config.ini"

echo ""
echo "Done. LVGL project now has:"
echo "  cat_parts_meta.{h,c}"
echo "  cat_C*.c ($(ls "$LVGL_ASSETS_DIR"/cat_C*.c 2>/dev/null | wc -l | xargs) files)"
echo "  pngseq/pngseq_C01_*.c ($(ls "$LVGL_ASSETS_DIR/pngseq"/*.c 2>/dev/null | wc -l | xargs) files)"
echo "  bg/森林/bg_forest_*.c ($(ls "$LVGL_BG_DIR/森林"/*.c 2>/dev/null | wc -l | xargs) files)"
echo "  bg/森林/bg_forest.{h,c}"
echo "  frame_lookup.c"
echo "  config/cat_animation_config.ini"
echo "  config/bg_forest_animation_config.ini"

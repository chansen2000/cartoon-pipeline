#!/bin/bash
# TVCartoon 素材流水线 → LVGL 工程 资产生成 & 拷贝 → xxd 嵌入 → 二进制重编
#
# 用法: bash build_assets.sh
#
# 产出:
#   output/小猫/lvgl_export/  — 角色资产 (meta + dsc + pngseq)
#   output/森林/lvgl_export/  — 背景资产 (meta + bg)
#   config/小猫/animation_config.ini → LVGL cat_animation_config.ini
#   config/森林/animation_config.ini → LVGL bg_forest_animation_config.ini
#   LVGL cat_animation_config_data.h / bg_forest_animation_config_data.h (xxd)
#   LVGL bin/main (make 重编)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 配置变量 ──────────────────────────────────────────
LVGL_PROJECT_DIR="/Users/chansen2000/Downloads/lv_port_pc_vscode"
LVGL_ASSETS_DIR="$LVGL_PROJECT_DIR/src/cartoon/assets"
LVGL_BG_DIR="$LVGL_ASSETS_DIR/bg"
LVGL_CONFIG_DIR="$LVGL_PROJECT_DIR/src/cartoon/config"
# ───────────────────────────────────────────────────────

# ── 旗标解析 ──────────────────────────────────────────
FAST_MODE=0
for arg in "$@"; do
    case "$arg" in
        --fast) FAST_MODE=1 ;;
        *) echo "未知参数: $arg"; exit 1 ;;
    esac
done

if [ $FAST_MODE -eq 1 ]; then
    echo "=== TVCartoon build_assets [FAST] ==="
    echo "(跳过资产生成 [1]~[8], 只跑 INI cp + xxd + make)"
else
    echo "=== TVCartoon build_assets ==="
fi
echo ""

if [ $FAST_MODE -eq 0 ]; then

# ── 角色: 小猫 ────────────────────────────────────────

echo "[1/11] gen_lvgl_meta --material 小猫"
python3 tools/gen_lvgl_meta.py --material 小猫
echo ""

echo "[2/11] gen_part_dscs 小猫"
bash tools/gen_part_dscs.sh 小猫
echo ""

echo "[3/11] gen_pngseq 小猫 01"
bash gen_pngseq.sh 小猫 01
echo ""

# ── 背景: 森林 ────────────────────────────────────────

echo "[4/11] assemble_bg --material 森林 --all --target 410x502 --export-lvgl"
python3 assemble_bg.py --material 森林 --all --target 410x502 --export-lvgl
echo ""

echo "[5/11] gen_bg_assets 森林"
bash tools/gen_bg_assets.sh 森林
echo ""

echo "[6/11] gen_bg_meta 森林"
python3 tools/gen_bg_meta.py --material 森林
echo ""

# ── 校验 ──────────────────────────────────────────────

echo "[7/11] validate_animation_config"
python3 tools/validate_animation_config.py
echo ""

# ── frame_lookup (LVGL 端工具, 先 cp pngseq 再调) ─────

echo "[8/11] gen_frame_lookup"
mkdir -p "$LVGL_ASSETS_DIR/pngseq"
cp -v output/小猫/lvgl_export/pngseq/pngseq_C01_*.c "$LVGL_ASSETS_DIR/pngseq/"
python3 "$LVGL_PROJECT_DIR/tools/gen_frame_lookup.py" \
    "$LVGL_ASSETS_DIR/pngseq" \
    "$LVGL_ASSETS_DIR/frame_lookup.c"
echo ""

fi  # FAST_MODE skip [1]~[8]

# ── 拷贝产物到 LVGL 工程 ──────────────────────────────

if [ $FAST_MODE -eq 0 ]; then
    echo "[9/11] cp assets → LVGL"
    cp -v output/小猫/lvgl_export/meta/cat_parts_meta.{h,c} "$LVGL_ASSETS_DIR/"
    cp -v output/小猫/lvgl_export/dsc/cat_C*.c "$LVGL_ASSETS_DIR/"

    mkdir -p "$LVGL_BG_DIR/森林"
    cp -v output/森林/lvgl_export/bg/bg_forest_*.c "$LVGL_BG_DIR/森林/"
    cp -v output/森林/lvgl_export/meta/bg_forest.{h,c} "$LVGL_BG_DIR/森林/"
    echo ""
fi

echo "[9/11] cp INI → LVGL"
cp -v config/小猫/animation_config.ini "$LVGL_CONFIG_DIR/cat_animation_config.ini"
cp -v config/森林/animation_config.ini "$LVGL_CONFIG_DIR/bg_forest_animation_config.ini"
echo ""

# ── INI 嵌入 C 数组 (xxd) ──────────────────────────────

echo "[10/11] xxd embed INI → C arrays"
cd "$LVGL_CONFIG_DIR"
xxd -i cat_animation_config.ini > cat_animation_config_data.h
xxd -i bg_forest_animation_config.ini > bg_forest_animation_config_data.h
echo "  → cat_animation_config_data.h"
echo "  → bg_forest_animation_config_data.h"
cd "$SCRIPT_DIR"
echo ""

# ── LVGL 工程重编 ─────────────────────────────────────

echo "[11/11] rebuild LVGL binary"
LVGL_BUILD_DIR="$LVGL_PROJECT_DIR/build_mac"
mkdir -p "$LVGL_BUILD_DIR"
cd "$LVGL_BUILD_DIR"
if [ ! -f "CMakeCache.txt" ]; then
    echo "  build_mac/ 未配置, 先 cmake"
    cmake -DCMAKE_BUILD_TYPE=Release ..
fi
make -j8
cd "$SCRIPT_DIR"
echo "  → $LVGL_PROJECT_DIR/bin/main"
echo ""

echo "Done. LVGL project now has:"
if [ $FAST_MODE -eq 0 ]; then
    echo "  cat_parts_meta.{h,c}"
    echo "  cat_C*.c ($(ls "$LVGL_ASSETS_DIR"/cat_C*.c 2>/dev/null | wc -l | xargs) files)"
    echo "  pngseq/pngseq_C01_*.c ($(ls "$LVGL_ASSETS_DIR/pngseq"/*.c 2>/dev/null | wc -l | xargs) files)"
    echo "  bg/森林/bg_forest_*.c ($(ls "$LVGL_BG_DIR/森林"/*.c 2>/dev/null | wc -l | xargs) files)"
    echo "  bg/森林/bg_forest.{h,c}"
    echo "  frame_lookup.c"
fi
echo "  config/cat_animation_config.ini"
echo "  config/bg_forest_animation_config.ini"
echo "  bin/main  ($(stat -f '%Sm' "$LVGL_PROJECT_DIR/bin/main"))"

#!/bin/bash
# TVCartoon 素材流水线 → LVGL 工程 资产生成 & 拷贝
#
# 用法: bash build_assets.sh
#
# LVGL 工程零修改 — 产物由本脚本拷入,CMake 自动 GLOB

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 配置变量 ──────────────────────────────────────────
LVGL_PROJECT_DIR="/Users/chansen2000/Downloads/lv_port_pc_vscode"
LVGL_ASSETS_DIR="$LVGL_PROJECT_DIR/src/cartoon/assets"
# ───────────────────────────────────────────────────────

echo "=== TVCartoon build_assets ==="
echo ""

# Step 1: 生成 LVGL meta (part_meta_t 数组 + 查表函数)
echo "[1/5] gen_lvgl_meta.py ..."
python3 tools/gen_lvgl_meta.py
echo ""

# Step 2: 单部件 dsc (Spine raw PNG → resize 到 410 视角 → ARGB8888 C 数组)
echo "[2/5] gen_part_dscs.sh ..."
bash tools/gen_part_dscs.sh
echo ""

# Step 3: PNG 序列 → RGB565A8 C 数组 (lv-img-conv)
echo "[3/5] gen_pngseq.sh ..."
bash gen_pngseq.sh
echo ""

# Step 4: 生成 frame_lookup.c (扫描 pngseq C 文件 → 静态映射表)
echo "[4/5] gen_frame_lookup ..."
# 先拷贝 pngseq C 文件到 LVGL 工程,gen_frame_lookup.py 扫描该目录
mkdir -p "$LVGL_ASSETS_DIR/pngseq"
cp -v output/小猫/lvgl_export/pngseq/pngseq_C01_*.c "$LVGL_ASSETS_DIR/pngseq/"
python3 "$LVGL_PROJECT_DIR/tools/gen_frame_lookup.py" \
    "$LVGL_ASSETS_DIR/pngseq" \
    "$LVGL_ASSETS_DIR/frame_lookup.c"
echo ""

# Step 5: 拷贝所有产物 → LVGL 工程
echo "[5/5] copy assets → LVGL project ..."
cp -v output/小猫/lvgl_export/meta/cat_parts_meta.h "$LVGL_ASSETS_DIR/"
cp -v output/小猫/lvgl_export/meta/cat_parts_meta.c "$LVGL_ASSETS_DIR/"
echo "  dsc/*.c → $LVGL_ASSETS_DIR/"
cp -v output/小猫/lvgl_export/dsc/cat_C*.c "$LVGL_ASSETS_DIR/"
echo ""

echo "Done. LVGL project assets/ now has:"
echo "  cat_parts_meta.{h,c}"
echo "  cat_C*.c ($(ls "$LVGL_ASSETS_DIR"/cat_C*.c 2>/dev/null | wc -l | xargs) files)"
echo "  pngseq/pngseq_C01_*.c ($(ls "$LVGL_ASSETS_DIR/pngseq"/*.c 2>/dev/null | wc -l | xargs) files)"
echo "  frame_lookup.c"
ls -la "$LVGL_ASSETS_DIR"/cat_parts_meta.* "$LVGL_ASSETS_DIR"/frame_lookup.c 2>/dev/null

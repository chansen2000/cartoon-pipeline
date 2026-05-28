#!/bin/bash
# 森林背景资产烘焙: 每图层 PNG → LVGL RGB565A8 C 数组
#
# 用法: bash tools/gen_bg_assets.sh [material]
#   material 默认 "小猫" (但本脚本只对背景包有意义, 如 "森林")
#
# 输入:
#   output/{material}/json/410_502/variant_*_layers.json — 图层清单
#   素材/选择/{material}/_PNG/{variant}/layers/{layer}.png — 原图
#   或 素材/选择/{material}/PNG/{variant}/layers/{layer}.png (自动探测)
#
# 输出: output/{material}/lvgl_export/bg/bg_{ascii}_{variant}_{layer}.c
# 格式: RGB565A8 (3 byte/pixel, 保留 alpha 用于图层叠加)

set -e

MATERIALS_DIR="/Users/chansen2000/Downloads/素材/选择"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PIPELINE_DIR"

MATERIAL="${1:-小猫}"

# ASCII 别名映射 (中文素材名 → 合法 C 标识符)
_ascii_name() {
    case "$1" in
        森林) echo "forest" ;;
        *)     echo "$1" ;;
    esac
}
ASCII_NAME=$(_ascii_name "$MATERIAL")

JSON_DIR="output/$MATERIAL/json/410_502"
OUT_DIR="output/$MATERIAL/lvgl_export/bg"

TARGET_W=410
TARGET_H=502

mkdir -p "$OUT_DIR"

# 探测源图目录: _PNG 优先 (匹配 BackgroundAssembler._find_dir)
SRC_BASE=""
if [ -d "$MATERIALS_DIR/$MATERIAL/_PNG" ]; then
    SRC_BASE="$MATERIALS_DIR/$MATERIAL/_PNG"
elif [ -d "$MATERIALS_DIR/$MATERIAL/PNG" ]; then
    SRC_BASE="$MATERIALS_DIR/$MATERIAL/PNG"
else
    echo "ERROR: 找不到源图目录 $MATERIALS_DIR/$MATERIAL/_PNG 或 .../PNG" >&2
    exit 1
fi
echo "SRC_BASE=$SRC_BASE"

TOTAL_LAYERS=0
shopt -s nullglob
for json_file in "$JSON_DIR"/variant_*_layers.json; do
    variant=$(basename "$json_file" | sed -E 's/variant_(.+)_layers\.json/\1/')
    layer_count=$(python3 -c "import json; print(len(json.load(open('$json_file'))['layers']))")

    echo ""
    echo "── variant $variant: $layer_count layers ──"

    # 读 JSON 取图层列表 (按 z_order 排序)
    layers_json=$(python3 -c "
import json
with open('$json_file') as f:
    data = json.load(f)
layers = sorted(data['layers'], key=lambda l: l['z_order'])
for l in layers:
    print(l['name'])
")

    while IFS= read -r layer; do
        layer_safe="${layer//[^a-zA-Z0-9_]/_}"
        var_name="bg_${ASCII_NAME}_${variant}_${layer_safe}"

        # 找源图: {variant}/layers/{layer}.png
        src_png="$SRC_BASE/${variant}/layers/${layer}.png"
        if [ ! -f "$src_png" ]; then
            # fallback: 直接用图层名
            src_png="$SRC_BASE/${variant}/layers/${layer_safe}.png"
        fi

        if [ ! -f "$src_png" ]; then
            echo "  ❌ MISS: $var_name (tried $SRC_BASE/${variant}/layers/${layer}.png)" >&2
            exit 1
        fi

        out_c="$OUT_DIR/${var_name}.c"

        # Resize → 410×502, then convert to RGB565A8 C array
        magick "$src_png" -resize ${TARGET_W}x${TARGET_H}! /tmp/_bg_resized.png
        npx lv_img_conv \
            -f \
            -i "$var_name" \
            -c CF_RGB565A8 \
            -o "$out_c" \
            /tmp/_bg_resized.png 2>&1 | grep -v "^$" || true
        # Post-process: lv_img_conv v0.4.0 outputs LVGL v8, convert to v9
        sed -i '' \
            -e 's/LV_IMG_CF_RGB565A8/LV_COLOR_FORMAT_RGB565A8/g' \
            -e 's/LV_IMG_PX_SIZE_ALPHA_BYTE/3/g' \
            -e '/\.header\.always_zero = 0,/d' \
            -e 's/\.header\.reserved = 0/\.header\.reserved_2 = 0/g' \
            "$out_c"

        TOTAL_LAYERS=$((TOTAL_LAYERS + 1))
        echo "    $layer → $var_name"
    done <<< "$layers_json"
done

rm -f /tmp/_bg_resized.png

echo ""
echo "=== Done: $TOTAL_LAYERS layers → $OUT_DIR ==="
ls "$OUT_DIR"/*.c 2>/dev/null | wc -l | xargs echo "Total .c files:"

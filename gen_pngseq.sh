#!/bin/bash
# TVCartoon PNG 序列 → LVGL C 数组 批量转换
#
# 用法: bash gen_pngseq.sh [material] [character_id]
#   material     默认 "小猫"
#   character_id 默认 "01"
#
# 输入: 素材/选择/{material}/Png/Character{id}/<Action>/*.png (788×504 RGBA)
# 输出: output/{material}/lvgl_export/pngseq/pngseq_C{id}_<action>_<NN>.c (410×502 RGB565A8)
#
# 工具: ImageMagick (resize) + lv_img_conv (RGB565A8 C 数组)
# 按 SPEC §6.2 要求使用 LVGL 官方 lv-img-conv,不自写编码

set -e

MATERIALS_DIR="/Users/chansen2000/Downloads/素材/选择"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MATERIAL="${1:-小猫}"
CHAR_ID="${2:-01}"

SRC="$MATERIALS_DIR/$MATERIAL/Png/Character$CHAR_ID"
OUT_DIR="output/$MATERIAL/lvgl_export/pngseq"

mkdir -p "$OUT_DIR"

# Action → (lowercase_name, expected_frame_count)
# Order matches SPEC §4.2: dead, fly, hit, idle, jump, roll, stuned, throwing, walk
ACTIONS=(
    "Dead:dead"
    "Fly:fly"
    "Hit:hit"
    "Idle:idle"
    "Jump:jump"
    "Roll:roll"
    "Stuned:stuned"
    "Throwing:throwing"
    "Walk:walk"
)

TOTAL_FRAMES=0

echo "=== TVCartoon gen_pngseq: $MATERIAL C$CHAR_ID ==="
echo ""

for action_pair in "${ACTIONS[@]}"; do
    action="${action_pair%%:*}"
    lower="${action_pair##*:}"
    src_dir="$SRC/$action"

    if [ ! -d "$src_dir" ]; then
        echo "  SKIP $action: source dir not found at $src_dir"
        continue
    fi

    # Find all PNGs, sorted
    pngs=($(ls "$src_dir"/*.png 2>/dev/null | sort))
    count=${#pngs[@]}

    if [ "$count" -eq 0 ]; then
        echo "  SKIP $action: no PNG files found"
        continue
    fi

    echo "  $action ($lower): $count frames"

    for ((i=0; i<count; i++)); do
        src_png="${pngs[$i]}"
        frame_num=$(printf "%02d" "$i")
        out_name="pngseq_C${CHAR_ID}_${lower}_${frame_num}"

        # Resize 788×504 → 410×502, then convert to RGB565A8 C array
        magick "$src_png" -resize 410x502 \
            -background none -gravity center -extent 410x502 \
            /tmp/_pngseq_resized.png
        npx lv_img_conv \
            -f \
            -i "$out_name" \
            -c CF_RGB565A8 \
            -o "$OUT_DIR/${out_name}.c" \
            /tmp/_pngseq_resized.png 2>&1 | grep -v "^$" || true
        # Post-process: lv_img_conv v0.4.0 outputs LVGL v8, convert to v9
        sed -i '' \
            -e 's/LV_IMG_CF_RGB565A8/LV_COLOR_FORMAT_RGB565A8/g' \
            -e 's/LV_IMG_PX_SIZE_ALPHA_BYTE/3/g' \
            -e '/\.header\.always_zero = 0,/d' \
            -e 's/\.header\.reserved = 0/\.header\.reserved_2 = 0/g' \
            "$OUT_DIR/${out_name}.c"
    done

    TOTAL_FRAMES=$((TOTAL_FRAMES + count))
    echo "    → $count .c files written"
done

rm -f /tmp/_pngseq_resized.png

echo ""
echo "=== Done: $TOTAL_FRAMES frames → $OUT_DIR ==="
ls "$OUT_DIR"/*.c 2>/dev/null | wc -l | xargs echo "Total .c files:"

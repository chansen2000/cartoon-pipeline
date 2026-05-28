#!/bin/bash
# 单部件 dsc 自动化: Spine raw PNG → resize 到 410 视角 → lv_img_conv ARGB8888
# 部件清单从 cat_parts_meta.h 解析 (单一事实源, 跟 meta 永远同步)
#
# 用法: bash tools/gen_part_dscs.sh [material]
#   material 默认 "小猫"
set -e

MATERIALS_DIR="/Users/chansen2000/Downloads/素材/选择"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PIPELINE_DIR"

MATERIAL="${1:-小猫}"
SPINE_ROOT="$MATERIALS_DIR/$MATERIAL/Spine"
META_H="output/$MATERIAL/lvgl_export/meta/cat_parts_meta.h"
OUT_DIR="output/$MATERIAL/lvgl_export/dsc"

SCALE_W=410
SCALE_H=502
SRC_W=788
SRC_H=504
# scale = min(410/788, 502/504) ≈ 0.520305 — 跟 SpineAssembler.export_positions 一致

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/cat_C*.c

parts=$(grep 'LV_IMAGE_DECLARE' "$META_H" | sed -E 's/.*LV_IMAGE_DECLARE\((.+)\);.*/\1/')
total=$(echo "$parts" | wc -l | tr -d ' ')
echo "=== gen_part_dscs: $MATERIAL $total parts ==="

count=0
for var_name in $parts; do
    # cat_C01_Hand_B → C01 / Hand_B
    char_id=$(echo "$var_name" | sed -E 's/^cat_(C[0-9]+)_.*/\1/')
    part_safe=$(echo "$var_name" | sed -E 's/^cat_C[0-9]+_(.+)/\1/')
    # 还原文件名: meta 用 _ 替换空格, Spine 文件名可能用空格
    part_space=$(echo "$part_safe" | tr '_' ' ')
    src_png="$SPINE_ROOT/$char_id/${part_safe}.png"
    if [ ! -f "$src_png" ]; then
        src_png="$SPINE_ROOT/$char_id/${part_space}.png"
    fi

    if [ ! -f "$src_png" ]; then
        echo "  ❌ MISS: $var_name (tried $SPINE_ROOT/$char_id/${part_safe}.png)" >&2
        exit 1
    fi

    # 计算 scaled 尺寸 (跟 SpineAssembler.export_positions 的 round(orig * scale) 一致)
    read raw_w raw_h <<< $(magick identify -format "%w %h" "$src_png")
    scaled=$(python3 -c "
raw_w, raw_h = $raw_w, $raw_h
scale = min($SCALE_W/$SRC_W, $SCALE_H/$SRC_H)
print(round(raw_w*scale), round(raw_h*scale))
")
    read sw sh <<< "$scaled"

    tmp_png=$(mktemp -t dscresize.XXXXXX.png)
    magick "$src_png" -resize "${sw}x${sh}!" "$tmp_png"
    npx lv_img_conv -f -i "$var_name" -c CF_TRUE_COLOR_ALPHA \
        -o "$OUT_DIR/${var_name}.c" "$tmp_png" 2>&1 | grep -v "^$" || true
    # Post-process: lv_img_conv v0.4.0 outputs LVGL v8 format, convert to v9
    sed -i '' \
        -e 's/LV_IMG_CF_TRUE_COLOR_ALPHA/LV_COLOR_FORMAT_ARGB8888/g' \
        -e 's/LV_IMG_PX_SIZE_ALPHA_BYTE/4/g' \
        -e '/\.header\.always_zero = 0,/d' \
        -e 's/\.header\.reserved = 0/\.header\.reserved_2 = 0/g' \
        "$OUT_DIR/${var_name}.c"
    rm -f "$tmp_png"
    count=$((count + 1))
done

echo "=== Done: $count/$total dsc → $OUT_DIR ==="
ls "$OUT_DIR"/*.c 2>/dev/null | wc -l | tr -d ' ' | xargs -I{} echo "Total .c files: {}"

# Sonnet 任务书 — 单部件 dsc 自动化(流水线最后一块拼图)

> 状态: 待执行
> 起草: 4.7 (2026-05-28)
> 审核: sheng → 4.7 → kaifu(无)
> 预计时长: ≤ 2 小时

---

## 1. 背景

efe045e 之后,流水线契约在 **JSON / cat_parts_meta.{h,c}** 两层已自洽。
但**单部件 dsc**(`cat_C01_Hand_B.c` 等 131 个文件,ARGB8888)是 2026-05-27 commit `faa6e49` 一次性手工烘焙的,**没进 `build_assets.sh`**。

风险: 改 Spine 原图 / 改 410 目标尺寸 / 加新角色,JSON 和 meta 自动重生成,dsc 不动 → 立刻错位。

**目标: 把 dsc 烘焙挂进流水线,实现 "一键 `bash build_assets.sh` 全自动同步"。**

---

## 2. 契约(必须严格满足)

| 项目 | 要求 |
|------|------|
| 输入 | `/Users/chansen2000/Downloads/素材/选择/小猫/Spine/C{01..15}/<part>.png` |
| 输出 | `output/小猫/lvgl_export/dsc/cat_C{01..15}_<part>.c` |
| 部件清单 | **从 `output/小猫/lvgl_export/meta/cat_parts_meta.h` 解析 `LV_IMAGE_DECLARE(cat_Cxx_Yyy)`,逐项产出**(当前应为 131 个) |
| 缩放算法 | `scale = min(410/788, 502/504) ≈ 0.520305`,`round(raw_w * scale) × round(raw_h * scale)`(跟 `SpineAssembler.export_positions` 完全一致) |
| 颜色格式 | `LV_COLOR_FORMAT_ARGB8888`(跟当前 131 个 dsc 保持一致,**与 pngseq 的 RGB565A8 严格区分**) |
| 拷贝 | `build_assets.sh` 末尾把 `output/小猫/lvgl_export/dsc/*.c` 拷到 `<LVGL>/src/cartoon/assets/` |
| 工具 | 用 `npx lv_img_conv`(已有 `node_modules/lv_img_conv`),不允许自写编码 |
| 中间产物 | resize 后的临时 PNG 用完即删,不留垃圾 |

---

## 3. 实施步骤

### Step 1 — 新建 `tools/gen_part_dscs.sh`

```bash
#!/bin/bash
# 单部件 dsc 自动化:Spine raw PNG → resize 到 410 视角 → lv_img_conv ARGB8888
# 部件清单从 cat_parts_meta.h 解析(单一事实源)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PIPELINE_DIR"

SPINE_ROOT="/Users/chansen2000/Downloads/素材/选择/小猫/Spine"
META_H="output/小猫/lvgl_export/meta/cat_parts_meta.h"
OUT_DIR="output/小猫/lvgl_export/dsc"

# scale = min(410/788, 502/504) = 0.520305
# 用 ImageMagick 缩放整个 Spine 视角 (788x504),单部件随之缩 → 跟 SpineAssembler 一致
# 注意: lv_img_conv 不做 resize,先用 magick resize 到目标尺寸再 conv

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR"/cat_C*.c   # 全量重生成,不留旧文件

# 从 meta.h 提取 LV_IMAGE_DECLARE 列表
parts=$(grep 'LV_IMAGE_DECLARE' "$META_H" | sed -E 's/LV_IMAGE_DECLARE\((.+)\);/\1/')
total=$(echo "$parts" | wc -l | xargs)
echo "=== gen_part_dscs: $total parts ==="

count=0
for var_name in $parts; do
    # cat_C01_Hand_B  →  C01 / Hand_B
    char_id=$(echo "$var_name" | sed -E 's/^cat_(C[0-9]+)_.*/\1/')
    part_safe=$(echo "$var_name" | sed -E 's/^cat_C[0-9]+_(.+)/\1/')
    # 还原文件名:meta 用 _ 替换空格,Spine 文件名是空格(暂无,但保留)
    part_file=$(echo "$part_safe" | tr '_' ' ')
    src_png="$SPINE_ROOT/$char_id/${part_safe}.png"
    if [ ! -f "$src_png" ]; then
        # 兜底:试空格版本
        src_png="$SPINE_ROOT/$char_id/${part_file}.png"
    fi

    if [ ! -f "$src_png" ]; then
        echo "  ❌ MISS: $var_name (looked for $SPINE_ROOT/$char_id/${part_safe}.png)" >&2
        exit 1
    fi

    # raw 尺寸 → 用 python 算 scaled 尺寸,跟 SpineAssembler.export_positions 一致
    read raw_w raw_h <<< $(magick identify -format "%w %h" "$src_png")
    scaled=$(python3 -c "
raw_w, raw_h = $raw_w, $raw_h
scale = min(410/788, 502/504)
print(round(raw_w*scale), round(raw_h*scale))
")
    read sw sh <<< "$scaled"

    tmp_png=$(mktemp -t dscresize.XXXXXX.png)
    magick "$src_png" -resize "${sw}x${sh}!" "$tmp_png"
    npx lv_img_conv -f -i "$var_name" -c CF_TRUE_COLOR_ALPHA \
        -o "$OUT_DIR/${var_name}.c" "$tmp_png" 2>&1 | grep -v "^$" || true
    rm -f "$tmp_png"
    count=$((count + 1))
done

echo "=== Done: $count/$total dsc → $OUT_DIR ==="
ls "$OUT_DIR"/*.c | wc -l | xargs echo "Total .c files:"
```

**关键约束**:
- `magick -resize "${sw}x${sh}!"` — 末尾 `!` 强制目标尺寸,不保比(因为 sw/sh 已经按 scale 算好,允许 ±1px 跟 raw 比例的微小偏差,跟 SpineAssembler 的 round() 一致)
- 部件清单**只**从 `cat_parts_meta.h` 解析(单一事实源,跟 meta 永远同步)
- 出错立即 `exit 1`(找不到源 PNG = 流水线契约破裂,不允许 silent skip)

### Step 2 — 改 `build_assets.sh`

在 step 2 (gen_pngseq.sh) **之前**插入新 step:

```bash
# Step 2: 单部件 dsc (Spine raw → resize 到 410 视角 → ARGB8888 C 数组)
echo "[2/5] gen_part_dscs.sh ..."
bash tools/gen_part_dscs.sh
echo ""
```

并把原 step 2/3/4 编号顺延到 3/4/5,末尾增加拷贝:

```bash
# Step 5 增量: 拷贝单部件 dsc → LVGL 工程
echo "  cp dsc/*.c → $LVGL_ASSETS_DIR/"
cp -v output/小猫/lvgl_export/dsc/cat_C*.c "$LVGL_ASSETS_DIR/"
```

### Step 3 — 自检(必须通过才提交)

跑完 `bash build_assets.sh` 后:

1. **数量校验**: `ls output/小猫/lvgl_export/dsc/*.c | wc -l` = `grep LV_IMAGE_DECLARE output/小猫/lvgl_export/meta/cat_parts_meta.h | wc -l`
2. **尺寸校验** (sample 三个):
   - `cat_C01_Hand_B.c` dsc 头 `.w=40 .h=39`
   - `cat_C01_Tails.c` dsc 头 `.w=50 .h=31`
   - `cat_C01_Body.c` dsc 头 `.w` 跟 JSON `output/小猫/json/410_502/C01_default_positions.json` 的 Body.w 一致
3. **格式校验**: `grep -L 'LV_COLOR_FORMAT_ARGB8888' output/小猫/lvgl_export/dsc/*.c` 必须为空
4. **diff 兜底**: 跟当前 LVGL 工程的 `cat_C01_Hand_B.c` `cat_C01_Tails.c` `cat_C01_Body.c` `.w/.h` 字段对一遍,允许像素数据不同(lv_img_conv 版本/算法差异),但**尺寸字段必须完全一致**

把自检命令和输出贴到 commit message。

---

## 4. 红线

1. **不允许** silent skip 任何部件 — 找不到源 PNG = 立即 exit 1
2. **不允许** 自写 PNG/ARGB 编码 — 必须走 `npx lv_img_conv`
3. **不允许** 改 LVGL 工程任何文件 — 这是流水线侧任务,LVGL 端零改动
4. **不允许** 偏离 SpineAssembler 的 scale 算法(`min(tw/cw, th/ch)` + `round`)— scale 不一致 = 错位回归
5. **不允许** 偏离 `cat_parts_meta.h` 的部件清单 — meta 是单一事实源
6. **必须** 跟 efe045e 的提交风格一致(短而准的 commit message,带自检输出)
7. **commit + push 后**,在群里(或回复任务书)告知 4.7 commit hash 和 build_assets.sh 跑通的输出

---

## 5. 验收(4.7 端)

收到 Sonnet 完成回执后,4.7 会:

1. `cd /Users/chansen2000/Downloads/素材流水线 && bash build_assets.sh` — 跑通无错
2. 进 LVGL 工程 build,确认 `cat_C01_Hand_B.c` 等 dsc 尺寸字段没变(像素数据可能变,但 .w/.h/.cf 不变)
3. SDL 跑一遍,视觉确认 C01 还在原位(efe045e 视觉效果不退化)
4. 通过后归档 Phase D 流水线侧 → close

---

## 6. 不在本任务范围(明确排除)

- LVGL 工程内任何代码改动(`scene_forest.c` 键盘 bug 是 kaifu 的事)
- 新增 `validate_lvgl_consistency.py`(暂缓,等本任务跑稳再说)
- 改 SpineAssembler / config.py / gen_lvgl_meta.py(efe045e 已稳定,不动)
- 其他素材包(企鹅/小熊/小鸡 …)— 本任务只覆盖 "小猫"

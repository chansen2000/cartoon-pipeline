# TVCartoon 素材拼装 — 实现方案

## 总览

`素材/选择/` 下有两类素材：**角色** (Spine 骨骼动画) 和 **背景** (图层叠加)。

```
选择/
├── 小猫/ 小熊/ 企鹅/ 小兔/ 小鸡/ 熊猫/     ← 角色 (Spine)
└── 北极/ 森林/ 海底/ 海滩/ 太空/
    沙漠/ 石头/ 西部/ 大自然/               ← 背景 (图层)
```

**三条流水线**，按素材名分目录，统一输出到 `output/{素材名}/`。

| # | 流水线 | 输入 | 输出 |
|---|--------|------|------|
| 1 | 角色拼装 | Spine 骨骼 + 部件 PNG | 合成 PNG + 坐标 JSON |
| 2 | 背景叠加 | 图层 PNG | 合成 PNG + 图层 JSON |
| 3 | **LVGL Meta 导出** | 坐标 JSON × 15 | `cat_parts_meta.{h,c}` → LVGL `#include` |

## 目录结构

```
素材流水线/
├── assembler/
│   ├── __init__.py
│   ├── config.py                  # 路径、配饰表、分类常量
│   ├── spine_assembler.py         # 角色拼装引擎
│   └── background_assembler.py    # 背景叠加引擎
├── assemble_cli.py                # 角色 CLI
├── assemble_bg.py                 # 背景 CLI
├── verify_assembler.py            # 角色验证 (6项测试)
├── preview_anim.py                # Spine PNG 逐帧预览交互工具
├── build_assets.sh                # ★ 一键资产生成 + 拷贝到 LVGL 工程
├── tools/
│   └── gen_lvgl_meta.py           # ★ 读 15 份 JSON → 产出 cat_parts_meta.{h,c}
├── IMPLEMENTATION.md              # 本文件
├── USAGE.md                       # 使用说明 (面向 kaifu)
├── BACKGROUND_PLAN.md             # 背景方案讨论稿
└── output/
    └── {素材名}/
        ├── picture/
        │   ├── 788_504/           # 角色: C01~C15_default.png
        │   ├── 410_502/           # P4 缩放
        │   └── 1920_1080/         # 背景: variant_*.png
        ├── json/
        │   └── {W}_{H}/           # 对应分辨率的坐标 JSON
        └── lvgl_export/           # ★ LVGL 工程消费的 C 产物统一出口
            └── meta/
                ├── cat_parts_meta.h   # part_meta_t 类型 + LV_IMAGE_DECLARE × 146
                └── cat_parts_meta.c   # 15 角色数组 + cat_parts_find / cat_full_find
```

---

# 一、角色流水线 (SpineAssembler)

## 核心算法

### 1. 骨骼矩阵链

Spine 骨骼是树状层级，每骨骼存 local transform (x, y, rotation, scaleX, scaleY) + parent。递归计算 world transform：

```
local = [cos(rot)*sx, -sin(rot)*sy, x]
        [sin(rot)*sx,  cos(rot)*sy, y]

child_world = parent_world × child_local
```

21 个骨骼全部递归收敛，缓存于 `bone_worlds`。

### 2. 附件世界坐标

```
world_x = bone.a * att_x + bone.b * att_y + bone.worldX
world_y = bone.c * att_x + bone.d * att_y + bone.worldY
```

### 3. 世界 → 画布 (Y 轴翻转)

```
canvas_x = world_x - skeleton.x
canvas_y = (skeleton.y + skeleton.height) - world_y
```

skeleton: `width=788, height=504, x=-416.54, y=-58.44`。

## Skin 系统

| 机制 | 说明 |
|------|------|
| Skin name | `Character01` ~ `Character15` → `C01` ~ `C15` |
| Attachment key | **全部以 `C01/` 为前缀** (如 `C01/Body`)，不管哪个 Skin |
| PNG 文件 | 按角色分目录 `Spine/C01/Body.png`、`Spine/C02/Body.png` |
| 配饰表 | config.py `CHAR_ACCESSORIES`，默认值 + CLI 覆盖 |

**关键陷阱**：Skin dict key 是 `"C01/Body"`，`_resolve_attachments()` 改写为 `"C02/Body"` (用于文件查找)。查位置数据时必须 fallback 到 C01 前缀。修复：精确匹配 → `C01/partname` → 裸名。

## 角色配饰表

```
C01: hat+glasses           C06: hat           C11: (裸)
C02: hat                   C07: cloth         C12: (裸)
C03: hat+cloth             C08: glasses       C13: (裸)
C04: cloth                 C09: (裸)          C14: glasses
C05: (裸)                  C10: (裸)          C15: hat
```

## 输出 JSON (角色)

```json
{
  "character": "C01",
  "canvas": {"w": 410, "h": 502},
  "parts_count": 10,
  "parts": [{
    "name": "Body",      "file": "C01/Body.png",
    "x": 168, "y": 233,  "w": 96,  "h": 111,
    "pivot_x": 48,        "pivot_y": 55,
    "rotation": 0.0,      "z_order": 7,
    "category": "core",   "clickable": true,
    "click_anim": "bounce"
  }]
}
```

部件分类: core (9) / accessory (Hat/Glasses/Cloth) / prop (Hammer/Umbrella) / effect (Confuse Fx/Star/Splash/Box)

动画类型: bounce → 上下弹跳, spin → 旋转, wag → 摇摆, null → 不可点击


# 二、背景流水线 (BackgroundAssembler)

## 素材结构

9 个背景主题，每个 4 变体，全部 1920×1080。两种目录模式：

**类型 A — layers/ 子目录** (北极/大自然/海底/海滩/森林/太空)
```
北极/_PNG/01/layers/
  l1-background.png         # z=0 底层
  l2-mountains01.png        # z=1
  ...
  l10-block.png             # z=9 顶层
```

**类型 B — 平铺编号** (沙漠/石头/西部)
```
沙漠/_PNG/1/
  background.png            # z=0 底层
  1.png                     # z=1
  ...
  6.png                     # z=6 顶层
```

命名规范不统一：`_PNG` vs `PNG`、`_AI` vs `AI`。`BackgroundAssembler._find_dir()` 自动探测。

## 核心算法

极简 —— 从底到顶 paste 图层：

```python
def composite(self, variant_name, size=None):
    canvas = Image.new("RGBA", size or (1920, 1080), (0,0,0,0))
    for layer in sorted_layers:        # z-order 升序
        img = Image.open(layer.path).convert("RGBA")
        canvas.paste(img, (0,0), img)  # 所有图层左上角对齐
    return canvas, layer_meta
```

## 图层排序

`_sort_key_natural()`: 从文件名提取首个数字 → `l1 < l2 < l10` (非字符串序)。

## 视差比

```
parallax_ratio = z / (total - 1)    # z=0→0.0, z=max→1.0
```

| ratio | 含义 | LVGL |
|-------|------|------|
| 0.0 | 不动 (远景天空) | camera_x * 0 |
| 0.5 | 半速 (中景山) | camera_x * 0.5 |
| 1.0 | 全速跟镜头 (前景遮挡) | camera_x * 1.0 |

## 输出 JSON (背景)

```json
{
  "material": "北极",
  "variant": "01",
  "canvas": {"w": 410, "h": 502},
  "source_size": {"w": 1920, "h": 1080},
  "layer_count": 10,
  "layers": [{
    "name": "l1-background",
    "z_order": 0,
    "parallax_ratio": 0.0,
    "w": 1920, "h": 1080,
    "x": 0, "y": 0
  }]
}
```

所有图层左上角对齐 (x=0, y=0)，缩放时保持比例居中。


# 三、LVGL Meta 导出 (gen_lvgl_meta.py)

## 设计动机

流水线是唯一生产者，LVGL 是纯粹消费者。Kaifu 的 C 代码不应重新解析 JSON、不应硬编码部件坐标。因此流水线侧多跑一步 codegen：读 15 份 `Cxx_default_positions.json` → 产出 `cat_parts_meta.{h,c}`，LVGL 工程直接 `#include`。

```
JSON (真值源)          gen_lvgl_meta.py         LVGL 工程
─────────────          ────────────────         ─────────
C01_default_positions.json ─┐
C02_default_positions.json  │  解析 → C 结构     cat_parts_meta.h
   ...                       ├────────────────→  cat_parts_meta.c
C15_default_positions.json ─┘                    (CMake GLOB 自动收纳)
```

## 输入

`output/小猫/json/410_502/Cxx_default_positions.json` × 15

## 输出

`output/小猫/lvgl_export/meta/cat_parts_meta.{h,c}`

## 产出物结构

```c
// cat_parts_meta.h

typedef struct {
    const char *name;            // "Eye1" / "Hand_F" / "Tails"
    int16_t  x, y, w, h;         // 410×502 画布坐标
    int16_t  pivot_x, pivot_y;   // 旋转轴心 (部件局部)
    int16_t  rotation_01;        // 0.1° 单位 (JSON rotation × 10 取整)
    uint8_t  z_order;            // Spine slot 顺序
    const lv_image_dsc_t *img;   // &cat_Cxx_<part> (编译期绑定)
    part_anim_type_t anim_type;  // PART_ANIM_NONE / SPIN / WAG / BOUNCE
} part_meta_t;

// 查表函数
const lv_image_dsc_t *cat_full_find(const char *char_id);
const part_meta_t    *cat_parts_find(const char *char_id, const char *part_name);
```

## 字段映射

| JSON 字段 | part_meta_t | 转换 |
|-----------|-------------|------|
| `name` | `name` | 原样字符串 |
| `x, y, w, h` | 同名 | int16_t |
| `pivot_x, pivot_y` | 同名 | int16_t |
| `rotation` (float, 度) | `rotation_01` | `round(rotation × 10)`, int16_t |
| `z_order` | 同名 | uint8_t |
| `file` (`"C01/Hand_F.png"`) | `img` | `&cat_C01_Hand_F` |
| `click_anim` | `anim_type` | `"wag"→PART_ANIM_WAG`, `"bounce"→PART_ANIM_BOUNCE`, `"spin"→PART_ANIM_SPIN`, null→`PART_ANIM_NONE` |

## 关键决策

- **包含全部部件** (不只是 `click_anim != null` 的)，给未来扩展留余地
- **不塞占位项** — 某角色 JSON 没有 Hat (如 C04)，`cat_parts_find("C04", "Hat")` 返回 NULL
- **Img 指针编译期绑定** — 变量名 `cat_<char>_<part_name>` 与 LVGL 现有 131 个资产 C 数组一致
- **LV_IMAGE_DECLARE 列全** — 146 个 (15 整图 + 131 部件)，`cat_assets.h` 将被 `cat_parts_meta.h` 取代

## 一键构建

```bash
bash build_assets.sh
```

1. 调 `python3 tools/gen_lvgl_meta.py` 生成 meta 文件
2. `cp` → LVGL 工程 `src/cartoon/assets/`

LVGL 工程 CMake 已 `file(GLOB ... cat_*.c)`，新文件自动收纳。LVGL 侧零文件修改。

## 命名规则 (三处严格一致)

| 项 | 模板 | 示例 |
|----|------|------|
| 角色 ID | `Cxx` | `C01` |
| 整图 C 变量 | `cat_full_<char>` | `cat_full_C01` |
| 部件 C 变量 | `cat_<char>_<part_name>` | `cat_C01_Hand_F` |
| 部件数组 | `cat_parts_<char>[]` | `cat_parts_C01[]` |
| 数组计数 | `cat_parts_<char>_count` | `cat_parts_C01_count` |
| 部件名空格处理 | 空格 → 下划线 | `"Eye 1"` → `Eye_1` |


# 四、三条流水线对比

| | 角色 (SpineAssembler) | 背景 (BackgroundAssembler) | LVGL Meta (gen_lvgl_meta) |
|---|---|---|---|
| 输入 | `Characters.json` + `Spine/` 分部件 PNG | `layers/` 或平铺 PNG | 角色 JSON × 15 |
| 核心算法 | 骨骼矩阵链 + 附件定位 + Y轴翻转 | 图层叠加 (左上角对齐) | JSON → C struct 字段映射 |
| 部件/图层数 | 8~10 per 角色 | 3~10 per 变体 | 全部 parts, 不筛选 |
| 变体数 | 15 角色 × 配饰组合 | 4 场景 | 15 角色 |
| 坐标 | 每部件独立 (x, y, pivot, rotation) | 全图层同原点 (x=0, y=0) | 从 JSON 直接搬运, 不重新计算 |
| 动画 | 部件独立旋转/平移/缩放 | 整层水平视差滚动 | part_meta_t 提供 anim_type, LVGL 端执行 |
| CLI | `assemble_cli.py --char C01` | `assemble_bg.py --material 北极` | `python3 tools/gen_lvgl_meta.py` |
| 产物 | 合成 PNG + 坐标 JSON | 合成 PNG + 图层 JSON | `cat_parts_meta.{h,c}` |


# 五、踩坑记录

1. **Skin attachment key 陷阱** — Skin dict key 全以 `C01/` 为前缀，`_resolve_attachments` 替换为 `C02/Body` 后查不到。修复: 精确匹配 → `C01/partname` → 裸名 fallback。

2. **Spine Y 轴翻转** — `canvas_y = (skeleton.y + skeleton.height) - world_y`，漏掉则上下颠倒。

3. **PIL rotate expand** — `expand=True` 后图片变大，paste 位置需相对新尺寸重算。

4. **图层字符串排序** — `l1 < l10 < l2` (ASCII序) 错误。修复: `_sort_key_natural()` 提取数字后按数值排序。

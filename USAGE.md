# 素材拼装输出 — 使用说明

## 文件位置

```
素材流水线/output/
└── {素材名}/                  # 对应 选择/ 下的目录名
    ├── picture/
    │   ├── 788_504/           # 角色: C01~C15_default.png
    │   ├── 410_502/           # P4 缩放
    │   └── 1920_1080/         # 背景: variant_*.png
    ├── json/
    │   └── {W}_{H}/
    └── lvgl_export/           # ★ LVGL 工程直接消费的 C 产物
        └── meta/
            ├── cat_parts_meta.h
            └── cat_parts_meta.c
```

角色图片: `C01_default.png ~ C15_default.png`，对应 JSON: `C01_default_positions.json`
背景图片: `variant_01.png ~ variant_04.png`，对应 JSON: `variant_01_layers.json`

**一键生成并部署到 LVGL 工程:**
```bash
bash build_assets.sh
```

---

# 一、角色

## JSON 格式

```json
{
  "character": "C01",
  "canvas": {"w": 410, "h": 502},
  "parts_count": 10,
  "parts": [{
    "name": "Body",       "file": "C01/Body.png",
    "x": 168, "y": 233,   "w": 96,  "h": 111,
    "pivot_x": 48,         "pivot_y": 55,
    "rotation": 0.0,       "z_order": 7,
    "category": "core",    "clickable": true,
    "click_anim": "bounce"
  }]
}
```

### 字段说明

| 字段 | 类型 | 含义 |
|------|------|------|
| `name` | string | 部件名 (Body, Hat, Eye1, Tails...) |
| `file` | string | 源文件路径 |
| `x`, `y` | int | 部件图片**左上角**在目标画布上的坐标 |
| `w`, `h` | int | 缩放后宽高 |
| `pivot_x`, `pivot_y` | int | 部件中心点 (旋转轴心) = w/2, h/2 |
| `rotation` | float | 初始旋转角度 (度) |
| `z_order` | int | 渲染层级，0=底层，越大越靠前 |
| `category` | string | core / accessory / prop / effect |
| `clickable` | bool | 是否可点击 |
| `click_anim` | string | bounce / spin / wag / null |

### 动画类型

| click_anim | 效果 | LVGL 实现 |
|-----------|------|-----------|
| bounce | 上下弹跳 | `lv_anim` 改 y，±20px 来回 |
| spin | 旋转一圈 | `lv_anim` rotation 0→360° |
| wag | 左右摇摆 | `lv_anim` rotation ±15° 来回 3 次 |
| null | 不响应点击 | — |

## LVGL 集成

### 1. 创建部件

```c
cJSON *root = cJSON_Parse(json_str);
cJSON *parts = cJSON_GetObjectItem(root, "parts");
int canvas_w = cJSON_GetObjectItem(root, "canvas")->valueint;

cJSON *part;
cJSON_ArrayForEach(part, parts) {
    const char *name = cJSON_GetObjectItem(part, "name")->valuestring;
    int x  = cJSON_GetObjectItem(part, "x")->valueint;
    int y  = cJSON_GetObjectItem(part, "y")->valueint;
    int rot = cJSON_GetObjectItem(part, "rotation")->valuedouble;

    lv_obj_t *img = lv_image_create(parent);
    lv_image_set_src(img, get_image_by_name(name));
    lv_obj_set_pos(img, x, y);
    lv_image_set_rotation(img, (int)(rot * 10));  // LVGL 0.1°

    if (cJSON_GetObjectItem(part, "clickable")->valueint) {
        lv_obj_add_flag(img, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(img, on_part_click, LV_EVENT_CLICKED, NULL);
    }
}
```

### 2. 点击动画

```c
// bounce — 上下弹跳
lv_anim_t a;
lv_anim_init(&a);
lv_anim_set_var(&a, part);
lv_anim_set_exec_cb(&a, anim_bounce_cb);  // 改 lv_obj_set_y
lv_anim_set_values(&a, 0, -20);
lv_anim_set_duration(&a, 150);
lv_anim_set_playback_time(&a, 150);
lv_anim_start(&a);

// spin — 旋转
lv_anim_set_exec_cb(&a, lv_image_set_rotation);
lv_anim_set_values(&a, 0, 3600);  // LVGL 0.1° = 360°
lv_anim_set_duration(&a, 500);
lv_anim_start(&a);

// wag — 摇摆 ±15°
lv_anim_set_exec_cb(&a, lv_image_set_rotation);
lv_anim_set_values(&a, -150, 150);
lv_anim_set_duration(&a, 200);
lv_anim_set_repeat_count(&a, 2);
lv_anim_set_playback_time(&a, 200);
lv_anim_start(&a);
```

### 3. 两阶段渲染 (省内存)

- **静态层** — 整张 `C01_default.png` 做背景
- **动画层** — 被点击的部件单独创建 `lv_image` 覆盖在上层
- 动画结束删除动画层，回到静态

这样只有动画中的部件才需要单独加载。

### 4. 渲染层级

按 `z_order` **升序**创建即可 (LVGL 后创建在上层)：

```
z=0  Shadow     (最先创建，底层)
z=4  Hand_B
z=5  Tails
z=7  Body
z=11 Eye1
z=13 Hand_F     (最后创建，顶层)
```

部件图片源路径: `素材/选择/小猫/Spine/C01/Body.png` 等。用 LVGLImage.py 转 C 数组。

---

# 二、背景

## JSON 格式

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

### 字段说明

| 字段 | 类型 | 含义 |
|------|------|------|
| `material` | string | 主题名 |
| `variant` | string | 变体名 |
| `source_size` | object | 原始尺寸 (1920×1080) |
| `layers[].name` | string | 图层名 |
| `layers[].z_order` | int | 渲染层级，0=最底层 |
| `layers[].parallax_ratio` | float | 视差滚动比 (0.0=不动, 1.0=全速) |
| `layers[].w`, `h` | int | 图层尺寸 |
| `layers[].x`, `y` | int | 图层左上角坐标 (始终 0,0) |

背景图层全部左上角对齐，缩放时居中显示。

## LVGL 集成

### 1. 创建图层

```c
cJSON *root = cJSON_Parse(json_str);
cJSON *layers = cJSON_GetObjectItem(root, "layers");

// 按 z_order 升序创建
cJSON *layer;
cJSON_ArrayForEach(layer, layers) {
    const char *name = cJSON_GetObjectItem(layer, "name")->valuestring;
    int z = cJSON_GetObjectItem(layer, "z_order")->valueint;
    float ratio = cJSON_GetObjectItem(layer, "parallax_ratio")->valuedouble;

    lv_obj_t *img = lv_image_create(bg_parent);
    lv_image_set_src(img, get_bg_layer(name));
    // 存储 parallax_ratio 用于后续滚动
    lv_obj_set_user_data(img, (void*)(intptr_t)(ratio * 1000));
}
```

### 2. 视差滚动

```c
void parallax_update(int16_t camera_x) {
    for (int i = 0; i < layer_count; i++) {
        float ratio = (float)(intptr_t)lv_obj_get_user_data(layer_objs[i]) / 1000.0f;
        int16_t layer_x = -(int16_t)(camera_x * ratio);
        lv_obj_set_x(layer_objs[i], layer_x);
    }
}
// ratio=0.0 → 远景不动
// ratio=1.0 → 前景全速跟随
```

### 3. 图层动画

每层独立 `lv_image`，可以单独做动画：

```c
// 云漂移 — 修改 x 坐标
lv_anim_t a;
lv_anim_init(&a);
lv_anim_set_var(&a, cloud_layer);
lv_anim_set_exec_cb(&a, lv_obj_set_x);
lv_anim_set_values(&a, 0, -100);
lv_anim_set_duration(&a, 5000);
lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE);
lv_anim_start(&a);
```

---

# 三、CLI 命令

## 角色

```bash
# 默认素材 (小猫)
python3 assemble_cli.py --all                              # 788×504
python3 assemble_cli.py --all --target 410x502 --export-lvgl  # P4 + JSON

# 切换素材
python3 assemble_cli.py --material 小熊 --all

# 单个角色变体
python3 assemble_cli.py --char C01 --no-glasses
python3 assemble_cli.py --char C03 --hammer

# 新分辨率
python3 assemble_cli.py --all --target 1024x768 --export-lvgl
```

## 背景

```bash
# 全部 9 个主题
python3 assemble_bg.py --all-materials

# 单个主题
python3 assemble_bg.py --material 北极 --all
python3 assemble_bg.py --material 森林 --variant 01

# P4 缩放 + JSON
python3 assemble_bg.py --material 北极 --all --target 410x502 --export-lvgl

# 列出变体
python3 assemble_bg.py --material 海底 --list
```

---

# 四、LVGL Meta 导出 (part_meta_t)

## 用途

流水线 JSON → C 结构体 `part_meta_t`，LVGL 工程直接 `#include "cat_parts_meta.h"` 使用。**LVGL 端不解析 JSON，不硬编码坐标**。

## 一键构建

```bash
bash build_assets.sh
```

内部两步：
1. `python3 tools/gen_lvgl_meta.py` → `output/小猫/lvgl_export/meta/cat_parts_meta.{h,c}`
2. `cp` → LVGL 工程 `src/cartoon/assets/`

## part_meta_t 结构

```c
typedef struct {
    const char *name;            // "Eye1" / "Hand_F" / "Tails" / "Hat" / "Body" / ...
    int16_t  x, y, w, h;         // 410×502 设计画布坐标
    int16_t  pivot_x, pivot_y;   // 旋转轴心 (部件局部坐标系)
    int16_t  rotation_01;        // 0.1° 单位 (JSON rotation × 10 取整)
    uint8_t  z_order;            // Spine slot 顺序
    const lv_image_dsc_t *img;   // &cat_Cxx_<part> (编译期已绑定)
    part_anim_type_t anim_type;  // PART_ANIM_NONE / SPIN / WAG / BOUNCE
} part_meta_t;
```

## 查表 API

```c
// 按角色 ID 取整图
const lv_image_dsc_t *cat_full_find(const char *char_id);
// 例: cat_full_find("C03") → &cat_full_C03

// 按角色 + 部件名取 part_meta_t
const part_meta_t *cat_parts_find(const char *char_id, const char *part_name);
// 例: cat_parts_find("C01", "Eye1") → 返回 Eye1 条目
//     cat_parts_find("C04", "Hat")  → NULL (C04 无 Hat, 不塞占位项)
```

## 命名规则

| 项 | 模板 | 示例 |
|----|------|------|
| 整图 C 变量 | `cat_full_<char>` | `cat_full_C01` |
| 部件 C 变量 | `cat_<char>_<part_name>` | `cat_C01_Hand_F` |
| 部件数组 | `cat_parts_<char>[]` | `cat_parts_C01[]` |
| 数组计数 | `cat_parts_<char>_count` | `cat_parts_C01_count` |
| 部件名空格处理 | 空格 → 下划线 | `"Eye 1"` → `Eye_1` |

## 包含范围

- **全部部件**，不只是 `click_anim != null` 的。含 Shadow / Leg_B / Leg_F / Glasses / Hand_B / Hand_F 等
- **不塞占位项**。某角色 JSON 没有 Hat（如 C04），`cat_parts_find("C04", "Hat")` 返回 NULL
- 15 角色总计 131 个部件 + 15 张整图 = 146 个 `LV_IMAGE_DECLARE`

## 字段映射 (JSON → part_meta_t)

| JSON 字段 | part_meta_t | 转换 |
|-----------|-------------|------|
| `name` | `name` | 原样字符串 |
| `x, y, w, h` | 同名 | int16_t |
| `pivot_x, pivot_y` | 同名 | int16_t |
| `rotation` (float, 度) | `rotation_01` | `round(rotation × 10)`, int16_t |
| `z_order` | 同名 | uint8_t |
| `file` (`"C01/Hand_F.png"`) | `img` | 从 file 路径提取部件名 → `&cat_<char>_<part>` |
| `click_anim` | `anim_type` | `"wag"→PART_ANIM_WAG`, `"bounce"→PART_ANIM_BOUNCE`, `"spin"→PART_ANIM_SPIN`, `null→PART_ANIM_NONE` |

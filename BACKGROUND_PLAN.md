# 背景拼装方案

## 素材现状

`选择/` 下有 9 个背景主题，每个 4 种场景变体。全部 1920×1080，有 AI 矢量源。

### 两种目录结构

**类型 A — layers/ 子目录命名图层** (6个: 北极/大自然/海底/海滩/森林/太空)
```
北极/_PNG/01/layers/
  l1-background.png         # 最底层 (RGB, 不透明底)
  l2-mountains01.png        # RGBA 透明叠加
  ...
  l10-block.png             # 最顶层
```
图层数 5~10 不等，文件名前缀 `l1_` ~ `lN_` 决定 z-order。

**类型 B — 平铺编号文件** (3个: 沙漠/石头/西部)
```
沙漠/_PNG/1/
  background.png            # 最底层 (RGB)
  1.png                     # RGBA → z=1
  2.png                     # RGBA → z=2
  ...
  6.png                     # RGBA → z=6 (顶层)
```
文件名 `1.png ~ N.png` 决定 z-order，`background.png` 固定是底。

### 命名规范不统一

| 主题 | PNG 目录 | AI 目录 | EPS 目录 | TXT 目录 |
|------|---------|---------|---------|---------|
| 北极/大自然/森林/沙漠/石头/西部 | `_PNG` | `_AI` | `_EPS` | `_TXT` |
| 海底/海滩/太空 | `PNG` | `AI` | `EPS` | `TXT` |

`BackgroundAssembler` 初始化时自动探测（先试 `_PNG` 再试 `PNG`），对 CLI 透明。

## 方案设计

### 1. 引擎：`assembler/background_assembler.py`

```
BackgroundAssembler
├── __init__(material_name)     # 探测目录结构，收集4个变体的图层列表
├── composite(variant, size)    # 叠图层 → PIL.Image + 图层元数据
├── export_layers(meta, w, h)   # 导出 LVGL 图层 JSON
├── scale_to_target(img, w, h)  # 缩放到目标分辨率
└── list_variants()             # 返回该主题的变体名列表
```

比 SpineAssembler 简单很多——没有骨骼矩阵、没有附件定位、没有配饰开关。核心逻辑就一个 `composite()`：

```python
def composite(self, variant, size=None):
    """从底到顶叠加图层"""
    canvas = Image.new("RGBA", size or (1920, 1080), (0,0,0,0))
    layer_meta = []
    for layer in self._layers[variant]:  # 已按 z-order 排序
        img = Image.open(layer["path"]).convert("RGBA")
        canvas.paste(img, (0, 0), img)
        layer_meta.append({
            "name": layer["name"],
            "file": layer["path"],
            "z_order": layer["z"],
            "w": img.width, "h": img.height,
        })
    return canvas, layer_meta
```

### 2. 图层排序规则

```
z=0: background.png 或 l1_*.png          (底层底图, RGB)
z=1: 1.png 或 l2_*.png                    (远景/天空)
z=2: 2.png 或 l3_*.png                    (中景/山/云)
...
z=N: 顶层 (前景/地面/遮挡物)
```

实现：
- **layers/ 型**: `ls layers/ | sort` — 文件名 `l1_` < `l2_` < ... → 自然排序
- **平铺型**: `background.png` → z=0, `1.png` → z=1, `2.png` → z=2...

### 3. 视差滚动比 (parallax_ratio)

每层一个 0.0~1.0 的系数，表示该层跟随镜头移动的速度比例：

```
z=0 (最远层): ratio=0.0   → 不动 (天空/远景)
z=N (最近层): ratio=1.0   → 全速跟随 (前景遮挡物)
中间层:      ratio = z / max_z  (线性插值)
```

或者按图层语义手动标注（云层偏慢 0.2~0.3，地面偏快 0.8~1.0）。初版用**线性插值**，后续可调。

### 4. 输出结构

```
output/{背景名}/
├── picture/
│   ├── 1920_1080/              # 原始分辨率，4 张复合 PNG
│   │   ├── variant_01.png
│   │   ├── variant_02.png
│   │   ├── variant_03.png
│   │   └── variant_04.png
│   └── 410_502/                # P4 缩放
│       └── variant_*.png
└── json/
    ├── 1920_1080/
    │   ├── variant_01_layers.json
    │   └── ...
    └── 410_502/
        └── ...
```

### 5. JSON 格式

```json
{
  "material": "北极",
  "variant": "01",
  "canvas": {"w": 410, "h": 502},
  "source_size": {"w": 1920, "h": 1080},
  "layers": [
    {
      "name": "background",
      "z_order": 0,
      "parallax_ratio": 0.0,
      "w": 410, "h": 231,
      "x": 0, "y": 271
    },
    {
      "name": "mountains01",
      "z_order": 1,
      "parallax_ratio": 0.11,
      "w": 410, "h": 286,
      "x": 0, "y": 167
    },
    {
      "name": "ground",
      "z_order": 8,
      "parallax_ratio": 0.89,
      "w": 410, "h": 98,
      "x": 0, "y": 404
    }
  ]
}
```

注意：背景图层铺满画布宽度，缩放后可能比 P4 窄屏宽，需记录 `x, y` 偏移（水平居中时的 left offset）。或者 LVGL 端直接 `lv_image_set_scale` 全屏拉伸。

### 6. CLI 接口

```bash
# 列出某个主题的变体
python3 assemble_bg.py --material 北极 --list

# 单变体
python3 assemble_bg.py --material 北极 --variant 01

# 全部 4 变体
python3 assemble_bg.py --material 北极 --all

# 指定分辨率
python3 assemble_bg.py --material 北极 --all --target 410x502 --export-lvgl

# 批量所有背景主题
python3 assemble_bg.py --all-materials --target 410x502
```

### 7. 关键差异：背景 vs 角色

| | 角色 (SpineAssembler) | 背景 (BackgroundAssembler) |
|---|---|---|
| 输入源 | `Characters.json` + Spine/ 分部件 | `layers/` 目录 + 图层 PNG |
| 核心算法 | 骨骼矩阵链 + 附件世界坐标 | 图层叠加 (paste from bottom to top) |
| 部件数 | 8~10 per 角色 | 3~10 per 变体 |
| 变体 | 15 角色 × 配饰组合 | 4 场景 × 固定图层 |
| 坐标系统 | Spine world → canvas (Y轴翻转) | 原点对齐 (所有图层左上角 0,0) |
| 动画方式 | 部件独立旋转/平移/缩放 | 整层水平滚动 (视差) |
| 矢量源 | AI 24页/角色 (每部件1页) | AI 1页/变体 (可能有 tileset) |
| 位置数据 | 每个部件的 canvas_x/y/rotation | 每个图层的 z_order + parallax_ratio |

### 8. 命名规范适配

`_PNG` vs `PNG` 不一致，在 `BackgroundAssembler` 里统一处理：

```python
def _find_dir(self, *candidates):
    for name in candidates:
        path = os.path.join(self.material_dir, name)
        if os.path.isdir(path):
            return path
    raise FileNotFoundError(f"None of {candidates} found in {self.material_dir}")

# 使用
png_dir = self._find_dir("_PNG", "PNG")
ai_dir = self._find_dir("_AI", "AI")
```

### 9. 视差滚动在 LVGL 中的实现

```c
// 每层一个 lv_image，按 parallax_ratio 移动 x 坐标
void parallax_scroll(int16_t camera_x) {
    for (int i = 0; i < layer_count; i++) {
        int16_t layer_x = - (camera_x * layers[i].parallax_ratio);
        lv_obj_set_x(layer_objs[i], layer_x);
    }
    // 最底层 ratio=0 → 不动
    // 最顶层 ratio=1.0 → 全速跟随
}
```

## 实施顺序

1. `assembler/background_assembler.py` — ~120 行
2. `assemble_bg.py` — CLI 入口
3. 验证：北极 4 变体 × 2 分辨率
4. 批量：9 主题全部生成

开始前先确认：方案和接口设计有没有需要调整的？

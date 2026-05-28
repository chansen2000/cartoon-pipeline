# 素材流水线 — 文件清单与契约

> 维护: 4.7 (2026-05-28)
> 用途: sheng review / Sonnet 执行边界 / kaifu 消费契约
> 状态: ✅ 流水线契约定义完整,标注 3 处架构越界待清理
> 范围: **全局多素材包**(6 角色 + 9 背景),小猫只是首个落地实验

---

## 0. 流水线契约(顶层)

**一句话**: 流水线把**所有素材包**(角色 + 背景)在 410 视角下的资源准备好,LVGL 端只消费,不计算。

**素材包覆盖范围**:

| 类型 | 素材包 | 当前实现 | 目标 |
|------|--------|----------|------|
| 角色(Spine) | 小猫 / 小熊 / 企鹅 / 小兔 / 小鸡 / 熊猫 | 仅小猫 | 全 6 包 |
| 背景(图层) | 北极 / 大自然 / 海底 / 海滩 / 森林 / 沙漠 / 石头 / 太空 / 西部 | 引擎已通用,未烘 LVGL 资产 | 全 9 包 |

**资源层 vs 应用层 — 职责分界**:

| 维度 | 资源层(流水线管) | 应用层(流水线 INI 管) |
|------|------------------|------------------------|
| 数据来源 | Spine 几何 / 背景图层尺寸 | 产品意图(谁会动/怎么动/什么时候动/视差比例) |
| 是否随素材改变 | 是 | 部分(action 帧数跟 pngseq 强绑定;艺术约束跟素材绑定) |
| 修改触发的回归 | 重跑 build_assets.sh | 改 INI 后重跑 build_assets.sh(校验 + 拷贝) |
| 例子 | x/y/w/h/pivot/rotation/z_order/parallax_ratio | 是否可点击 / 点击播什么动画 / idle 候选 / 背景摆动幅度 |

**红线**: 资源层不允许出现 `clickable` / `click_anim` / `anim_type` / `CLICK_ANIM_MAP` 这类应用决策字段。

**两层契约的"家"**(都在流水线):

| 层 | 契约文件(源头) | 维护人 | 同步去向 | 消费方 |
|----|----------------|--------|----------|--------|
| 资源层 — 角色 | `output/{素材}/json/410_502/*_positions.json` + `cat_parts_meta.{h,c}` + `cat_C*.c` × N + `pngseq_*.c` × M | Sonnet | build_assets.sh cp → `lv_port_pc_vscode/src/cartoon/assets/` | LVGL runtime |
| 资源层 — 背景 | `output/{背景}/json/410_502/variant_*_layers.json` + `bg_*.c`(图层 RGB565)+ 元数据 C 文件 | Sonnet | build_assets.sh cp → `lv_port_pc_vscode/src/cartoon/assets/bg/` | LVGL runtime |
| 应用层 | `config/{素材}/animation_config.ini`(每个素材包一份) | Sonnet | build_assets.sh cp → `lv_port_pc_vscode/src/cartoon/config/` | LVGL runtime |

**关键原则**: LVGL 工程零维护契约。所有 INI / 资产 C 文件都是 build 产物,kaifu 不该手编辑。

**应用层契约的内容**(animation_config.ini,每个素材包一份):
- `[global]` — `default_skin` / 内存日志阈值
- `[idle_script]` — `enable` / `parts=eye,tail,hat` / `gap_ms` / `shuffle`(idle 候选清单)
- `[part.eye] / [part.tail] / [part.hat]` — 每类部件的 `enable` / `anim_type` / `duration_ms` / `amplitude`
- `[action.idle / walk / jump / fly / hit / roll / dead / stuned / throwing]` — `frame_count` / `fps` / `loop` / `asset_prefix`(**frame_count 必须跟 pngseq 产出帧数一致**)
- `[bg.{layer_name}]` — 背景每图层的 `parallax_ratio_override` / `sway_enable` / `sway_amplitude` / `sway_duration_ms`(背景动画契约)
- `[bg.global]` — 整体摄像机移动速度 / 默认 sway 参数

**为什么动画定义要从流水线开始**:
1. **action.frame_count / asset_prefix 跟 pngseq 强绑定** — 流水线烘 20 帧,LVGL frame_count 必须 20,手动同步必出错
2. **part.hat enable=false 这种艺术约束跟素材绑定** — C01 美术左耳被遮挡 → 不能 bounce,这是素材包事实
3. **default_skin 是素材包指定主角** — 跟 CHAR_ACCESSORIES 一样属于素材层决策
4. **bg.sway / bg.parallax 跟图层数量+图层语义绑定** — 北极的"l10-block"是前景遮挡(parallax=1.0,不摆动),海底的"水母层"要左右摆动(sway_enable=true),这些跟图层身份绑定,不是 LVGL 工程的事实

---

## 1. 输入(只读,不在本仓库)

### 1.1 角色素材(6 包)

| 路径 | 内容 |
|------|------|
| `/Users/chansen2000/Downloads/素材/选择/{小猫,小熊,企鹅,小兔,小鸡,熊猫}/Json Atlas/Characters.json` | Spine 骨骼 JSON |
| `/Users/chansen2000/Downloads/素材/选择/{素材}/Spine/C{01..15}/*.png` | 单部件原图 |
| `/Users/chansen2000/Downloads/素材/选择/{素材}/Png/Character{01..15}/{Action}/*.png` | 整身动画帧序列 |

### 1.2 背景素材(9 包)

| 路径 | 内容 |
|------|------|
| `/Users/chansen2000/Downloads/素材/选择/{北极,大自然,海底,海滩,森林,沙漠,石头,太空,西部}/_PNG/{variant}/layers/*.png` | 类型 A:layers/ 子目录(z 顺序按文件名数字) |
| `/Users/chansen2000/Downloads/素材/选择/{沙漠,石头,西部}/PNG/{variant}/{background,1..N}.png` | 类型 B:平铺编号 |

每个背景包通常有 4 个变体,每变体 3~10 图层,1920×1080。

---

## 2. 文件清单

### 2.1 引擎层(可复用,无副作用)

#### `assembler/config.py` — ⚠️ 含越界字段

- **位置**: `素材流水线/assembler/config.py`
- **业务功能**: 流水线全局常量与素材矩阵 — 所有素材包路径解析 + 角色配饰矩阵 + slot 渲染顺序的"中央配置"
- **正确职责**:
  - `MATERIALS_DIR` 素材根 / `CANVAS_W,H=788,504` / `P4_W,H=410,502`
  - `CHAR_ACCESSORIES` 15 角色配饰矩阵(资源事实,目前只覆盖小猫,**待扩到 6 包**)
  - `SLOT_DRAW_ORDER[material]` 渲染顺序(资源决策,**待扩到 6 包**)
  - `CORE_PARTS / ACCESSORY_PARTS / PROP_PARTS / FX_PARTS` 部件分类
  - `resolve_paths(material)` 路径解析
- **❌ 越界(待删)**: `CLICK_ANIM_MAP` — 应用决策,挪到 INI
- **输入**: 无(纯常量)
- **输出**: 无(被 import 使用)

#### `assembler/spine_assembler.py` — ⚠️ export_positions 含越界字段

- **位置**: `素材流水线/assembler/spine_assembler.py`
- **业务功能**: 把 Spine 骨骼动画文件解析成 410 视角下每个部件的精确位置/旋转/尺寸 — 一个 Spine 角色进,一张 PNG + 一份 JSON 出
- **职责**:
  - 读 `Characters.json`,递归计算骨骼世界变换链
  - `assemble(character, ...)` → 返回 (PIL.Image 788×504, positions 列表)
  - `scale_to_p4(image)` 视角缩放
  - `export_positions(positions, target_w, target_h)` 输出未旋转 sprite 的 TL+尺寸+中心 pivot
- **scale 算法(契约)**: `scale = min(tw/788, th/504)`,所有部件 `round(orig * scale)`
- **post-efe045e 修正**: positions 输出未旋转语义(`raw_w × scale`),不再输出已旋转 bbox
- **❌ 越界(待删)**: `export_positions` 末尾每个 part 写入 `clickable` / `click_anim` 字段
- **输入**:
  - `{material}/Json Atlas/Characters.json`
  - `{material}/Spine/C{01..15}/*.png`
- **输出**: 内存中的 PIL.Image 与 positions 列表(被 CLI 落盘)

#### `assembler/background_assembler.py` — ✅ 引擎通用,需扩资产烘焙

- **位置**: `素材流水线/assembler/background_assembler.py`
- **业务功能**: 把背景包(多张分层 PNG)按 z-order 叠成完整一张大图,并标注每图层的视差比 — 一个背景变体进,一张合成 PNG + 一份图层 JSON 出
- **职责**:
  - 自动探测 `_PNG` vs `PNG` / 类型 A(layers/)vs 类型 B(平铺编号)
  - 自然数字排序图层,叠加 → composite RGBA 1920×1080
  - 计算 `parallax_ratio = z / (total - 1)`(z=0 远景不动,z=max 前景全速跟镜头)
  - `export_layers(meta, target_w, target_h)` 导出 410 缩放后的图层坐标
- **输入**: `{背景}/{_PNG|PNG}/{variant}/layers/*.png` 或 `{背景}/{_PNG|PNG}/{variant}/{background,1..N}.png`
- **输出**: 内存 PIL.Image + 图层 meta(被 CLI 落盘)

---

### 2.2 入口 CLI(落盘第一段产物)

#### `assemble_cli.py` — ✅ 无越界

- **位置**: `素材流水线/assemble_cli.py`
- **业务功能**: 从美术资产到角色组合的 CLI — 命令行批量把 Spine 角色组合成完整一张 PNG,顺带导出 LVGL 消费的部件坐标 JSON
- **常用调用**: `python3 assemble_cli.py --material 小猫 --all --target 410x502 --export-lvgl`
- **职责**: 调用 SpineAssembler → 输出 PNG(整身) + JSON(部件坐标表)
- **输入**: 通过 SpineAssembler 间接读 Spine 资源
- **输出**:
  - `output/{material}/picture/410_502/C{01..15}_default.png`(整身预览图,留档用)
  - `output/{material}/json/410_502/C{01..15}_default_positions.json`(LVGL 消费的坐标表)

#### `assemble_bg.py` — ✅ 无越界

- **位置**: `素材流水线/assemble_bg.py`
- **业务功能**: 从美术资产到背景组合的 CLI — 命令行批量把背景图层叠成完整一张大图,顺带导出每图层视差比的 JSON
- **常用调用**: `python3 assemble_bg.py --all-materials --target 410x502 --export-lvgl`
- **职责**: 调用 BackgroundAssembler → 输出 PNG(合成图) + JSON(图层坐标 + 视差比)
- **输入**: 通过 BackgroundAssembler 间接读背景资源
- **输出**:
  - `output/{背景}/picture/410_502/variant_{name}.png`
  - `output/{背景}/json/410_502/variant_{name}_layers.json`

---

### 2.3 工具层(LVGL 资产烘焙)

#### `tools/gen_lvgl_meta.py` — ⚠️ 含越界字段,需扩多素材

- **位置**: `素材流水线/tools/gen_lvgl_meta.py`
- **业务功能**: 把 JSON 坐标表翻译成 LVGL C 端可以直接 `cat_parts_get(char_id)` 调用的代码 — JSON 进,头/源 C 文件出
- **职责**:
  - 读 N 份 JSON(每素材 ≤15 角色),按 z_order 升序排列
  - 校验必备 8 部件齐全 + 同名唯一,失败非零退出
  - 生成 `cat_parts_meta.h`(声明 + LV_IMAGE_DECLARE 列表)
  - 生成 `cat_parts_meta.c`(N 个 part_meta_t 数组 + cat_parts_find/get API)
- **❌ 越界(待删)**: `ANIM_MAP` + part_meta_t 的 `anim_type` 字段
- **当前局限**: 只读小猫,**待参数化为 `--material {小猫,小熊,...}` 或一次出多素材表**
- **输入**: `output/{material}/json/410_502/C*_default_positions.json`
- **输出**:
  - `output/{material}/lvgl_export/meta/cat_parts_meta.h`
  - `output/{material}/lvgl_export/meta/cat_parts_meta.c`

#### `tools/gen_part_dscs.sh` — ✅ 已写入流水线,需扩多素材

- **位置**: `素材流水线/tools/gen_part_dscs.sh`
- **业务功能**: 把 Spine 单部件原图烘成 LVGL ARGB8888 C 数组 — 部件 PNG 进,部件 dsc C 文件出,LVGL 端直接以 `&cat_C01_Body` 引用
- **职责**:
  - 从 `cat_parts_meta.h` 解析 LV_IMAGE_DECLARE 列表(单一事实源)
  - 找 Spine 原图 → magick resize → npx lv_img_conv ARGB8888
  - sed post-process: lv_img_conv v0.4.0 输出 v8 → 转 v9
  - 找不到源图立刻 exit 1
- **scale 算法**: 与 SpineAssembler.export_positions 完全一致
- **当前局限**: 路径硬编码小猫,**待参数化 `SPINE_ROOT` / `META_H` / `OUT_DIR`**
- **输入**:
  - `output/{material}/lvgl_export/meta/cat_parts_meta.h`
  - `{material}/Spine/C{01..15}/<part>.png`
- **输出**: `output/{material}/lvgl_export/dsc/cat_C{01..15}_<part>.c`
- **格式**: `LV_COLOR_FORMAT_ARGB8888`

#### `gen_pngseq.sh` — ✅ 无越界,需扩多素材

- **位置**: `素材流水线/gen_pngseq.sh`(根目录,非 tools/)
- **业务功能**: 把整身动画帧序列(每 action 一组 PNG)烘成 LVGL RGB565A8 C 数组 — Action PNG 进,pngseq C 文件出
- **职责**: magick resize 410×502 → npx lv_img_conv RGB565A8 → sed v8→v9
- **覆盖**: 9 组 action × ~28 帧 ≈ 250 帧
- **当前局限**: 只读小猫 C01,**待参数化 + 支持每个素材包多角色**
- **输入**: `{material}/Png/Character{NN}/{Action}/*.png`
- **输出**: `output/{material}/lvgl_export/pngseq/pngseq_{Cxx}_{action}_{NN}.c`
- **格式**: `LV_COLOR_FORMAT_RGB565A8`

#### `tools/gen_bg_assets.sh` — ⚠️ 待新建(背景资产烘焙)

- **目标位置**: `素材流水线/tools/gen_bg_assets.sh`(新建)
- **业务功能**: 把背景每图层 PNG 烘成 LVGL RGB565 C 数组 — 图层 PNG 进,图层 dsc C 文件出
- **职责**:
  - 遍历 9 个背景包 × 4 变体 × 每变体图层
  - magick resize 到 410×502(或保持 1920×410 以支持横向滚动 — 需 sheng 决策)
  - npx lv_img_conv RGB565(或 RGB565A8 若有 alpha)
  - sed v8→v9
- **输入**: `output/{背景}/json/410_502/variant_*_layers.json`(图层清单)+ 原图
- **输出**: `output/{背景}/lvgl_export/bg/bg_{背景}_{variant}_{layer}.c`
- **格式**: `LV_COLOR_FORMAT_RGB565` 或 `RGB565A8`

#### `tools/gen_bg_meta.py` — ⚠️ 待新建(背景元数据 C 翻译)

- **目标位置**: `素材流水线/tools/gen_bg_meta.py`(新建)
- **业务功能**: 把背景图层 JSON 翻译成 LVGL C 端可以直接 `bg_variant_get(name)` 调用的代码 — 图层 JSON 进,头/源 C 文件出
- **职责**:
  - 读 9 个背景包的 `variant_*_layers.json`
  - 生成 `bg_meta.h` + `bg_meta.c`,定义 `bg_layer_meta_t { name, z_order, parallax_ratio, w, h, *img }`
  - 提供 `bg_variant_get(material, variant) → bg_layer_meta_t* + count` 查表 API
- **输入**: `output/{背景}/json/410_502/variant_*_layers.json`
- **输出**: `output/{背景}/lvgl_export/meta/bg_meta.{h,c}`(或汇总到统一 bg_meta.{h,c})

#### `config/{素材}/animation_config.ini` — ⚠️ 待新建(应用层契约源头)

- **目标位置**:
  - `素材流水线/config/小猫/animation_config.ini`
  - `素材流水线/config/小熊/animation_config.ini`(将来)
  - `素材流水线/config/北极/animation_config.ini`(背景动画,将来)
  - …
- **当前位置**: `lv_port_pc_vscode/src/cartoon/config/animation_config.ini`(待迁移)
- **业务功能**: 应用层契约源头 — 谁会动 / 怎么动 / idle 候选 / 背景视差与摆动,跟具体素材包绑定
- **职责**:
  - 角色包: `[global] / [idle_script] / [part.X] / [action.X]`
  - 背景包: `[bg.global] / [bg.{layer_name}]`(每图层是否摆动 / 视差 override)
- **维护人**: Sonnet
- **同步**: build_assets.sh 拷到 `lv_port_pc_vscode/src/cartoon/config/`

#### `tools/validate_animation_config.py` — ⚠️ 待新建

- **目标位置**: `素材流水线/tools/validate_animation_config.py`(新建)
- **业务功能**: 校验应用层 INI 跟资源层 C 数组的一致性 — 防止 frame_count / asset_prefix / 图层 sway 配错
- **职责**:
  - 读 `config/{素材}/animation_config.ini` 解析所有 `[action.X]` 与 `[bg.X]`
  - 扫资源产物(pngseq 帧数 / bg 图层名)
  - 角色: 每 `[action.X].frame_count` = pngseq 实际帧数;`[part.X]` 的 X 必须在 part_meta_t 部件清单
  - 背景: 每 `[bg.{layer}]` 的 layer 必须在 bg_meta 图层清单
  - 任一不一致 → 打印明细 + exit 1
- **输入**: INI + 资源产物目录
- **输出**: 0 / 非零退出

---

### 2.4 编排层(一键流水线)

#### `build_assets.sh` — ⚠️ 需扩到 8 步 + 多素材循环

- **位置**: `素材流水线/build_assets.sh`
- **业务功能**: 一键编排 — 把所有素材包的资源 + 应用契约从源头烘焙好,拷贝到 LVGL 工程,LVGL 端零手编辑
- **目标流程**(对每个角色素材包循环):
  1. `python3 assemble_cli.py --material {M} --all --target 410x502 --export-lvgl` — 出 JSON
  2. `python3 tools/gen_lvgl_meta.py --material {M}` — 出 meta.{h,c}
  3. `bash tools/gen_part_dscs.sh {M}` — 出单部件 dsc(ARGB8888)
  4. `bash gen_pngseq.sh {M}` — 出 pngseq(RGB565A8)

  对每个背景素材包循环:

  5. `python3 assemble_bg.py --material {B} --all --target 410x502 --export-lvgl` — 出 JSON
  6. `bash tools/gen_bg_assets.sh {B}` — 出 bg layer dsc
  7. `python3 tools/gen_bg_meta.py --material {B}` — 出 bg_meta.{h,c}

  统一收尾:

  8. `python3 tools/validate_animation_config.py` — 校验所有 INI 与资源一致(任一失败 exit 1)
  9. `python3 LVGL/tools/gen_frame_lookup.py` — 扫 pngseq 生成 lookup 表
  10. `cp` 全部产物 → LVGL 工程对应目录(资产 + INI)

---

### 2.5 周边工具(开发期,不在主流水线)

#### `verify_assembler.py` — ✅ 测试驱动

- **位置**: `素材流水线/verify_assembler.py`
- **业务功能**: SpineAssembler 硬编码回归测试 — 跑 5 个 sample 验证组合算法没退化
- **职责**: 跑 C01 default / no_glasses / naked / C05 / C03 no_cloth
- **输出**: `output/小猫/picture/788_504/*.png`

#### `preview_anim.py` — ✅ 开发预览

- **位置**: `素材流水线/preview_anim.py`
- **业务功能**: matplotlib 可视化预览动画帧序列 — 检查美术原图有没有缺帧/帧序错乱,开发期检查工具
- **职责**: 读 `素材/选择/小猫/Png/Character{NN}/{Action}/*.png`,键盘 1-9 切 action,G 导出 GIF
- **输出**: `output/previews/*.gif`(开发期产物)
- **状态**: 不在 build_assets.sh

---

## 3. 数据流(完整链路)

```
═══════════ 角色资产流(每个素材包: 小猫/小熊/...) ═══════════

Spine 资源 (素材/选择/{material}/)
   ├── Json Atlas/Characters.json ──┐
   ├── Spine/C{01..15}/*.png        │
   └── Png/Character{NN}/{Action}/*.png
                                    │
                                    ▼
                 ┌────── assemble_cli.py --material {M}
                 │        (SpineAssembler)
                 │
                 ▼
       output/{M}/json/410_502/C{01..15}_default_positions.json
                                    │
                                    ▼
                 ┌────── tools/gen_lvgl_meta.py --material {M}
                 │
                 ▼
       output/{M}/lvgl_export/meta/cat_parts_meta.{h,c}
                                    │
                                    ▼ (LV_IMAGE_DECLARE 清单)
                 ┌────── tools/gen_part_dscs.sh {M}
                 │
                 ▼
       output/{M}/lvgl_export/dsc/cat_C{01..15}_<part>.c (ARGB8888)


       素材/选择/{M}/Png/Character{NN}/{Action}/*.png
                                    │
                                    ▼
                 ┌────── gen_pngseq.sh {M}
                 │
                 ▼
       output/{M}/lvgl_export/pngseq/pngseq_C{NN}_{action}_{NN}.c (RGB565A8)


═══════════ 背景资产流(每个背景包: 北极/海底/...) ═══════════

背景资源 (素材/选择/{B}/{_PNG|PNG}/{variant}/layers/*.png)
                                    │
                                    ▼
                 ┌────── assemble_bg.py --material {B}
                 │        (BackgroundAssembler)
                 │
                 ▼
       output/{B}/json/410_502/variant_{name}_layers.json
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
            ┌── tools/gen_bg_assets.sh {B}    tools/gen_bg_meta.py {B}
            │
            ▼
       output/{B}/lvgl_export/bg/bg_{B}_{variant}_{layer}.c (RGB565)
            │
            └────────────► output/{B}/lvgl_export/meta/bg_meta.{h,c}


═══════════ 应用契约流(每个素材包一份 INI) ═══════════

       config/{M}/animation_config.ini       (角色: idle_script / part.X / action.X)
       config/{B}/animation_config.ini       (背景: bg.global / bg.{layer})
                          │
                          │ frame_count/asset_prefix/layer 名一致性
                          ▼
                 ┌────── tools/validate_animation_config.py
                 │        (失败 exit 1)
                 ▼
       (校验通过)


═══════════ 收尾 ═══════════

所有产物 → build_assets.sh step 10 → cp →
   ├── lv_port_pc_vscode/src/cartoon/assets/      (角色 meta + dsc + pngseq + frame_lookup)
   ├── lv_port_pc_vscode/src/cartoon/assets/bg/   (背景 layer dsc + bg_meta)
   └── lv_port_pc_vscode/src/cartoon/config/      ({material}_animation_config.ini × N)
                          │
                          ▼
            LVGL CMake GLOB 自动收录
            cat_parts_get / bg_variant_get / cartoon_config_load 消费
```

---

## 4. 架构越界 — 待清理清单(3 处)

| 序号 | 位置 | 越界字段 | 应在哪 | 删除影响 |
|------|------|----------|--------|----------|
| ❌ 1 | `assembler/config.py` | `CLICK_ANIM_MAP` | `config/{素材}/animation_config.ini` | 直接删,无引用断裂(只被 ❌2 用) |
| ❌ 2 | `assembler/spine_assembler.py` `export_positions` | `clickable` / `click_anim` 字段 | LVGL 端运行时查 INI | JSON 字段消失,需同步删 ❌3 读取 |
| ❌ 3 | `tools/gen_lvgl_meta.py` | `ANIM_MAP` + `anim_type` 字段写入 | 同上 | part_meta_t 结构体收缩,需同步改 LVGL 消费侧 |

**清理后的 part_meta_t 结构(目标态)**:
```c
typedef struct {
    const char *name;
    int16_t  x, y, w, h;
    int16_t  pivot_x, pivot_y;
    int16_t  rotation_01;
    const lv_image_dsc_t *img;
    /* anim_type 已移除 — 应用层查 animation_config.ini */
} part_meta_t;
```

**清理后的 JSON 部件结构(目标态)**:
```json
{
  "name": "Hand_B",
  "file": "C01/Hand_B.png",
  "x": 225, "y": 284, "w": 40, "h": 39,
  "pivot_x": 20, "pivot_y": 19,
  "rotation": -16.7,
  "z_order": 2,
  "category": "core"
}
```
(删除 `clickable` / `click_anim` 两字段)

---

## 5. 资源齐备性自检(build_assets.sh 后必过)

| 校验项 | 命令 | 期望 |
|--------|------|------|
| 角色 meta 部件数 | `grep LV_IMAGE_DECLARE output/{M}/lvgl_export/meta/cat_parts_meta.h \| wc -l` | 等于 dsc 文件数 |
| 角色 dsc 格式 | `grep -L 'LV_COLOR_FORMAT_ARGB8888' output/{M}/lvgl_export/dsc/*.c` | 空 |
| 角色 pngseq 格式 | `grep -L 'LV_COLOR_FORMAT_RGB565A8' output/{M}/lvgl_export/pngseq/*.c` | 空 |
| 背景 bg dsc 格式 | `grep -L 'LV_COLOR_FORMAT_RGB565' output/{B}/lvgl_export/bg/*.c` | 空 |
| 背景 meta 图层数 | `grep -c 'bg_layer_meta_t' output/{B}/lvgl_export/meta/bg_meta.c` | 等于 bg dsc 文件数 |
| C01 Hand_B 尺寸 | dsc 头 `.w/.h` vs JSON | 40/39 一致 |
| INI vs 资源一致 | `python3 tools/validate_animation_config.py` | 退出码 0 |
| INI 同步 | `diff config/ lv_port_pc_vscode/src/cartoon/config/` | 仅扩展名/路径差异 |

---

## 6. 落地分期(优先级)

| 期 | 范围 | 状态 |
|----|------|------|
| **P0(本任务)** | 小猫: dsc 入流水线 + 越界清理 + INI 迁到流水线 + 多素材路径参数化 | ⏳ 待 sheng 批准后让 Sonnet 执行 |
| P1 | 其余 5 角色包(小熊/企鹅/小兔/小鸡/熊猫): 复用 P0 的参数化工具 | 后续 |
| P2 | 9 背景包烘焙: gen_bg_assets.sh + gen_bg_meta.py + bg INI 契约 | 后续 |
| P3 | LVGL 端 bg_driver.c 接入 bg_meta + INI 视差/摆动 | 后续(kaifu) |

**P0 强制要求**: 所有工具必须**多素材参数化**,不允许把 "小猫" 字符串硬编码,确保 P1/P2 直接复用。

---

## 7. 不在本流水线范围(明确排除)

- LVGL 工程内 C 代码改动(channel_animal.c / scene_forest.c / bg_driver.c 是 kaifu 的事)
- LVGL 工程的 `animation_config.ini` 手动编辑 — 改成 build 产物
- preview_anim.py / verify_assembler.py 为开发期工具,不烘焙到 LVGL


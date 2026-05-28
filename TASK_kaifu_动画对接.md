# TVCartoon: 素材流水线对接 — 开发任务书

> 发件: Sonnet (开发主管)  
> 收件: kaifu (固件显示动画)  
> 日期: 2026-05-27

## 核心原则

**流水线是唯一生产者，LVGL 是纯粹消费者。C 端不重新拼装、不重新计算坐标。**

流水线已完成：
- 读取 Spine 骨骼 → 递归计算 21 骨骼 world transform
- 每个部件精确定位 (x, y, rotation, pivot)
- 合成完整 PNG（已验证像素级对齐参考帧）
- 输出 JSON = 每个部件在合成图上的位置、旋转、动画类型

kaifu 的工作是消费这些数据，不需要重做任何计算。

## 可用数据

```
素材流水线/output/小猫/
├── picture/410_502/C01_default.png ~ C15_default.png   # 合成 PNG，直接显示
└── json/410_502/C01_default_positions.json              # 部件坐标 + 动画描述
```

JSON 内容（C01 示例，完整 10 个部件）：

```json
{
  "character": "C01",
  "canvas": {"w": 410, "h": 502},
  "parts": [
    {"name":"Shadow",  "x":180,"y":325,"w":73,"h":26, "pivot_x":36,"pivot_y":13, "rotation":0.0, "z_order":0, "click_anim":null},
    {"name":"Hand_B",  "x":220,"y":279,"w":50,"h":49, "pivot_x":25,"pivot_y":24, "rotation":-16.7, "z_order":4, "click_anim":null},
    {"name":"Tails",   "x":150,"y":308,"w":52,"h":34, "pivot_x":26,"pivot_y":17, "rotation":-2.6, "z_order":5, "click_anim":"wag"},
    {"name":"Body",    "x":168,"y":233,"w":96,"h":111,"pivot_x":48,"pivot_y":55, "rotation":0.0, "z_order":7, "click_anim":"bounce"},
    {"name":"Eye1",    "x":215,"y":269,"w":32,"h":17, "pivot_x":16,"pivot_y":8,  "rotation":0.0, "z_order":11,"click_anim":"spin"}
  ]
}
```

所有字段含义见 `USAGE.md`。

## 任务

### 任务 1: 静态显示 — 用合成 PNG

用流水线的 `C01_default.png` (410×502) 直接显示。一个 `lv_image` 搞定。

验证：和流水线 output 截图一致。

### 任务 2: 点击动画 — JSON 驱动覆盖层

**不预创建 10 个部件。** 只在点击时创建覆盖层。

流程：
1. 解析 JSON → 得到每个部件的 `x, y, w, h, click_anim, pivot_x, pivot_y, rotation`
2. 为每个 `click_anim != null` 的部件在合成图上方放透明点触区 (`lv_obj` 设 `clickable`，大小=w×h，位置=x,y)
3. 点击点触区 → 创建该部件的 `lv_image` 覆盖层（位置=x,y，旋转=rotation），播动画
4. 动画结束 → 删除覆盖层

```c
// 伪代码
void on_part_click(lv_event_t *e) {
    part_info_t *part = lv_event_get_user_data(e);
    
    // 创建覆盖层，放在合成图的同一坐标
    lv_obj_t *overlay = lv_image_create(parent);
    lv_image_set_src(overlay, part->img_src);
    lv_obj_set_pos(overlay, part->x, part->y);
    lv_image_set_rotation(overlay, part->rotation * 10);
    
    // 播动画
    if (part->click_anim == BOUNCE) {
        // lv_anim 改 y，±20px 来回
    } else if (part->click_anim == SPIN) {
        // lv_anim 改 rotation，0→360°
    } else if (part->click_anim == WAG) {
        // lv_anim 改 rotation，±15° 来回 3 次
    }
    
    // 动画结束 → lv_obj_del(overlay)
}
```

部件图片从哪里来：从 Sprites 目录里提前转好 C 数组，或者按需加载。只需要 `click_anim != null` 的几个部件：Body (bounce), Eye1 (spin), Eye2 (spin), Tails (wag), Hat (bounce)。其余 6 个部件不需要单独加载。

### 任务 3: 15 角色切换

1. 定义 15 个角色的静态图（合成 PNG）和 JSON 数据
2. 切换角色 = 换底图 + 换 JSON 数据（点触区位置跟着变）
3. 每个角色的 `part_count` 不同（C01=10, C05=8），点触区动态创建

### 任务 4: 清理旧代码

`animal_driver` 的逐部件拼装逻辑不再需要。如果 `bg_driver` 仍有价值（森林背景层+摇摆），保留；否则一起清掉。

## 不需要做

- ❌ 在 C 端重新逐部件拼装猫
- ❌ 重新计算部件坐标
- ❌ 对 z-order 排序
- ❌ 预创建 10 个 lv_image

流水线已经全算了。LVGL 只消费结果。

## 验证标准

- C01 静态显示 = 流水线合成图，像素一致
- 点 Body → 身体弹跳，动画后恢复
- 点 Eye1 → 眼睛旋转
- 点 Tails → 尾巴摇摆
- 切到 C05 → 无帽子无眼镜，部件数正确

## 参考

| 文件 | 内容 |
|------|------|
| `output/小猫/picture/410_502/` | 15 张合成 PNG |
| `output/小猫/json/410_502/` | 15 份部件坐标 JSON |
| `USAGE.md` | JSON 字段说明、动画 C 代码 |
| `IMPLEMENTATION.md` | 流水线算法总览 |

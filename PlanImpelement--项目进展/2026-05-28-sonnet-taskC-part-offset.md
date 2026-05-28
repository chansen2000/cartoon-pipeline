# Sonnet Task C — 应用层位置覆盖通道(part_offset) 完成

**日期**: 2026-05-28
**实施人**: Sonnet
**范围**: 流水线 INI source + LVGL cartoon_config + channel_animal 三层联动

## 实施内容

### 1.1 流水线 INI source
- `config/小猫/animation_config.ini` 末尾追加 `[part_offset]` 段
- hat_dx=0, hat_dy=0 (默认, 由 sheng 真机调)

### 1.2 cartoon_config.h
- 新增 `part_offset_t` (name[16]/dx/dy) + `part_offset_table_t` (items[16]/count)
- `cartoon_config_t` 末尾加 `part_offset_table_t part_offset`
- API 声明: `cartoon_config_find_part_offset(name)`

### 1.3 cartoon_config.c
- `_ini_handler` 加 `[part_offset]` 段处理: 解析 `<part>_dx/_dy`, 首字母大写规范化, 查表或新建
- `_dump_config` 末尾加 part_offset 打印
- `cartoon_config_find_part_offset` 实现: simple strcmp loop

### 1.4 channel_animal.c
- `_create_parts` 循环: `lv_obj_set_pos(img, m->x + dx, m->y + dy)`
- 通过 `cartoon_config_find_part_offset(m->name)` 查 offset
- offset 不存在 → dx/dy=0 → 行为不变(向后兼容)
- pivot/rotation 不动

## 验证结果

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | INI diff | ✅ 仅末尾追加 [part_offset] |
| 2 | cartoon_config.h diff | ✅ 仅加 struct + API 声明 |
| 3 | cartoon_config.c diff | ✅ 仅加解析 + API + dump |
| 4 | channel_animal.c diff | ✅ 仅 _create_parts lv_obj_set_pos |
| 5 | build_assets.sh exit 0 | ✅ |
| 6 | cmake + make 0 error 0 warning | ✅ |
| 7-10 | SDL 真机验证 | ⚠️ 需 sheng/kaifu 验证 (无显示器) |

## 涉及文件

- 修改: `素材流水线/config/小猫/animation_config.ini`
- 修改: `lv_port_pc_vscode/src/cartoon/config/cartoon_config.h`
- 修改: `lv_port_pc_vscode/src/cartoon/config/cartoon_config.c`
- 修改: `lv_port_pc_vscode/src/cartoon/channel/channel_animal.c`

"""TVCartoon 组装系统 — 配置与常量"""

import os

# ── 素材根路径 ──────────────────────────────────────────
MATERIALS_DIR = "/Users/chansen2000/Downloads/素材/选择"
DEFAULT_MATERIAL = "小猫"

# ── 画布尺寸 ──────────────────────────────────────────
CANVAS_W, CANVAS_H = 788, 504
P4_W, P4_H = 410, 502

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def resolve_paths(material_name):
    """根据素材名解析路径，返回 (characters_json, sprites_root, picture_dir, json_dir)"""
    import os as _os
    base = _os.path.join(MATERIALS_DIR, material_name)
    characters_json = _os.path.join(base, "Json Atlas/Characters.json")
    sprites_root = _os.path.join(base, "Spine")
    picture_dir = _os.path.join(OUTPUT_DIR, material_name, "picture")
    json_dir = _os.path.join(OUTPUT_DIR, material_name, "json")
    return characters_json, sprites_root, picture_dir, json_dir

# ── 部件分类 ──────────────────────────────────────────
CORE_PARTS = {"Shadow", "Body", "Eye1", "Eye2", "Leg_B", "Leg_F",
              "Tails", "Hand_B", "Hand_F"}
ACCESSORY_PARTS = {"Hat", "Glasses", "Cloth"}
PROP_PARTS = {"Hammer", "Umbrella", "Hand_B2", "Leg_F2"}
FX_PARTS = {"Confuse Fx1", "Confuse Fx2", "Confuse Fx3",
            "Confuse Fx4", "Confuse Fx5", "Confuse Fx6",
            "Star", "Splash", "Splash2", "Box"}

# ── 各角色配饰 ────────────────────────────────────────
CHAR_ACCESSORIES = {
    "C01": {"hat": True,  "glasses": True,  "cloth": False},
    "C02": {"hat": True,  "glasses": False, "cloth": False},
    "C03": {"hat": True,  "glasses": False, "cloth": True},
    "C04": {"hat": False, "glasses": False, "cloth": True},
    "C05": {"hat": False, "glasses": False, "cloth": False},
    "C06": {"hat": True,  "glasses": False, "cloth": False},
    "C07": {"hat": False, "glasses": False, "cloth": True},
    "C08": {"hat": False, "glasses": True,  "cloth": False},
    "C09": {"hat": False, "glasses": False, "cloth": False},
    "C10": {"hat": False, "glasses": False, "cloth": False},
    "C11": {"hat": False, "glasses": False, "cloth": False},
    "C12": {"hat": False, "glasses": False, "cloth": False},
    "C13": {"hat": False, "glasses": False, "cloth": False},
    "C14": {"hat": False, "glasses": True,  "cloth": False},
    "C15": {"hat": True,  "glasses": False, "cloth": False},
}

# ── 默认配置 ──────────────────────────────────────────
DEFAULT_ACCESSORIES = {"hat": True, "glasses": True, "cloth": True}
DEFAULT_PROPS = {"hammer": False, "umbrella": False}
DEFAULT_EFFECTS = {"confuse": False, "star": False, "splash": False}

# ── Slot 绘制顺序 (per material) ──────────────────────
# 定义各 slot 从底到顶的绘制顺序。列表中的 slot 按此序排 z_order，
# 未在列表中的 slot 追加在末尾（保持原有相对顺序）。
# 不定义或为空 → 沿用 Spine JSON slots 数组顺序（默认行为）。
SLOT_DRAW_ORDER = {
    "小猫": [
        "Shadow", "Leg_B", "Hand_B", "Tails",
        "Body", "Cloth",         # Body → Cloth (若有)
        "Hat",                    # Hat 必须在 Body/Cloth 之上 (帽子戴在头顶)
        "Leg_F", "Eye1", "Glasses", "Hand_F",
    ],
}

# ── 点击动画映射 ──────────────────────────────────────
CLICK_ANIM_MAP = {
    "Eye1":   "spin",
    "Eye2":   "spin",
    "Tails":  "wag",
    "Body":   None,    # 耳朵在 Body 里，bounce 暴露左右不对称
    "Hat":    None,    # bounce 暴露被盖住的左耳
    "Shadow": None,
    "Leg_B":  None,
    "Leg_F":  None,
    "Hand_B": None,
    "Hand_F": None,
}

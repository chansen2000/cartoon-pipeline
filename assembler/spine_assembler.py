"""TVCartoon — Spine 精确组装引擎"""

import json, math, os
from PIL import Image
from . import config


class SpineAssembler:
    """角色拼装引擎：骨骼矩阵链 + 附件定位 → 合成 PNG"""

    def __init__(self, material_name=None, json_path=None, sprites_root=None):
        self.material_name = material_name or config.DEFAULT_MATERIAL
        _jp, _sr, _, _ = config.resolve_paths(self.material_name)
        self.json_path = json_path or _jp
        self.sprites_root = sprites_root or _sr

        with open(self.json_path) as f:
            self.spine = json.load(f)

        self.skeleton = self.spine["skeleton"]
        self.canvas_w = int(self.skeleton["width"])
        self.canvas_h = int(self.skeleton["height"])

        # 骨骼 + slot 元数据
        self.bone_worlds = self._compute_bone_transforms()
        self.slot_bone = {s["name"]: s["bone"] for s in self.spine["slots"]}
        self.slot_order = self._resolve_draw_order()

        # 默认 slot attachment
        self._default_attachments = {}
        for s in self.spine["slots"]:
            if s.get("attachment"):
                self._default_attachments[s["name"]] = s["attachment"]

    # ── 解析 slot 绘制顺序 ────────────────────────────
    def _resolve_draw_order(self):
        """返回 slot 名列表，从底到顶。

        优先查 config.SLOT_DRAW_ORDER[material_name]；
        未定义则沿用 Spine JSON slots 数组顺序。
        """
        spine_order = [s["name"] for s in self.spine["slots"]]
        draw_order = config.SLOT_DRAW_ORDER.get(self.material_name)
        if not draw_order:
            return spine_order

        # 以 draw_order 为主序，不在列表中的 slot 追加在末尾
        result = [s for s in draw_order if s in spine_order]
        for s in spine_order:
            if s not in result:
                result.append(s)
        return result

    # ── 骨骼矩阵链 ────────────────────────────────────
    def _compute_bone_transforms(self):
        bones_raw = {b["name"]: b for b in self.spine["bones"]}
        world = {}

        def calc(name):
            if name in world:
                return world[name]
            bone = bones_raw[name]
            x   = bone.get("x", 0)
            y   = bone.get("y", 0)
            rot = math.radians(bone.get("rotation", 0))
            sx  = bone.get("scaleX", 1)
            sy  = bone.get("scaleY", 1)

            la =  math.cos(rot) * sx
            lb = -math.sin(rot) * sy
            lc =  math.sin(rot) * sx
            ld =  math.cos(rot) * sy

            parent = bone.get("parent")
            if parent is None:
                world[name] = {"a": la, "b": lb, "c": lc, "d": ld,
                               "worldX": x, "worldY": y}
            else:
                p = calc(parent)
                world[name] = {
                    "a": p["a"]*la + p["b"]*lc,
                    "b": p["a"]*lb + p["b"]*ld,
                    "c": p["c"]*la + p["d"]*lc,
                    "d": p["c"]*lb + p["d"]*ld,
                    "worldX": p["a"]*x + p["b"]*y + p["worldX"],
                    "worldY": p["c"]*x + p["d"]*y + p["worldY"],
                }
            return world[name]

        for name in bones_raw:
            calc(name)
        return world

    # ── 附件世界坐标 ──────────────────────────────────
    def _attachment_world_center(self, bone_world, att):
        att_x = att.get("x", 0)
        att_y = att.get("y", 0)
        wx = bone_world["a"]*att_x + bone_world["b"]*att_y + bone_world["worldX"]
        wy = bone_world["c"]*att_x + bone_world["d"]*att_y + bone_world["worldY"]
        return wx, wy

    # ── 世界 → 画布像素 ────────────────────────────────
    def _world_to_canvas(self, wx, wy):
        cx = wx - self.skeleton["x"]
        cy = (self.skeleton["y"] + self.skeleton["height"]) - wy
        return cx, cy

    # ── 获取 skin 的附件数据 ──────────────────────────
    def _get_skin(self, character):
        skin_name = f"Character{int(character[1:]):02d}"
        for s in self.spine["skins"]:
            if s["name"] == skin_name:
                return s
        return None

    # ── 计算有效旋转 ──────────────────────────────────
    def _effective_rotation(self, bone_world, att):
        bone_rot = math.degrees(math.atan2(bone_world["c"], bone_world["a"]))
        return bone_rot + att.get("rotation", 0)

    # ── 主入口：组装 ──────────────────────────────────
    def assemble(self, character="C01",
                 accessories=None, props=None, effects=None,
                 canvas_size=None, bg_color=None):
        """
        组装角色并返回 PIL.Image + 部件坐标列表。

        返回: (image: PIL.Image, positions: list[dict])
        """
        cw, ch = canvas_size or (self.canvas_w, self.canvas_h)
        canvas = Image.new("RGBA", (cw, ch),
                           bg_color if bg_color else (0, 0, 0, 0))

        skin = self._get_skin(character)
        if not skin:
            raise ValueError(f"角色 {character} 不存在 (skin Character{int(character[1:]):02d} 未找到)")

        # 解析配饰/道具/特效参数
        ac = dict(config.DEFAULT_ACCESSORIES)
        ac.update(config.CHAR_ACCESSORIES.get(character, {}))
        if accessories:
            ac.update(accessories)

        pr = dict(config.DEFAULT_PROPS)
        if props:
            pr.update(props)

        ef = dict(config.DEFAULT_EFFECTS)
        if effects:
            ef.update(effects)

        positions = []
        slot_attachments = self._resolve_attachments(character, skin, ac, pr, ef)

        for slot_name in self.slot_order:
            if slot_name not in slot_attachments:
                continue

            att_name = slot_attachments[slot_name]
            # 解析: "C01/Body" → 文件 "Body.png"
            file_name = att_name.split("/")[-1] + ".png"
            file_path = os.path.join(self.sprites_root, character, file_name)

            if not os.path.exists(file_path):
                continue

            bone_name = self.slot_bone[slot_name]
            bone_w = self.bone_worlds[bone_name]

            # 从 skin 获取附件偏移（skin key 以 C01 为基准）
            slot_atts = skin.get("attachments", {}).get(slot_name, {})
            att_data = slot_atts.get(att_name)
            if not att_data:
                part_name = att_name.split("/")[-1]
                att_data = slot_atts.get(f"C01/{part_name}") or slot_atts.get(part_name) or {}

            wx, wy = self._attachment_world_center(bone_w, att_data)
            eff_rot = self._effective_rotation(bone_w, att_data)
            cx, cy = self._world_to_canvas(wx, wy)

            # 加载、旋转、粘贴
            part_img = Image.open(file_path).convert("RGBA")
            orig_w, orig_h = part_img.size
            if abs(eff_rot) > 0.5:
                part_img = part_img.rotate(eff_rot, expand=True,
                                           resample=Image.BICUBIC)
            pw, ph = part_img.size
            paste_x = round(cx - pw/2)
            paste_y = round(cy - ph/2)
            canvas.paste(part_img, (paste_x, paste_y), part_img)

            z = self.slot_order.index(slot_name)
            cat = self._category(slot_name)
            parts_dir = os.path.join(self.sprites_root, character, file_name)

            positions.append({
                "name":       att_name.split("/")[-1],
                "slot":       slot_name,
                "file":       f"{character}/{file_name}",
                "canvas_x":   round(cx),
                "canvas_y":   round(cy),
                "paste_x":    paste_x,
                "paste_y":    paste_y,
                "img_w":      pw,
                "img_h":      ph,
                "orig_w":     orig_w,
                "orig_h":     orig_h,
                "pivot_x":    pw // 2,
                "pivot_y":    ph // 2,
                "rotation":   round(eff_rot, 1),
                "z_order":    z,
                "category":   cat,
                "clickable":  cat == "core" and att_name.split("/")[-1] in
                              config.CLICK_ANIM_MAP and
                              config.CLICK_ANIM_MAP[att_name.split("/")[-1]] is not None,
                "click_anim": config.CLICK_ANIM_MAP.get(att_name.split("/")[-1]),
            })

        return canvas, positions

    # ── 解析每个 slot 最终使用的附件 ───────────────────
    def _resolve_attachments(self, character, skin, ac, pr, ef):
        result = {}
        skin_atts = skin.get("attachments", {})

        for slot_name in self.slot_order:
            # 特效 slot
            if slot_name.startswith("Confuse Fx"):
                if ef.get("confuse"):
                    result[slot_name] = f"{character}/{slot_name}"
                continue
            if slot_name in ("Star", "Star2", "Star3"):
                if ef.get("star"):
                    result[slot_name] = f"{character}/{slot_name}"
                continue
            if slot_name in ("Splash", "Splash2"):
                if ef.get("splash"):
                    result[slot_name] = f"{character}/{slot_name}"
                continue

            # 道具 slot
            if slot_name == "Umbrella":
                if pr.get("umbrella"):
                    result[slot_name] = f"{character}/Umbrella"
                continue
            if slot_name == "Hand_B":
                if pr.get("hammer"):
                    result[slot_name] = f"{character}/Hammer"
                else:
                    result[slot_name] = f"{character}/Hand_B"
                continue

            # 配饰 slot
            if slot_name == "Hat":
                if ac.get("hat"):
                    result[slot_name] = f"{character}/Hat"
                continue
            if slot_name == "Hat_F":
                if ac.get("hat"):
                    result[slot_name] = "Hat_F"
                continue
            if slot_name == "Glasses":
                if ac.get("glasses"):
                    result[slot_name] = f"{character}/Glasses"
                continue
            if slot_name == "Cloth":
                if ac.get("cloth"):
                    result[slot_name] = "Cloth"
                continue

            # 核心部件
            default_att = self._default_attachments.get(slot_name)
            if default_att:
                # 替换角色前缀
                part_name = default_att.split("/")[-1]
                result[slot_name] = f"{character}/{part_name}"
            elif slot_name == "Box":
                pass  # 默认隐藏
            elif slot_name == "Hand_F":
                result[slot_name] = f"{character}/Hand_F"

        return result

    # ── 部件分类 ───────────────────────────────────────
    def _category(self, slot_name):
        if slot_name in ("Shadow", "Body", "Eye1", "Eye2", "Leg_B", "Leg_F",
                         "Tails", "Hand_B", "Hand_F"):
            return "core"
        if slot_name in ("Hat", "Glasses", "Cloth"):
            return "accessory"
        if slot_name in ("Hammer", "Umbrella"):
            return "prop"
        return "effect"

    # ── 获取可用配饰列表 ───────────────────────────────
    def get_available_accessories(self, character):
        info = config.CHAR_ACCESSORIES.get(character, {})
        return [k for k, v in info.items() if v]

    # ── 导出 LVGL 坐标表 (410×502) ─────────────────────
    def export_positions(self, positions, target_w=None, target_h=None):
        """输出未旋转 sprite 的 TL + 尺寸 + 中心 pivot。

        契约: LVGL 端用 lv_image_set_rotation() 自己旋转。
        (x, y) = 未旋转 sprite 左上角在目标画布上的位置，
        (w, h) = 未旋转 sprite 尺寸，
        (pivot_x, pivot_y) = 旋转轴心(图片中心)，
        rotation = 有效旋转角 (0.1°)。
        """
        tw, th = target_w or config.P4_W, target_h or config.P4_H
        scale_x = tw / self.canvas_w
        scale_y = th / self.canvas_h
        scale = min(scale_x, scale_y)
        scaled_w = round(self.canvas_w * scale)
        scaled_h = round(self.canvas_h * scale)
        offset_x = (tw - scaled_w) // 2
        offset_y = (th - scaled_h) // 2

        result = []
        for p in positions:
            pw = p["img_w"]       # 已旋转 bbox 宽
            ph = p["img_h"]       # 已旋转 bbox 高
            raw_w = round(p["orig_w"] * scale)
            raw_h = round(p["orig_h"] * scale)

            # 旋转中心 = 已旋转 bbox 的中心点 (画布坐标 → 目标坐标)
            center_x = (p["paste_x"] + pw / 2) * scale + offset_x
            center_y = (p["paste_y"] + ph / 2) * scale + offset_y

            # 未旋转 sprite 左上角 = 中心 − 未旋转尺寸的一半
            tl_x = round(center_x - raw_w / 2)
            tl_y = round(center_y - raw_h / 2)

            result.append({
                "name":       p["name"],
                "file":       p["file"],
                "x":          tl_x,
                "y":          tl_y,
                "w":          raw_w,
                "h":          raw_h,
                "pivot_x":    raw_w // 2,
                "pivot_y":    raw_h // 2,
                "rotation":   p["rotation"],
                "z_order":    p["z_order"],
                "category":   p["category"],
                "clickable":  p["clickable"],
                "click_anim": p["click_anim"],
            })
        return result

    def get_canvas_anchor(self, positions):
        """返回角色身体中心在目标画布上的 (x, y), 即 anchor。

        anchor = Body 部件的几何中心 (Body 是所有 15 角色的共同核心部件)。
        跟 LVGL 端 spawn_x/y 严格对应, 15 角色完全一致 (同一骨架)。
        """
        body = next((p for p in positions if p["name"] == "Body"), None)
        if body is None:
            raise RuntimeError("Body part not found in positions — cannot compute anchor")
        return body["x"] + body["w"] // 2, body["y"] + body["h"] // 2

    def scale_to_p4(self, image, target_w=None, target_h=None):
        """将 788×504 画布缩放到 P4 屏幕"""
        tw, th = target_w or config.P4_W, target_h or config.P4_H
        scale = min(tw / self.canvas_w, th / self.canvas_h)
        scaled_w = round(self.canvas_w * scale)
        scaled_h = round(self.canvas_h * scale)
        scaled = image.resize((scaled_w, scaled_h), Image.LANCZOS)
        screen = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        ox = (tw - scaled_w) // 2
        oy = (th - scaled_h) // 2
        screen.paste(scaled, (ox, oy), scaled)
        return screen

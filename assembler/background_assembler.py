"""TVCartoon — 背景图层叠加引擎"""

import os, re
from PIL import Image


class BackgroundAssembler:
    """背景拼装：图层叠加 → 复合 PNG + 图层元数据"""

    def __init__(self, material_name):
        from . import config

        self.material_name = material_name
        self.material_dir = os.path.join(config.MATERIALS_DIR, material_name)

        # 探测命名规范 (_PNG vs PNG, _AI vs AI)
        self.png_dir = self._find_dir("_PNG", "PNG")
        self.ai_dir  = self._find_dir("_AI", "AI")

        # 枚举变体 (01~04 或 game_background_1~4 或 1~4)
        self.variants = self._discover_variants()

    def _find_dir(self, *candidates):
        for name in candidates:
            path = os.path.join(self.material_dir, name)
            if os.path.isdir(path):
                return path
        raise FileNotFoundError(f"None of {candidates} found in {self.material_dir}")

    def _discover_variants(self):
        variants = []
        for name in sorted(os.listdir(self.png_dir)):
            vpath = os.path.join(self.png_dir, name)
            if not os.path.isdir(vpath):
                continue
            layers = self._read_layers(name)
            if layers:
                variants.append({
                    "name": name,
                    "path": vpath,
                    "layers": layers,
                })
        return variants

    def _read_layers(self, variant_name):
        """读取一个变体的图层列表，按 z-order 排序"""
        vdir = os.path.join(self.png_dir, variant_name)
        layers_dir = os.path.join(vdir, "layers")

        layer_files = []

        if os.path.isdir(layers_dir):
            # 类型 A: layers/ 子目录 — 按文件名自然数字排序
            pngs = sorted(
                [f for f in os.listdir(layers_dir) if f.lower().endswith(".png")],
                key=self._sort_key_natural
            )
            layer_files = [os.path.join(layers_dir, f) for f in pngs]
        else:
            # 类型 B: 平铺编号文件
            pngs = sorted(
                [f for f in os.listdir(vdir) if f.lower().endswith(".png")],
                key=self._sort_key_flat
            )
            layer_files = [os.path.join(vdir, f) for f in pngs]

        layers = []
        for i, fpath in enumerate(layer_files):
            name = os.path.splitext(os.path.basename(fpath))[0]
            layers.append({
                "name": name,
                "path": fpath,
                "z": i,
            })

        return layers

    def _sort_key_natural(self, fname):
        """自然数字排序: l1 < l2 < l10 (不是字符串序)"""
        base = os.path.splitext(fname)[0]
        # 提取第一个数字
        m = re.match(r"^[^\d]*(\d+)", base)
        if m:
            n = int(m.group(1))
            # 取数字后面的部分作为二级排序
            suffix = base[m.end():]
            return (n, suffix)
        return (9999, base)

    def _sort_key_flat(self, fname):
        """平铺型: background → z=0, 数字文件按数值排序"""
        base = os.path.splitext(fname)[0]
        if base.lower() == "background":
            return (0, 0)
        m = re.match(r"^(\d+)$", base)
        if m:
            return (1, int(m.group(1)))
        return (2, base)

    # ── 主入口 ──────────────────────────────────────

    def composite(self, variant_name, size=None):
        """
        叠加图层，返回 (PIL.Image, layers_meta).
        size: (w, h) 或 None (原始 1920×1080)
        """
        variant = next((v for v in self.variants if v["name"] == variant_name), None)
        if not variant:
            raise ValueError(f"变体 {variant_name} 不存在。可选: {self.list_variants()}")

        w, h = size or (1920, 1080)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        meta = []
        for layer in variant["layers"]:
            img = Image.open(layer["path"]).convert("RGBA")
            if (w, h) != (img.width, img.height):
                img = img.resize((w, h), Image.LANCZOS)
            canvas.paste(img, (0, 0), img)

            meta.append({
                "name": layer["name"],
                "z_order": layer["z"],
                "parallax_ratio": self._parallax_ratio(layer["z"], len(variant["layers"])),
                "src_w": img.width,
                "src_h": img.height,
            })

        return canvas, meta

    def _parallax_ratio(self, z, total):
        """z=0 → 0.0 (不动), z=max → 1.0 (全速)"""
        if total <= 1:
            return 0.0
        return round(z / (total - 1), 2)

    def list_variants(self):
        return [v["name"] for v in self.variants]

    # ── 导出 ──────────────────────────────────────

    def export_layers(self, meta, target_w, target_h):
        """缩放后的图层坐标"""
        result = []
        for m in meta:
            result.append({
                "name": m["name"],
                "z_order": m["z_order"],
                "parallax_ratio": m["parallax_ratio"],
                "w": m["src_w"],
                "h": m["src_h"],
                "x": 0,
                "y": 0,
            })
        return result

    def scale_to_target(self, image, target_w, target_h):
        scale = min(target_w / image.width, target_h / image.height)
        scaled_w = round(image.width * scale)
        scaled_h = round(image.height * scale)
        scaled = image.resize((scaled_w, scaled_h), Image.LANCZOS)
        screen = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        ox = (target_w - scaled_w) // 2
        oy = (target_h - scaled_h) // 2
        screen.paste(scaled, (ox, oy), scaled)
        return screen

    def list_materials():
        """返回所有可用背景主题"""
        import os as _os
        from . import config
        materials = []
        for name in sorted(_os.listdir(config.MATERIALS_DIR)):
            d = _os.path.join(config.MATERIALS_DIR, name)
            if not _os.path.isdir(d):
                continue
            # 有 _PNG 或 PNG 目录的就是背景素材
            for sub in ("_PNG", "PNG"):
                if _os.path.isdir(_os.path.join(d, sub)):
                    materials.append(name)
                    break
        return materials

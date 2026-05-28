#!/usr/bin/env python3
"""TVCartoon 背景组装 CLI — 图层叠加工具

用法:
  python3 assemble_bg.py --material 北极 --all                    # 北极全部 4 变体
  python3 assemble_bg.py --material 北极 --variant 01             # 单个变体
  python3 assemble_bg.py --material 北极 --all --target 410x502   # P4 缩放
  python3 assemble_bg.py --all-materials                          # 9 主题全部
"""

import sys, os, json, argparse

sys.path.insert(0, os.path.dirname(__file__))
from assembler.background_assembler import BackgroundAssembler
from assembler import config


def main():
    p = argparse.ArgumentParser(description="TVCartoon 背景图层叠加工具")
    p.add_argument("--material", default=None, help="背景主题名 (北极/海底/森林...)")
    p.add_argument("--all-materials", action="store_true", help="批量生成所有背景主题")
    p.add_argument("--variant", default=None, help="变体名 (01/game_background_1...)")
    p.add_argument("--all", action="store_true", help="生成该主题全部变体")
    p.add_argument("--list", action="store_true", help="列出变体")
    p.add_argument("--target", default="1920x1080", help="输出分辨率 WxH (默认 1920x1080)")
    p.add_argument("--export-lvgl", action="store_true", help="导出图层坐标 JSON")
    p.add_argument("--output", "-o", default=None, help="输出文件路径")
    args = p.parse_args()

    # 决定要处理的素材列表
    if args.all_materials:
        materials = BackgroundAssembler.list_materials()
    elif args.material:
        materials = [args.material]
    else:
        p.print_help()
        return

    tw, th = (int(x) for x in args.target.split("x"))

    for material in materials:
        _, _, pic_base, json_base = config.resolve_paths(material)

        try:
            bg = BackgroundAssembler(material)
        except FileNotFoundError as e:
            print(f"[{material}] 跳过: {e}")
            continue

        # --list
        if args.list:
            print(f"[{material}] 变体: {bg.list_variants()}")
            continue

        # 决定变体列表
        if args.all:
            variants = bg.list_variants()
        elif args.variant:
            variants = [args.variant]
        else:
            variants = bg.list_variants()

        res_dir = f"{tw}_{th}"
        pic_dir = os.path.join(pic_base, res_dir)
        json_dir = os.path.join(json_base, res_dir)
        os.makedirs(pic_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)

        for vname in variants:
            print(f"[{material}/{vname}] 叠加中...")
            try:
                img, meta = bg.composite(vname)
            except ValueError as e:
                print(f"  ❌ {e}")
                continue

            # 缩放
            if (tw, th) != (img.width, img.height):
                out_img = bg.scale_to_target(img, tw, th)
            else:
                out_img = img

            if args.output and len(variants) == 1:
                out_path = args.output
            else:
                out_path = os.path.join(pic_dir, f"variant_{vname}.png")

            out_img.save(out_path)
            print(f"  → {out_path} ({out_img.size[0]}×{out_img.size[1]}, {len(meta)} 图层)")

            if args.export_lvgl:
                layers = bg.export_layers(meta, tw, th)
                json_path = os.path.join(json_dir, f"variant_{vname}_layers.json")
                with open(json_path, "w") as f:
                    json.dump({
                        "material": material,
                        "variant": vname,
                        "canvas": {"w": tw, "h": th},
                        "source_size": {"w": 1920, "h": 1080},
                        "layer_count": len(layers),
                        "layers": layers
                    }, f, indent=2, ensure_ascii=False)
                print(f"  → {json_path}")

    print("Done.")


if __name__ == "__main__":
    main()

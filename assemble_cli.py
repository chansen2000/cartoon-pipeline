#!/usr/bin/env python3
"""TVCartoon 组装 CLI — 命令行组装工具

用法:
  python3 assemble_cli.py --char C01                          # 小猫 C01, 788×504
  python3 assemble_cli.py --char C01 --no-glasses             # C01 去眼镜
  python3 assemble_cli.py --char C01 --target 410x502         # 缩放到 P4 分辨率
  python3 assemble_cli.py --all --export-lvgl                 # 批量 15 角色 + JSON
  python3 assemble_cli.py --material 小熊 --all               # 小熊素材批量
"""

import sys, os, json, argparse

sys.path.insert(0, os.path.dirname(__file__))
from assembler.spine_assembler import SpineAssembler
from assembler import config


def main():
    p = argparse.ArgumentParser(description="TVCartoon 角色组装工具 (Spine → PNG + LVGL坐标)")
    p.add_argument("--char", default=None, help="角色名 (C01~C15)")
    p.add_argument("--all", action="store_true", help="批量生成所有角色")
    p.add_argument("--material", default=None, help="素材名 (默认 小猫, 可选: 企鹅/小鸡/小兔/小熊/熊猫)")
    p.add_argument("--no-hat", action="store_true", help="去掉帽子")
    p.add_argument("--no-glasses", action="store_true", help="去掉眼镜")
    p.add_argument("--no-cloth", action="store_true", help="去掉衣服")
    p.add_argument("--hammer", action="store_true", help="显示锤子")
    p.add_argument("--umbrella", action="store_true", help="显示雨伞")
    p.add_argument("--export-lvgl", action="store_true", help="导出 LVGL 坐标 JSON")
    p.add_argument("--target", default="788x504", help="输出分辨率 WxH (默认 788x504)")
    p.add_argument("--output", "-o", default=None, help="输出文件路径")
    args = p.parse_args()

    material = args.material or config.DEFAULT_MATERIAL
    _, _, pic_base, json_base = config.resolve_paths(material)

    # 解析目标分辨率
    tw, th = (int(x) for x in args.target.split("x"))
    res_dir = f"{tw}_{th}"
    pic_dir = os.path.join(pic_base, res_dir)
    json_dir = os.path.join(json_base, res_dir)
    os.makedirs(pic_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    a = SpineAssembler(material_name=material)

    # 解析配饰/道具
    accessories = {"hat": not args.no_hat, "glasses": not args.no_glasses,
                   "cloth": not args.no_cloth}
    props = {"hammer": args.hammer, "umbrella": args.umbrella}

    characters = []
    if args.all:
        characters = [f"C{i:02d}" for i in range(1, 16)]
    elif args.char:
        characters = [args.char]
    else:
        p.print_help()
        return

    for char in characters:
        print(f"[{material}/{char}] 组装中...")
        try:
            img, positions = a.assemble(char, accessories=accessories, props=props)
        except ValueError as e:
            print(f"  ❌ {e}")
            continue

        tags = []
        if args.no_hat: tags.append("no_hat")
        if args.no_glasses: tags.append("no_glasses")
        if args.no_cloth: tags.append("no_cloth")
        if args.hammer: tags.append("hammer")
        if args.umbrella: tags.append("umbrella")
        suffix = "_" + "_".join(tags) if tags else "_default"

        # 缩放到目标分辨率
        if (tw, th) != (a.canvas_w, a.canvas_h):
            out_img = a.scale_to_p4(img, tw, th)
        else:
            out_img = img

        if args.output and len(characters) == 1:
            out_path = args.output
        else:
            out_path = os.path.join(pic_dir, f"{char}{suffix}.png")

        out_img.save(out_path)
        print(f"  → {out_path} ({out_img.size[0]}×{out_img.size[1]}, {len(positions)} 部件)")

        if args.export_lvgl:
            lvgl = a.export_positions(positions, tw, th)
            json_path = os.path.join(json_dir, f"{char}{suffix}_positions.json")
            with open(json_path, "w") as f:
                json.dump({
                    "character": char,
                    "config": {"hat": accessories["hat"],
                               "glasses": accessories["glasses"],
                               "cloth": accessories["cloth"]},
                    "canvas": {"w": tw, "h": th},
                    "parts": lvgl
                }, f, indent=2, ensure_ascii=False)
            print(f"  → {json_path}")

    print("Done.")


if __name__ == "__main__":
    main()

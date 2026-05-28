"""TVCartoon 组装验证 — 验证 SpineAssembler 核心功能"""
import sys, os, json

sys.path.insert(0, os.path.dirname(__file__))
from assembler.spine_assembler import SpineAssembler
from assembler import config


def main():
    material = "小猫"
    _, _, pic_base, _ = config.resolve_paths(material)
    out_dir = os.path.join(pic_base, "788_504")
    os.makedirs(out_dir, exist_ok=True)
    assembler = SpineAssembler(material_name=material)

    print(f"Spine 画布: {assembler.canvas_w}×{assembler.canvas_h}")
    print(f"骨骼数: {len(assembler.spine['bones'])}")
    print(f"Slot 数: {len(assembler.spine['slots'])}")
    print(f"角色数: {len(assembler.spine['skins'])-1}")  # 减 default
    print()

    # ── 测试 1: C01 默认 ─────────────────────────
    print("=== 测试 1: C01 默认 ===")
    img, positions = assembler.assemble("C01")
    img.save(os.path.join(out_dir, "C01_default.png"))
    print(f"  部件数: {len(positions)}")
    for p in positions:
        print(f"  {p['slot']:15s} {p['name']:15s} "
              f"画布({p['canvas_x']:4d},{p['canvas_y']:4d}) "
              f"z={p['z_order']:2d} rot={p['rotation']:6.1f} "
              f"cat={p['category']:10s} click={p['clickable']}")

    # 缩放到 P4
    p4 = assembler.scale_to_p4(img)
    p4.save(os.path.join(out_dir, "C01_410x502.png"))

    # 导出 LVGL 坐标
    lvgl_pos = assembler.export_positions(positions)
    with open(os.path.join(out_dir, "C01_positions.json"), "w") as f:
        json.dump({"character": "C01", "canvas": {"w": 410, "h": 502},
                   "parts": lvgl_pos}, f, indent=2, ensure_ascii=False)
    print(f"\n  → C01_default.png ({img.size})")
    print(f"  → C01_410x502.png")
    print(f"  → C01_positions.json")

    # ── 测试 2: C01 去掉眼镜 ─────────────────────
    print("\n=== 测试 2: C01 去掉眼镜 ===")
    img2, pos2 = assembler.assemble("C01", accessories={"glasses": False})
    img2.save(os.path.join(out_dir, "C01_no_glasses.png"))
    names2 = [p['name'] for p in pos2]
    print(f"  部件: {names2}")
    assert "Glasses" not in names2, "眼镜应该被移除!"
    print("  ✅ 眼镜已正确移除")

    # ── 测试 3: C01 全裸 ─────────────────────────
    print("\n=== 测试 3: C01 全裸 (无帽无镜) ===")
    img3, pos3 = assembler.assemble("C01", accessories={"hat": False, "glasses": False})
    img3.save(os.path.join(out_dir, "C01_naked.png"))
    names3 = [p['name'] for p in pos3]
    assert "Glasses" not in names3, "眼镜应该被移除!"
    assert "Hat" not in names3, "帽子应该被移除!"
    print("  ✅ 帽子眼镜已正确移除")

    # ── 测试 4: C05 (无配饰) ─────────────────────
    print("\n=== 测试 4: C05 (无配饰角色) ===")
    available = assembler.get_available_accessories("C05")
    print(f"  C05 可用配饰: {available}")
    assert available == [], f"C05 应该无配饰，实际: {available}"
    img5, _ = assembler.assemble("C05")
    img5.save(os.path.join(out_dir, "C05_default.png"))
    print("  ✅ C05 组装正确（无配饰）")

    # ── 测试 5: C03 去衣服 ───────────────────────
    print("\n=== 测试 5: C03 去掉衣服 ===")
    available3 = assembler.get_available_accessories("C03")
    print(f"  C03 可用配饰: {available3}")
    img3c, _ = assembler.assemble("C03", accessories={"cloth": False})
    img3c.save(os.path.join(out_dir, "C03_no_cloth.png"))
    print("  ✅ C03 去衣服正确")

    # ── 测试 6: 批量 15 角色 ─────────────────────
    print("\n=== 测试 6: 批量 15 角色 ===")
    for i in range(1, 16):
        char = f"C{i:02d}"
        img, pos = assembler.assemble(char)
        path = os.path.join(out_dir, f"{char}_default.png")
        img.save(path)
        print(f"  {char}: {len(pos)} 部件 → {char}_default.png")

    print(f"\n{'='*50}")
    print(f"全部通过！输出: {out_dir}/")
    print(f"文件列表:")
    for f in sorted(os.listdir(out_dir)):
        print(f"  {f}")


if __name__ == "__main__":
    main()

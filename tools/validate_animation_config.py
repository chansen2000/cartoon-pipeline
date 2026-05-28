#!/usr/bin/env python3
"""validate_animation_config.py — 校验 INI 与产出资产一致性

用法:
  python3 tools/validate_animation_config.py

校验项:
  1. 小猫 INI:
     - [action.X] 的 X 在 pngseq/ 有对应 .c 文件
     - frame_count 匹配实际文件数
     - asset_prefix 匹配实际文件名前缀
     - [part.X] 的 X 能映射到 cat_parts_meta.h 里的部件名
  2. 森林 INI:
     - [bg.{layer}] 的 layer 存在于任一变体 JSON 的 layers 数组中
     - [bg.global] 必须存在

任一失败 → 打印明细 → sys.exit(1)
"""

import configparser
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "tools" else SCRIPT_DIR

# 小猫 INI part → meta 部件名映射
PART_NAME_MAP = {
    "eye":  "Eye1",
    "tail": "Tails",
    "hat":  "Hat",
}


def validate_cat_ini():
    ini_path = os.path.join(PROJECT_DIR, "config", "小猫", "animation_config.ini")
    pngseq_dir = os.path.join(PROJECT_DIR, "output", "小猫", "lvgl_export", "pngseq")
    meta_h = os.path.join(PROJECT_DIR, "output", "小猫", "lvgl_export", "meta", "cat_parts_meta.h")

    if not os.path.exists(ini_path):
        print(f"WARN: 小猫 INI not found at {ini_path}, skipping")
        return True

    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")

    errors = []
    pngseq_files = set(os.listdir(pngseq_dir)) if os.path.exists(pngseq_dir) else set()

    for section in cp.sections():
        # [action.X] sections
        if section.startswith("action."):
            action = section.split(".", 1)[1]
            prefix = cp.get(section, "asset_prefix", fallback="")
            frame_count_str = cp.get(section, "frame_count", fallback="")

            # Check that files exist with this prefix
            matching = [f for f in pngseq_files if f.startswith(prefix) and f.endswith(".c")]
            actual_count = len(matching)

            if actual_count == 0:
                errors.append(f"[小猫] [action.{action}]: no pngseq files found with prefix '{prefix}'")
                continue

            # Check frame_count matches
            if frame_count_str:
                expected = int(frame_count_str)
                if expected != actual_count:
                    errors.append(
                        f"[小猫] [action.{action}]: frame_count={expected} but actual pngseq files={actual_count}"
                    )

            # Check prefix matches actual files
            if prefix and not matching:
                errors.append(f"[小猫] [action.{action}]: asset_prefix='{prefix}' matches no files")

        # [part.X] sections
        elif section.startswith("part."):
            part_key = section.split(".", 1)[1]
            mapped = PART_NAME_MAP.get(part_key)
            if mapped is None:
                errors.append(f"[小猫] [part.{part_key}]: unknown part key, not in PART_NAME_MAP")

    # Check part mappings against actual meta.h
    if os.path.exists(meta_h):
        with open(meta_h, "r") as f:
            meta_content = f.read()
        for ini_key, meta_name in PART_NAME_MAP.items():
            if f"cat_C01_{meta_name}" not in meta_content and meta_name not in meta_content:
                errors.append(f"[小猫] [part.{ini_key}] → {meta_name}: not found in cat_parts_meta.h")

    if errors:
        print("小猫 INI validation FAILED:")
        for e in errors:
            print(f"  ❌ {e}")
        return False

    print("小猫 INI validation: OK")
    return True


def validate_forest_ini():
    ini_path = os.path.join(PROJECT_DIR, "config", "森林", "animation_config.ini")
    json_dir = os.path.join(PROJECT_DIR, "output", "森林", "json", "410_502")

    if not os.path.exists(ini_path):
        print(f"WARN: 森林 INI not found at {ini_path}, skipping")
        return True

    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")

    errors = []

    # [bg.global] must exist
    if "bg.global" not in cp.sections():
        errors.append("[森林] missing required section [bg.global]")

    # Collect all layer names from variant JSONs
    import json
    all_layer_names = set()
    if os.path.exists(json_dir):
        for fname in os.listdir(json_dir):
            if fname.endswith("_layers.json"):
                with open(os.path.join(json_dir, fname), "r") as f:
                    data = json.load(f)
                for l in data.get("layers", []):
                    all_layer_names.add(l["name"])

    if not all_layer_names:
        print(f"WARN: no layer JSONs found in {json_dir}, skipping layer name check")
    else:
        for section in cp.sections():
            if section.startswith("bg.") and section != "bg.global":
                layer_name = section.split(".", 1)[1]
                if layer_name not in all_layer_names:
                    errors.append(
                        f"[森林] [{section}]: layer '{layer_name}' not found in any variant JSON"
                    )

    if errors:
        print("森林 INI validation FAILED:")
        for e in errors:
            print(f"  ❌ {e}")
        return False

    print("森林 INI validation: OK")
    return True


def main():
    ok = True
    ok &= validate_cat_ini()
    ok &= validate_forest_ini()

    if not ok:
        print("\nVALIDATION FAILED — fix errors above before deploying to LVGL")
        return 1

    print("\nAll validations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

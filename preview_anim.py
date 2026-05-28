#!/usr/bin/env python3
"""TVCartoon 动画预览 — 逐帧播放 Spine 导出的 PNGS

用法:
  python3 preview_anim.py                           # Character01 全部动作
  python3 preview_anim.py --char Character05        # 指定角色
  python3 preview_anim.py --action Idle             # 指定动作
  python3 preview_anim.py --char Character01 --action Walk

控件:
  1-9   切换动作 (Dead/Fly/Hit/Idle/Jump/Roll/Stuned/Throwing/Walk)
  ← →   切换角色 (上/下一个 Character)
  Space 暂停/继续
  G     导出当前动作 GIF
  Q/ESC 退出
"""

import sys
import os
import glob
from pathlib import Path

PNG_DIR = "/Users/chansen2000/Downloads/素材/选择/小猫/Png"
ACTIONS = ["Dead", "Fly", "Hit", "Idle", "Jump", "Roll", "Stuned", "Throwing", "Walk"]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "previews")


def get_chars():
    dirs = sorted(d for d in os.listdir(PNG_DIR) if d.startswith("Character"))
    return dirs


def load_frames(char_dir, action):
    pattern = os.path.join(PNG_DIR, char_dir, action, "*.png")
    files = sorted(glob.glob(pattern))
    frames = []
    from PIL import Image
    for f in files:
        frames.append(Image.open(f).convert("RGBA"))
    return frames, files


def main():
    import argparse
    p = argparse.ArgumentParser(description="TVCartoon 动画预览")
    p.add_argument("--char", default="Character01")
    p.add_argument("--action", default=None)
    args = p.parse_args()

    chars = get_chars()
    if args.char not in chars:
        print(f"Unknown character: {args.char}. Available: {chars}")
        return
    char_idx = chars.index(args.char)
    action = args.action or "Idle"

    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title("TVCartoon Anim Preview")

    state = {"char_idx": char_idx, "action": action, "paused": False,
             "frame_i": 0, "frames": [], "img_obj": None}

    def load():
        frames, paths = load_frames(chars[state["char_idx"]], state["action"])
        state["frames"] = frames
        state["frame_i"] = 0
        title = f"{chars[state['char_idx']]} — {state['action']}  ({len(frames)} frames)"
        ax.set_title(title)
        print(f"Loaded: {title}")
        return frames

    load()

    if state["frames"]:
        state["img_obj"] = ax.imshow(state["frames"][0])
    ax.axis("off")
    fig.tight_layout()

    def update(_frame_num):
        if state["paused"] or not state["frames"]:
            return
        state["frame_i"] = (state["frame_i"] + 1) % len(state["frames"])
        state["img_obj"].set_array(state["frames"][state["frame_i"]])

    def on_key(event):
        k = event.key
        if k in ("q", "escape"):
            plt.close()
        elif k == " ":
            state["paused"] = not state["paused"]
            s = "PAUSED" if state["paused"] else "RUNNING"
            title = ax.get_title().rsplit("  [", 1)[0] + (f"  [{s}]" if state["paused"] else "")
            ax.set_title(title)
            fig.canvas.draw_idle()
        elif k == "left":
            state["char_idx"] = (state["char_idx"] - 1) % len(chars)
            state["frame_i"] = 0
            load()
            state["img_obj"] = ax.imshow(state["frames"][0])
            fig.canvas.draw_idle()
        elif k == "right":
            state["char_idx"] = (state["char_idx"] + 1) % len(chars)
            state["frame_i"] = 0
            load()
            state["img_obj"] = ax.imshow(state["frames"][0])
            fig.canvas.draw_idle()
        elif k in "123456789":
            idx = int(k) - 1
            if idx < len(ACTIONS):
                state["action"] = ACTIONS[idx]
                state["frame_i"] = 0
                load()
                state["img_obj"] = ax.imshow(state["frames"][0])
                fig.canvas.draw_idle()
        elif k == "g":
            if not state["frames"]:
                return
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            name = f"{chars[state['char_idx']]}_{state['action']}.gif"
            out = os.path.join(OUTPUT_DIR, name)
            frames = state["frames"]
            durations = [80] * len(frames)  # ~12.5 fps
            frames[0].save(out, save_all=True, append_images=frames[1:],
                           duration=durations, loop=0, disposal=2)
            print(f"GIF saved → {out}")

    fig.canvas.mpl_connect("key_press_event", on_key)

    # ~12.5 fps
    _ani = animation.FuncAnimation(fig, update, interval=80, cache_frame_data=False)

    print("Keys: 1-9=action  ←→=char  Space=pause  G=export GIF  Q=quit")
    plt.show()


if __name__ == "__main__":
    main()

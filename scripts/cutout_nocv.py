# -*- coding: utf-8 -*-
"""白底渐变抠图（numpy + PIL，BFS 连通域，不依赖 OpenCV）

用法：
  py cutout_nocv.py --input 原图.png --output out.png [--ai ai_cut.png] [--path-thr 100] [--white-val 249] [--preview]
"""
import argparse
from collections import deque

import numpy as np
from PIL import Image

CHECKER = 16


def make_checker(w, h, a=200, b=255):
    yy, xx = np.mgrid[0:h, 0:w]
    board = ((yy // CHECKER + xx // CHECKER) % 2).astype(np.uint8)
    out = np.empty((h, w, 3), np.uint8)
    out[board == 0] = a
    out[board == 1] = b
    return out


def bg_from_borders(path_mask):
    """从四边向内的 BFS，返回与边缘连通的路径区（bool）。"""
    h, w = path_mask.shape
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if path_mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append(y * w + x)
    for y in range(h):
        for x in (0, w - 1):
            if path_mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append(y * w + x)

    flat_mask = path_mask.ravel()
    flat_seen = seen.ravel()
    while q:
        i = q.popleft()
        y, x = divmod(i, w)
        if x + 1 < w:
            j = i + 1
            if flat_mask[j] and not flat_seen[j]:
                flat_seen[j] = True
                q.append(j)
        if x > 0:
            j = i - 1
            if flat_mask[j] and not flat_seen[j]:
                flat_seen[j] = True
                q.append(j)
        if y + 1 < h:
            j = i + w
            if flat_mask[j] and not flat_seen[j]:
                flat_seen[j] = True
                q.append(j)
        if y > 0:
            j = i - w
            if flat_mask[j] and not flat_seen[j]:
                flat_seen[j] = True
                q.append(j)
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--ai", default="")
    ap.add_argument("--path-thr", type=float, default=100.0)
    ap.add_argument("--white-val", type=float, default=249.0)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    im = Image.open(args.input).convert("RGBA")
    w, h = im.size
    arr = np.array(im).astype(np.float32)
    min_ch = arr[:, :, :3].min(axis=2)

    path_mask = min_ch > args.path_thr
    bg = bg_from_borders(path_mask)

    t = np.clip((args.white_val - min_ch) / (args.white_val - args.path_thr), 0, 1)
    alpha = np.where(bg, t * 255.0, 255.0)

    if args.ai:
        ai = np.array(Image.open(args.ai).convert("RGBA"))
        if ai.shape[:2] == (h, w):
            alpha = np.maximum(alpha, ai[:, :, 3].astype(np.float32))

    out = arr.copy()
    out[:, :, 3] = np.clip(alpha, 0, 255)
    Image.fromarray(out.astype(np.uint8), "RGBA").save(args.output)

    print("bg pixels: %.1f%%" % (bg.mean() * 100))
    print("alpha: transparent %.1f%% / semi %.1f%% / opaque %.1f%%" % (
        (alpha < 5).mean() * 100, ((alpha >= 5) & (alpha < 250)).mean() * 100, (alpha >= 250).mean() * 100))
    print("saved", args.output)

    if args.preview:
        checker = make_checker(w, h)
        a = (out[:, :, 3:4] / 255.0)
        comp = (out[:, :, :3] * a + checker * (1 - a)).astype(np.uint8)
        pv = args.output.replace(".png", "_preview.png")
        Image.fromarray(comp, "RGB").save(pv)
        print("preview", pv)


if __name__ == "__main__":
    main()

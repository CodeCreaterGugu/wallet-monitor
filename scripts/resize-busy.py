# -*- coding: utf-8 -*-
"""把 default 套 busy 缩到和 think 一样高（按实际绘制高度对齐）。"""
import os, sys
from PIL import Image

SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
WORK = r"C:\Users\21674\Desktop\待抠图\默认"
TARGET_H = 375


def draw_h(path):
    im = Image.open(path).convert("RGBA")
    bb = im.getbbox()
    return bb, im.size, (bb[3] - bb[1]) if bb else 0


print("--- 现状 ---")
think_bb, think_size, think_h = draw_h(os.path.join(SPR, "think.webp"))
busy_bb, busy_size, busy_h = draw_h(os.path.join(SPR, "busy.webp"))
print("think  canvas=%s 绘制高=%d" % (think_size, think_h))
print("busy   canvas=%s 绘制高=%d" % (busy_size, busy_h))

src = os.path.join(WORK, "busy.png")
if not os.path.exists(src):
    print("MISS 源图:", src)
    sys.exit(1)

im = Image.open(src).convert("RGBA")
bb = im.getbbox()
if bb:
    im = im.crop(bb)
print("源图 %s 裁切后=%s" % (os.path.basename(src), im.size))

h = think_h  # 和 think 实高完全一致
sc = h / im.height
im = im.resize((max(1, int(im.width * sc)), h), Image.LANCZOS)
canvas = Image.new("RGBA", (im.width, TARGET_H), (0, 0, 0, 0))
canvas.alpha_composite(im, (0, TARGET_H - h))
out = os.path.join(SPR, "busy.webp")
canvas.save(out, "WEBP", quality=88, method=4)
print("新 busy canvas=%s 绘制高=%d 字节=%d" % (canvas.size, h, os.path.getsize(out)))

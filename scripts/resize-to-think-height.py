# -*- coding: utf-8 -*-
"""把默认套 settle（坐在书堆上）缩到和 think 一样的实际绘制高度。"""
import os, sys
from PIL import Image

SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
WORK = r"C:\Users\21674\Desktop\待抠图\默认"
TARGET_H = 375
NAME = sys.argv[1] if len(sys.argv) > 1 else "settle"


def draw_h(path):
    im = Image.open(path).convert("RGBA")
    bb = im.getbbox()
    return im.size, (bb[3] - bb[1]) if bb else 0


think_size, think_h = draw_h(os.path.join(SPR, "think.webp"))
cur_size, cur_h = draw_h(os.path.join(SPR, NAME + ".webp"))
print("think canvas=%s 绘制高=%d" % (think_size, think_h))
print("%s  canvas=%s 绘制高=%d" % (NAME, cur_size, cur_h))
if cur_h == think_h:
    print("已经对齐，无需处理")
    sys.exit(0)

src = os.path.join(WORK, NAME + ".png")
if not os.path.exists(src):
    print("MISS 源图:", src)
    sys.exit(1)

im = Image.open(src).convert("RGBA")
bb = im.getbbox()
if bb:
    im = im.crop(bb)
sc = think_h / im.height
im = im.resize((max(1, int(im.width * sc)), think_h), Image.LANCZOS)
canvas = Image.new("RGBA", (im.width, TARGET_H), (0, 0, 0, 0))
canvas.alpha_composite(im, (0, TARGET_H - think_h))
out = os.path.join(SPR, NAME + ".webp")
canvas.save(out, "WEBP", quality=88, method=4)
print("新 %s canvas=%s 绘制高=%d 字节=%d" % (NAME, canvas.size, think_h, os.path.getsize(out)))

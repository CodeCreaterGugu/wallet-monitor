# -*- coding: utf-8 -*-
"""导入圣诞/和服的动作图：裁切 → 缩放到目标绘制高 → 375 画布底部对齐 → webp。"""
import os
import sys
from PIL import Image

SRC = r"C:\Users\21674\Desktop\待抠图\皮肤"
SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
CANVAS_H = 375

# 名称 → 缩放系数（1.0 = 满高；0.7787 = 和目标 292 一致）
JOBS = [
    ("christmas_idle", 1.0),
    ("christmas_talk", 1.0),
    ("christmas_busy", 0.7787),
    ("christmas_sleep", 1.0),
    ("yukata_idle", 1.0),
    ("yukata_talk", 1.0),
    ("yukata_busy", 0.7787),
    ("yukata_sleep", 1.0),
]

for name, factor in JOBS:
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        continue
    src = os.path.join(SRC, name + ".png")
    if not os.path.exists(src):
        print("MISS", src)
        continue
    im = Image.open(src).convert("RGBA")
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    h = int(CANVAS_H * factor)
    sc = h / im.height
    im = im.resize((max(1, int(im.width * sc)), h), Image.LANCZOS)
    if factor < 1.0:
        canvas = Image.new("RGBA", (im.width, CANVAS_H), (0, 0, 0, 0))
        canvas.alpha_composite(im, (0, CANVAS_H - h))
        im = canvas
    out = os.path.join(SPR, name + ".webp")
    im.save(out, "WEBP", quality=88, method=4)
    print("%-18s canvas=%s 绘制高=%3d  %6d B" % (name, im.size, h, os.path.getsize(out)))

print("done")

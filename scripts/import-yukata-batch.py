# -*- coding: utf-8 -*-
"""导入和服整套立绘：下蹲动作按比例缩小，settle 略缩，其余满高。"""
import glob
import os

from PIL import Image

SRC = r"C:\Users\21674\Desktop\待抠图\皮肤"
SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
CANVAS_H = 375

FACTORS = {
    "yukata_low": 0.75,      # 蹲坐抱膝
    "yukata_busy": 0.7787,   # 蹲着烤团子
    "yukata_think": 0.7787,  # 蹲着捧脸
    "yukata_settle": 0.90,   # 坐木廊，略缩
}

rows = []
for path in sorted(glob.glob(os.path.join(SRC, "yukata_*.png"))):
    name = os.path.splitext(os.path.basename(path))[0]
    factor = FACTORS.get(name, 1.0)
    im = Image.open(path).convert("RGBA")
    alpha_min = im.getchannel("A").getextrema()[0]
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
    rows.append((name, im.size, h, os.path.getsize(out), alpha_min))

for name, size, h, b, amin in rows:
    print("%-24s %-12s 绘制高=%3d %7d B  alphaMin=%d" % (name, "%dx%d" % size, h, b, amin))
print("导入 %d 张" % len(rows))

# -*- coding: utf-8 -*-
"""把待抠图里的 christmas_*.png 批量导入 sprites（按动作选择缩放系数）。"""
import glob
import os
from PIL import Image

SRC = r"C:\Users\21674\Desktop\待抠图\皮肤"
SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
CANVAS_H = 375

# 非站姿动作缩到 78%（绘制高 292），其余满高
FACTORS = {
    "christmas_busy": 0.7787,
    "christmas_settle": 0.7787,
    "christmas_think": 0.7787,
}

rows = []
for path in sorted(glob.glob(os.path.join(SRC, "christmas_*.png"))):
    name = os.path.splitext(os.path.basename(path))[0]
    # 跳过临时副本
    if name.endswith("_2"):
        continue
    factor = FACTORS.get(name, 1.0)
    im = Image.open(path).convert("RGBA")
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
    rows.append((name, im.size, h, os.path.getsize(out)))

for name, size, h, b in rows:
    print("%-24s %-12s 绘制高=%3d %7d B" % (name, "%dx%d" % size, h, b))
print("导入 %d 张" % len(rows))

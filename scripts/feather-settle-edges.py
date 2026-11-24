# -*- coding: utf-8 -*-
"""把边缘（含影子）改柔和收进画面：四周羽化到纯白，再整体缩小留白。"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = r"C:\Users\21674\.openclaw\media\tool-image-generation\christmas_settle_v4---1ac13e2a-d7f7-4946-bcac-c135a68c52af.png"
OUT_DIR = r"D:\AI生成\看图\圣诞"
OUT = os.path.join(OUT_DIR, "christmas_settle_v4_fixed.png")

im = Image.open(SRC).convert("RGB")
w, h = im.size

# 1) 边缘羽化蒙版：保留内部，四周 F 像素平滑过渡到 0
F = int(min(w, h) * 0.055)
mask = Image.new("L", (w, h), 0)
d = ImageDraw.Draw(mask)
d.rectangle([F, F, w - F, h - F], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(F))

white = Image.new("RGB", (w, h), (255, 255, 255))
feathered = Image.composite(im, white, mask)

# 2) 整体缩小 6%，居中放到纯白画布，保证不贴边
scale = 0.94
sw, sh = int(w * scale), int(h * scale)
small = feathered.resize((sw, sh), Image.LANCZOS)
canvas = Image.new("RGB", (w, h), (255, 255, 255))
canvas.paste(small, ((w - sw) // 2, (h - sh) // 2))

os.makedirs(OUT_DIR, exist_ok=True)
canvas.save(OUT)
print("saved", OUT, canvas.size, os.path.getsize(OUT))

# 3) 验收：检查四边是否都接近纯白
a = np.asarray(canvas).astype(int)
def edge(name, arr):
    print("%-6s mean=%s maxdiff=%d" % (name, arr.mean(0).round(0), int(np.abs(arr - 255).sum(1).max())))
edge("top", a[0])
edge("bottom", a[-1])
edge("left", a[:, 0])
edge("right", a[:, -1])

# -*- coding: utf-8 -*-
"""下午茶立绘：镜像 → 去白底 → 阴影保留为半透明 → 输出 PNG"""
import glob, os
from PIL import Image, ImageOps
from collections import deque

GEN = r"C:\Users\21674\.openclaw\media\tool-image-generation"
OUT_DIR = r"C:\Users\21674\Desktop\看图\问候"
os.makedirs(OUT_DIR, exist_ok=True)

hits = sorted(glob.glob(os.path.join(GEN, "base_greet_afternoon_tea---*.png")), key=os.path.getmtime)
src = hits[-1]
im = ImageOps.mirror(Image.open(src).convert("RGBA"))
w, h = im.size
px = im.load()

# 1) 从四角 floodfill 去掉纯白（容差内的连通白）
WHITE = 244
visited = bytearray(w * h)
q = deque()
for x in range(w):
    q.append((x, 0)); q.append((x, h - 1))
for y in range(h):
    q.append((0, y)); q.append((w - 1, y))

while q:
    x, y = q.popleft()
    if x < 0 or y < 0 or x >= w or y >= h:
        continue
    i = y * w + x
    if visited[i]:
        continue
    r, g, b, a = px[x, y]
    if r >= WHITE and g >= WHITE and b >= WHITE:
        visited[i] = 1
        px[x, y] = (r, g, b, 0)
        q.append((x + 1, y)); q.append((x - 1, y)); q.append((x, y + 1)); q.append((x, y - 1))

# 2) 阴影：中性灰像素（非纯白）→ 按亮度给半透明
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        mx, mn = max(r, g, b), min(r, g, b)
        if mx - mn <= 14 and 150 <= mx < WHITE:
            # 越暗越不透明，最淡的接近全透明
            alpha = int(max(0, min(200, (WHITE - mx) * 4.2)))
            px[x, y] = (int(r * 0.6), int(g * 0.6), int(b * 0.6), alpha)

out = os.path.join(OUT_DIR, "greet_afternoon_mirror.png")
im.save(out)
print("saved", out, im.size)

# 附加一张白底预览，方便看轮廓
prev = Image.new("RGBA", im.size, (255, 255, 255, 255))
prev.alpha_composite(im)
prev.convert("RGB").save(os.path.join(OUT_DIR, "greet_afternoon_mirror_预览.png"))
print("preview saved")

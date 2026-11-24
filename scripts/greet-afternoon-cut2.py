# -*- coding: utf-8 -*-
"""下午茶立绘：镜像 → 仅去白底（标准流程，不改阴影）→ 输出 PNG 给他手动修"""
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

# 轻微收边：去掉与透明相邻的近白像素，减少白边
for y in range(1, h - 1):
    for x in range(1, w - 1):
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        if r >= 238 and g >= 238 and b >= 238:
            if (px[x-1, y][3] == 0 or px[x+1, y][3] == 0 or px[x, y-1][3] == 0 or px[x, y+1][3] == 0):
                px[x, y] = (r, g, b, 0)

out = os.path.join(OUT_DIR, "greet_afternoon_cut.png")
im.save(out)
print("saved", out, im.size)

prev = Image.new("RGBA", im.size, (255, 255, 255, 255))
prev.alpha_composite(im)
prev.convert("RGB").save(os.path.join(OUT_DIR, "greet_afternoon_cut_白底预览.png"))
print("preview saved")

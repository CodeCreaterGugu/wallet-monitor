# -*- coding: utf-8 -*-
"""对指定四张：抠图 + 原图叠加，未被抠图覆盖的部分作为阴影补回，alpha=0.85。"""
import os
from collections import deque
from PIL import Image

SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
WORK = r"C:\Users\21674\Desktop\待抠图"

# (名称, 新抠图, 原图, 目标是否在 sprites 里的名字, 缩放系数)
JOBS = [
    ("idle", os.path.join(WORK, "默认", "idle.png"), r"D:\AI生成\看图\默认\01_idle.webp", "idle", 1.0),
    ("greet_afternoon", os.path.join(WORK, "默认", "greet_afternoon.png"), r"D:\AI生成\看图\问候\greet_afternoon_final.png", "greet_afternoon", 1.0),
    ("whale_think", os.path.join(WORK, "鲸鱼", "whale_think.png"), r"D:\AI生成\看图\鲸鱼\10_think.png", "whale_think", 0.686),
    ("whale_settle", os.path.join(WORK, "鲸鱼", "whale_settle.png"), r"D:\AI生成\看图\鲸鱼\06_settle.png", "whale_settle", 0.72),
]

SHADOW_ALPHA = int(255 * 0.85)


def normalize(path, height=375):
    """去白底 -> 裁边 -> 缩放到指定高度，返回 RGBA"""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
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
        if seen[i]:
            continue
        r, g, b, a = px[x, y]
        if r >= 244 and g >= 244 and b >= 244:
            seen[i] = 1
            px[x, y] = (r, g, b, 0)
            q.append((x + 1, y)); q.append((x - 1, y)); q.append((x, y + 1)); q.append((x, y - 1))
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    if height:
        sc = height / im.height
        im = im.resize((max(1, int(im.width * sc)), height), Image.LANCZOS)
    return im


for label, new_path, old_path, out_name, factor in JOBS:
    cut = Image.open(new_path).convert("RGBA")
    base = normalize(old_path, 375)

    # 尺寸对齐：以抠图为准
    if base.size != cut.size:
        base = base.resize(cut.size, Image.LANCZOS)

    w, h = cut.size
    cp, bp = cut.load(), base.load()

    shadow = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = cp[x, y]
            br, bg, bb_, ba = bp[x, y]
            # 原图有内容、抠图没有 -> 阴影
            if a == 0 and ba > 0:
                cp[x, y] = (br, bg, bb_, min(SHADOW_ALPHA, ba))
                shadow += 1

    # 按既定比例缩放（保持底部对齐）
    if factor < 1.0:
        nw, nh = int(w * factor), int(h * factor)
        small = cut.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (nw, 375), (0, 0, 0, 0))
        canvas.alpha_composite(small, (0, 375 - nh))
        cut = canvas

    out = os.path.join(SPR, out_name + ".webp")
    cut.save(out, "WEBP", quality=88, method=4)
    print("%-16s shadow_px=%-7d -> %s %s" % (label, shadow, out_name + ".webp", cut.size))

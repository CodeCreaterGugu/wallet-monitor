# -*- coding: utf-8 -*-
"""把看图里的鲸鱼 PNG 处理成 sprites/whale_*.webp（去白底 / 裁边 / 375 高）"""
import os
from collections import deque
from PIL import Image

SRC = r"D:\AI生成\看图\鲸鱼"
SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"

MAP = {
    "01_idle": "whale_idle",
    "02_talk": "whale_talk",
    "03_busy": "whale_busy",
    "04_cheer": "whale_cheer",
    "05_wave": "whale_wave",
    "06_settle": "whale_settle",
    "07_sleep": "whale_sleep",
    "08_low": "whale_low",
    "09_error": "whale_error",
    "10_think": "whale_think",
    "11_full": "whale_full",
    "12_pat_happy": "whale_pat_happy",
    "13_shy": "whale_shy",
    "15_stretch": "whale_stretch",
    "16_yawn": "whale_yawn",
    "17_greet_morning": "whale_greet_morning",
    "18_greet_night": "whale_greet_night",
    "19_scratch": "whale_scratch",
    "20_checkwatch": "whale_checkwatch",
    "21_angry": "whale_angry",
    "22_dizzy": "whale_dizzy",
    "23_drag": "whale_drag",
}

WHITE = 244


def cut(src, dst):
    im = Image.open(src).convert("RGBA")
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
        if r >= WHITE and g >= WHITE and b >= WHITE:
            seen[i] = 1
            px[x, y] = (r, g, b, 0)
            q.append((x + 1, y)); q.append((x - 1, y)); q.append((x, y + 1)); q.append((x, y - 1))
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    sc = 375.0 / im.height
    im = im.resize((max(1, int(im.width * sc)), 375), Image.LANCZOS)
    im.save(dst, "WEBP", quality=88, method=4)
    return im.size


done = 0
for key, target in MAP.items():
    src = os.path.join(SRC, key + ".png")
    if not os.path.exists(src):
        print("MISS", key)
        continue
    dst = os.path.join(SPR, target + ".webp")
    size = cut(src, dst)
    done += 1
    print("%-22s -> %-26s %s" % (key, target + ".webp", size))

print("done", done)

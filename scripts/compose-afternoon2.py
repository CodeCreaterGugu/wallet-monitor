# -*- coding: utf-8 -*-
"""按亮度提取阴影，把重叠区域改成半透明。"""
import glob, os
from PIL import Image

INBOX = r"C:\Users\21674\.openclaw\media\inbound"
DIR = r"C:\Users\21674\Desktop\看图\问候"
SHADOW = os.path.join(DIR, "greet_afternoon_shadow.png")
OUT = os.path.join(DIR, "greet_afternoon_final.png")
PREV = os.path.join(DIR, "greet_afternoon_final_白底预览.png")

char = Image.open(sorted(glob.glob(os.path.join(INBOX, "greet_afternoon_cut---*.png")), key=os.path.getmtime)[-1]).convert("RGBA")
shadow = Image.open(SHADOW).convert("RGB")
if shadow.size != char.size:
    shadow = shadow.resize(char.size, Image.LANCZOS)

w, h = char.size
cp = char.load()
sp = shadow.load()

# 阴影强度 = 255 - 亮度（白底=0），再放大一点让淡阴影也有效果
K = 0.85
changed = 0
for y in range(h):
    for x in range(w):
        r, g, b, a = cp[x, y]
        if a == 0:
            continue
        sr, sg, sb = sp[x, y]
        lum = (sr * 299 + sg * 587 + sb * 114) // 1000
        if lum >= 250:
            continue
        strength = min(255, (255 - lum) * 3)   # 240灰 → 45
        factor = 1 - K * (strength / 255.0)
        new_a = int(a * factor)
        if new_a < a:
            cp[x, y] = (r, g, b, new_a)
            changed += 1

# 清白边
cleaned = 0
for y in range(1, h - 1):
    for x in range(1, w - 1):
        r, g, b, a = cp[x, y]
        if a == 0:
            continue
        if r > 235 and g > 235 and b > 235:
            if cp[x-1, y][3] == 0 or cp[x+1, y][3] == 0 or cp[x, y-1][3] == 0 or cp[x, y+1][3] == 0:
                cp[x, y] = (r, g, b, 0)
                cleaned += 1

char.save(OUT)
prev = Image.new("RGBA", char.size, (255, 255, 255, 255))
prev.alpha_composite(char)
prev.convert("RGB").save(PREV)
print("shadow_pixels", changed, "white_cleaned", cleaned, "saved", OUT)

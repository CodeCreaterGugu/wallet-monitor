# -*- coding: utf-8 -*-
"""把人工抠好的阴影叠回人物图：重叠区域变半透明 + 清白边"""
import glob, os
from PIL import Image

INBOX = r"C:\Users\21674\.openclaw\media\inbound"
DIR = r"C:\Users\21674\Desktop\看图\问候"
SHADOW = os.path.join(DIR, "greet_afternoon_shadow.png")
OUT = os.path.join(DIR, "greet_afternoon_final.png")
PREV = os.path.join(DIR, "greet_afternoon_final_白底预览.png")

chars = sorted(glob.glob(os.path.join(INBOX, "greet_afternoon_cut---*.png")), key=os.path.getmtime)
char = Image.open(chars[-1]).convert("RGBA")
shadow = Image.open(SHADOW).convert("RGBA")

print("char", char.size, "shadow", shadow.size)
if shadow.size != char.size:
    shadow = shadow.resize(char.size, Image.LANCZOS)

w, h = char.size
cp = char.load()
sp = shadow.load()

# 1) 阴影叠回：阴影越浓 → 人物越透明（最浓处压到 35%）
K = 0.65
changed = 0
for y in range(h):
    for x in range(w):
        r, g, b, a = cp[x, y]
        if a == 0:
            continue
        sa = sp[x, y][3]
        if sa == 0:
            continue
        factor = 1 - K * (sa / 255.0)
        new_a = int(a * factor)
        if new_a < a:
            cp[x, y] = (r, g, b, new_a)
            changed += 1

# 2) 清边缘近白像素
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
print("shadow_pixels", changed, "white_cleaned", cleaned)
print("saved", OUT)

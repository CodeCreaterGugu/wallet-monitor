# -*- coding: utf-8 -*-
"""整理待抠图：已完成的圣诞图归档，保留尚未抠的。"""
import glob
import os
import shutil

SRC = r"C:\Users\21674\Desktop\待抠图\皮肤"
ARC = r"D:\AI生成\WalletCrab\02_素材\已抠图\christmas"
os.makedirs(ARC, exist_ok=True)

# 这两张是刚出的，可能还没抠，留在原处
KEEP = {"christmas_cheer.png", "christmas_wave.png"}

moved = []
for p in sorted(glob.glob(os.path.join(SRC, "christmas_*.png"))):
    name = os.path.basename(p)
    if name in KEEP:
        continue
    shutil.move(p, os.path.join(ARC, name))
    moved.append(name)

print("归档 %d 张到 %s" % (len(moved), ARC))
for n in moved:
    print("  -", n)

print("\n留在待抠图：")
for n in sorted(os.listdir(SRC)):
    p = os.path.join(SRC, n)
    if os.path.isfile(p):
        print("  ", n)

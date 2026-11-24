# -*- coding: utf-8 -*-
"""把 sprites 里所有在用的立绘（除缩略图/三视图）导出为 PNG，按组放到桌面待抠图。"""
import glob, os
from PIL import Image

SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
OUT = r"C:\Users\21674\Desktop\待抠图"
os.makedirs(OUT, exist_ok=True)

groups = {"默认": [], "鲸鱼": [], "皮肤": []}

for f in sorted(glob.glob(os.path.join(SPR, "*.webp"))):
    name = os.path.splitext(os.path.basename(f))[0]
    if name.startswith("skinprev_"):
        continue
    if name.startswith("whale_"):
        groups["鲸鱼"].append(f)
    elif name in ("christmas", "whale", "newyear"):
        groups["皮肤"].append(f)
    else:
        groups["默认"].append(f)

total = 0
for g, files in groups.items():
    d = os.path.join(OUT, g)
    os.makedirs(d, exist_ok=True)
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        im = Image.open(f).convert("RGBA")
        im.save(os.path.join(d, name + ".png"))
        total += 1
    print(g, len(files))

README = """待抠图 · 使用说明
====================

结构
  默认\   基础套装动作图 + 问候图
  鲸鱼\   鲸鱼套装动作图（whale_xxx）
  皮肤\   各套装待机图（whale / christmas / newyear）

要求
  1) 文件名不要改，也不要改大小比例
  2) 输出 PNG，保留透明通道（RGBA）
  3) 阴影按你之前的方法：要么保透明，要么留半透明
  4) 抠完直接放回对应子文件夹（同名覆盖）

我拿到后会
  - 按原尺寸校正到 375 高
  - 转回 webp（quality 88）
  - 覆盖 sprites\\ 里的原文件
  - build 后你重启即可看到

注意
  不要动 sprites 目录，也不要碰三视图（turnaround）文件。
"""
open(os.path.join(OUT, "使用说明.txt"), "w", encoding="utf-8").write(README)
print("total", total, "->", OUT)

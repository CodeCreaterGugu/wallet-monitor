# -*- coding: utf-8 -*-
"""把用户抠好的图批量导入 sprites（按规则跳过默认的 idle / greet_afternoon）。"""
import glob, os
from PIL import Image

WORK = r"C:\Users\21674\Desktop\待抠图"
SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"

SKIP = {("默认", "idle"), ("默认", "greet_afternoon")}

FACTORS = {
    "whale_busy": 0.686,
    "whale_think": 0.686,
    "whale_settle": 0.72,
    "whale_sleep": 0.75,
    "whale_drag": 0.95,
    "think": 0.78,
    "busy": 0.7787,   /* 292/375：和 think 实高对齐 */
    "settle": 0.7787, /* 坐在书堆上，同高 */
}


def prepare(path, target_h, factor=1.0):
    im = Image.open(path).convert("RGBA")
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    h = int(target_h * factor)
    sc = h / im.height
    im = im.resize((max(1, int(im.width * sc)), h), Image.LANCZOS)
    if factor < 1.0:
        canvas = Image.new("RGBA", (im.width, target_h), (0, 0, 0, 0))
        canvas.alpha_composite(im, (0, target_h - h))
        im = canvas
    return im


jobs = []
for group in ("默认", "鲸鱼", "皮肤", "全天问候"):
    for f in sorted(glob.glob(os.path.join(WORK, group, "*.png"))):
        name = os.path.splitext(os.path.basename(f))[0]
        if (group, name) in SKIP:
            print("skip", group, name)
            continue
        jobs.append((group, name, f, 375, FACTORS.get(name, 1.0)))

for f in sorted(glob.glob(os.path.join(WORK, "缩略图", "skinprev_*.png"))):
    name = os.path.splitext(os.path.basename(f))[0]
    jobs.append(("缩略图", name, f, 260, 1.0))

count = 0
for group, name, path, h, factor in jobs:
    im = prepare(path, h, factor)
    out = os.path.join(SPR, name + ".webp")
    im.save(out, "WEBP", quality=88, method=4)
    count += 1
    print("%-10s %-22s -> %s %s" % (group, name, name + ".webp", im.size))

print("imported", count)

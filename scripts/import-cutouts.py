# -*- coding: utf-8 -*-
"""把用户抠好的图直接转成 sprites（不做阴影合成）。"""
import glob, os
from PIL import Image

SPR = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\sprites"
WORK = r"C:\Users\21674\Desktop\待抠图"

# 这些已经单独处理过（含阴影合成），跳过
DONE = {("默认", "idle"), ("默认", "greet_afternoon"), ("鲸鱼", "whale_think"), ("鲸鱼", "whale_settle")}

# 非站姿需要缩小（内容高度占 375 的比例）
FACTORS = {
    "whale_sleep": 0.75,
    "whale_drag": 0.95,
    "whale_busy": 0.686,
}

count = 0
for group in ("默认", "鲸鱼"):
    for f in sorted(glob.glob(os.path.join(WORK, group, "*.png"))):
        name = os.path.splitext(os.path.basename(f))[0]
        if (group, name) in DONE:
            continue
        im = Image.open(f).convert("RGBA")

        # 统一高度 375（若本来不是）
        if im.height != 375:
            sc = 375.0 / im.height
            im = im.resize((max(1, int(im.width * sc)), 375), Image.LANCZOS)

        factor = FACTORS.get(name, 1.0)
        if factor < 1.0:
            nw, nh = int(im.width * factor), int(im.height * factor)
            small = im.resize((nw, nh), Image.LANCZOS)
            canvas = Image.new("RGBA", (nw, 375), (0, 0, 0, 0))
            canvas.alpha_composite(small, (0, 375 - nh))
            im = canvas

        out = os.path.join(SPR, name + ".webp")
        im.save(out, "WEBP", quality=88, method=4)
        count += 1
        print("%-24s -> %s %s" % (os.path.join(group, name + ".png"), name + ".webp", im.size))

print("converted", count)

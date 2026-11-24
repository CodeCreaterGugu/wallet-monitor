# -*- coding: utf-8 -*-
"""1) 镜像 talk_v2 并替换 02_talk.png  2) 每套早晚安各加一句"""
import io, os, re, glob
from PIL import Image, ImageOps

GEN = r"C:\Users\21674\.openclaw\media\tool-image-generation"
DEST = r"C:\Users\21674\Desktop\看图\鲸鱼"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"

# ---------- 1. 镜像 talk ----------
hits = sorted(glob.glob(os.path.join(GEN, "wm_whale_talk_v2---*.png")), key=os.path.getmtime)
if hits:
    src = hits[-1]
    im = Image.open(src)
    flipped = ImageOps.mirror(im)
    out = os.path.join(DEST, "02_talk.png")
    flipped.save(out)
    print("mirrored ->", out, flipped.size)
else:
    print("talk_v2 not found")

# ---------- 2. 早晚安各加一句 ----------
EXTRA = {
    "none": {"greet_morning": "别趴着看屏幕。", "greet_night": "灯关了吧，我替你看余额。"},
    "christmas": {"greet_morning": "先吃点热的。", "greet_night": "雪夜的灯，记得关。"},
    "whale": {"greet_morning": "早。今天也别太用力。", "greet_night": "夜深了。我在这儿。"},
    "yukata": {"greet_morning": "早安，今天风小。", "greet_night": "夜里凉，披件外套。"},
}

for skin, kinds in EXTRA.items():
    p = os.path.join(D, "lines-%s.txt" % skin)
    lines = io.open(p, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    out, cur = [], None
    pending = dict(kinds)
    for ln in lines:
        m = re.match(r"^\[([^\]]+)\]$", ln.strip())
        if m:
            cur = m.group(1)
        # 在进入下一个段落/注释前，补上上一段
        if (m or ln.strip().startswith("#")) and pending:
            for k in list(pending):
                if "%s.%s" % (skin, k) == cur or True:
                    pass
        out.append(ln)

    # 简化：逐段重建——按段落收集，补句后输出
    text = io.open(p, encoding="utf-8").read().replace("\r\n", "\n")
    for kind, extra in kinds.items():
        marker = "[%s.%s]" % (skin, kind)
        if marker not in text:
            print("MISS", marker)
            continue
        if extra in text:
            continue
        # 找到该段起始，插入到该段最后一条台词之后（即下一个 "[" 或 "#" 之前）
        start = text.index(marker) + len(marker)
        rest = text[start:]
        m2 = re.search(r"\n\[|\n#", rest)
        insert_at = start + (m2.start() if m2 else len(rest))
        text = text[:insert_at].rstrip("\n") + "\n" + extra + text[insert_at:]
        print("added to", marker, "->", extra)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)

# -*- coding: utf-8 -*-
"""补中午/下午问候段落。"""
import io, os

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"

GREET = {
    "none": {
        "greet_noon": ["中午了，吃饭了吗？", "午休一下，别硬撑。", "这个点余额不用盯太紧。"],
        "greet_afternoon": ["下午好。", "下午容易犯困，喝点水。", "还有半天，慢慢来。"],
    },
    "christmas": {
        "greet_noon": ["中午了，先吃点热的。", "雪天里热汤最舒服。", "午休一会儿吧。"],
        "greet_afternoon": ["下午好，天又暗得快了。", "下午冷，加件外套。", "天快黑了，早点收工。"],
    },
    "whale": {
        "greet_noon": ["中午了。太阳最毒的时候。", "这会儿水里凉快。", "吃饭了吗。"],
        "greet_afternoon": ["下午好。", "下午的潮还没退。", "别一直盯着屏幕。"],
    },
    "yukata": {
        "greet_noon": ["中午好，日头有点大。", "找个阴凉处歇一会儿。", "吃饭了吗？"],
        "greet_afternoon": ["下午好，风起来了。", "下午适合慢慢逛。", "天还亮，别急着回。"],
    },
}

for skin, kinds in GREET.items():
    p = os.path.join(D, "lines-%s.txt" % skin)
    t = io.open(p, encoding="utf-8").read().rstrip("\n")
    if "[%s.greet_noon]" % skin in t:
        print("skip", skin)
        continue
    block = ["\n"]
    for kind, lines in kinds.items():
        block.append("[%s.%s]" % (skin, kind))
        block.extend(lines)
        block.append("")
    io.open(p, "w", encoding="utf-8", newline="\n").write(t + "\n" + "\n".join(block).rstrip("\n") + "\n")
    print("updated", p)

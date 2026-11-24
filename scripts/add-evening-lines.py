# -*- coding: utf-8 -*-
"""补晚上好（18:00-22:59）问候段落。"""
import io, os

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"

EVENING = {
    "none": ["晚上好。今天辛苦了。", "晚饭吃了吗？", "晚上别熬太晚。"],
    "christmas": ["晚上好，灯都亮了。", "晚饭吃点热的。", "雪夜早点休息。"],
    "whale": ["晚上好。", "夜里水更凉。", "别熬，明天还要出门。"],
    "yukata": ["晚上好，灯挂起来了。", "夜里风凉。", "早点歇，明天还有集市。"],
}

for skin, lines in EVENING.items():
    p = os.path.join(D, "lines-%s.txt" % skin)
    t = io.open(p, encoding="utf-8").read().rstrip("\n")
    if "[%s.greet_evening]" % skin in t:
        print("skip", skin)
        continue
    block = "\n[%s.greet_evening]\n%s\n" % (skin, "\n".join(lines))
    io.open(p, "w", encoding="utf-8", newline="\n").write(t + block)
    print("updated", p)

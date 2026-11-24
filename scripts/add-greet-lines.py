# -*- coding: utf-8 -*-
"""给四套服装的台词文件补上问候语段落。"""
import io, os

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"

GREET = {
    "none": {
        "greet_morning": ["早。书看完了吗？", "早上好，先喝口水。", "新的一天，余额还够。"],
        "greet_night": ["这么晚了，还不睡？", "夜里看书伤眼睛。", "晚安，我盯着余额。"],
    },
    "christmas": {
        "greet_morning": ["早上好，雪还没化。", "早，先暖暖手。", "今天也要省着花哦。"],
        "greet_night": ["晚安，记得关灯。", "这么晚还不睡，礼物我替你留着。", "夜里冷，盖好被子。"],
    },
    "whale": {
        "greet_morning": ["早。潮水退了。", "醒了？海面很平。", "这个点，水里最暖。"],
        "greet_night": ["这个点还不睡。", "夜深了，别熬。", "晚安。有事叫我。"],
    },
    "yukata": {
        "greet_morning": ["早上好，风很凉。", "早，木屐已经摆好了。", "今天也慢慢走。"],
        "greet_night": ["花火散了，早点休息。", "这么晚，路上小心。", "晚安，明天还有祭典。"],
    },
}

for skin, kinds in GREET.items():
    p = os.path.join(D, "lines-%s.txt" % skin)
    t = io.open(p, encoding="utf-8").read().rstrip("\n")
    if "[%s.greet_morning]" % skin in t:
        print("skip", skin, "(already has greet)")
        continue
    block = ["\n", "# -------------------- 问候 --------------------"]
    for kind, lines in kinds.items():
        block.append("[%s.%s]" % (skin, kind))
        block.extend(lines)
        block.append("")
    io.open(p, "w", encoding="utf-8", newline="\n").write(t + "\n" + "\n".join(block).rstrip("\n") + "\n")
    print("updated", p)

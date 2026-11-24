# -*- coding: utf-8 -*-
"""检查鲸鱼五段问候是否已有 cus_{皮肤}_{hash}.mp3 音频。"""
import io, os

PLUG = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
VOICE = os.path.join(PLUG, "voice")
TXT = os.path.join(PLUG, "lines-whale.txt")


def fnv1a(text: str) -> str:
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


secs = {}
cur = None
for raw in io.open(TXT, encoding="utf-8").read().splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("[") and line.endswith("]"):
        cur = line[1:-1]
        secs[cur] = []
        continue
    if cur and cur.startswith("whale.greet"):
        secs[cur].append(line)

missing = []
total = 0
for key in ["whale.greet_morning", "whale.greet_noon", "whale.greet_afternoon", "whale.greet_evening", "whale.greet_night"]:
    lines = secs.get(key, [])
    print("== %s (%d 句)" % (key, len(lines)))
    kind = key.split(".", 1)[1]
    for i, ln in enumerate(lines, 1):
        total += 1
        h = fnv1a(ln)
        cus = "cus_whale_%s.mp3" % h
        seq = "line_whale_%s_%d.mp3" % (kind, i)
        has_cus = os.path.exists(os.path.join(VOICE, cus))
        has_seq = os.path.exists(os.path.join(VOICE, seq))
        print("   %-28s cus=%s seq=%s" % (ln, "OK" if has_cus else "-", "OK" if has_seq else "-"))
        if not has_cus and not has_seq:
            missing.append((kind, i, ln, cus))

print("\n共 %d 句，缺音频 %d 句" % (total, len(missing)))
for m in missing:
    print("MISS", m[0], m[1], m[2], "->", m[3])

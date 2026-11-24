# -*- coding: utf-8 -*-
"""把四套的 done 台词改成「任务完成啦～」，并按各自音色重新合成。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
TEXT = "任务完成啦～"
MODEL = "speech-2.8-hd"
SPEED = 1.15
HQ = (32000, 128000)
LQ = (24000, 32000)
LQ_THRESHOLD = 45000

SKINS = {
    "none": ("female-shaonv", "done"),
    "christmas": ("Chinese (Mandarin)_Sweet_Lady", "christmas_done"),
    "whale": ("female-yujie-jingpin", "whale_done"),
    "yukata": ("female-tianmei-jingpin", "yukata_done"),
}

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}


def tts(voice, sr, br, tries=3):
    for _ in range(tries):
        body = {
            "model": MODEL,
            "text": TEXT,
            "stream": False,
            "voice_setting": {"voice_id": voice, "speed": SPEED, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": sr, "bitrate": br, "format": "mp3"},
        }
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST", headers=HDRS)
            r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
            a = (r.get("data") or {}).get("audio")
            if a:
                return bytes.fromhex(a)
        except Exception:
            pass
        time.sleep(1.5)
    return b""


# 1) 改 txt
for skin in SKINS:
    p = os.path.join(D, "lines-%s.txt" % skin)
    t = io.open(p, encoding="utf-8").read()
    marker = "[%s.done]" % skin
    if marker in t:
        start = t.index(marker) + len(marker)
        rest = t[start:]
        m2 = re.search(r"\n\[|\n#", rest)
        end = start + (m2.start() if m2 else len(rest))
        t = t[:start] + "\n" + TEXT + "\n" + t[end:]
        io.open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("txt updated:", skin)

# 2) 合成
for skin, (voice, base) in SKINS.items():
    hq = tts(voice, *HQ)
    if not hq:
        print("FAIL", skin)
        continue
    io.open(os.path.join(OUT, base + ".mp3"), "wb").write(hq)
    note = ""
    if len(hq) > LQ_THRESHOLD:
        low = tts(voice, *LQ)
        if low:
            io.open(os.path.join(OUT, base + "_lq.mp3"), "wb").write(low)
            note = " lq=%dB" % len(low)
    print("OK %-9s %s %dB%s" % (skin, base, len(hq), note))
    time.sleep(0.4)

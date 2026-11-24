# -*- coding: utf-8 -*-
"""只重做圣诞 / 和服的语音，语速 1.0（比鲸鱼的 1.15 慢）。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
MODEL = "speech-2.8-hd"
SPEED = 1.0
HQ = (32000, 128000)
LQ = (24000, 32000)
LQ_THRESHOLD = 45000

SKINS = {
    "christmas": "Chinese (Mandarin)_Sweet_Lady",
    "yukata": "female-tianmei-jingpin",
}
SYS = ["done", "full", "sad", "panel_low", "panel_high"]

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}


def fnv(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")


def tts(text, voice, sr, br, tries=3):
    for _ in range(tries):
        body = {
            "model": MODEL, "text": text, "stream": False,
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


ok = fail = 0
for skin, voice in SKINS.items():
    path = os.path.join(D, "lines-%s.txt" % skin)
    sec, data = None, {}
    for ln in io.open(path, encoding="utf-8"):
        s = ln.strip()
        m = re.match(r"^\[([^\]]+)\]$", s)
        if m:
            sec = m.group(1)
            continue
        if sec and s and not s.startswith("#"):
            data.setdefault(sec, []).append(s)

    print("===", skin, "===")
    for kind in ["pat", "angry", "legs", "dizzy"]:
        for i, text in enumerate(data.get("%s.%s" % (skin, kind), []), 1):
            for base in ("line_%s_%s_%d" % (skin, kind, i), "cus_%s_%s" % (skin, fnv(text))):
                hq = tts(text, voice, *HQ)
                if hq:
                    io.open(os.path.join(OUT, base + ".mp3"), "wb").write(hq)
                    if len(hq) > LQ_THRESHOLD:
                        low = tts(text, voice, *LQ)
                        if low:
                            io.open(os.path.join(OUT, base + "_lq.mp3"), "wb").write(low)
                    ok += 1
                else:
                    fail += 1
                time.sleep(0.2)

    for kind in SYS:
        lines = data.get("%s.%s" % (skin, kind), [])
        if not lines:
            continue
        base = ("line_%s_%s" % (skin, kind)) if kind.startswith("panel") else ("%s_%s" % (skin, kind))
        hq = tts(lines[0], voice, *HQ)
        if hq:
            io.open(os.path.join(OUT, base + ".mp3"), "wb").write(hq)
            ok += 1
        else:
            fail += 1
        time.sleep(0.2)

print("ok", ok, "fail", fail)

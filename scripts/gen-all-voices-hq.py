# -*- coding: utf-8 -*-
"""所有皮肤语音：32kHz/128kbps，超过 45KB 额外生成 _lq 备用。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
MODEL = "speech-2.8-hd"
SPEED = 1.15
HQ = (32000, 128000)
LQ = (24000, 32000)
LQ_THRESHOLD = 45000

SKINS = {
    "whale": "female-yujie-jingpin",
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
            "model": MODEL,
            "text": text,
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
        time.sleep(1.6)
    return b""


def save(text, voice, base_name):
    hq = tts(text, voice, *HQ)
    if not hq:
        return 0, 0
    io.open(os.path.join(OUT, base_name + ".mp3"), "wb").write(hq)
    lq = 0
    if len(hq) > LQ_THRESHOLD:
        low = tts(text, voice, *LQ)
        if low:
            io.open(os.path.join(OUT, base_name + "_lq.mp3"), "wb").write(low)
            lq = len(low)
    return len(hq), lq


ok = fail = 0
for skin, voice in SKINS.items():
    path = os.path.join(D, "lines-%s.txt" % skin)
    if not os.path.exists(path):
        print("NO FILE", path)
        continue
    sec, data = None, {}
    for ln in io.open(path, encoding="utf-8"):
        s = ln.strip()
        m = re.match(r"^\[([^\]]+)\]$", s)
        if m:
            sec = m.group(1)
            continue
        if sec and s and not s.startswith("#"):
            data.setdefault(sec, []).append(s)

    print("=== %s (%s) ===" % (skin, voice))
    for kind in ["pat", "angry", "legs", "dizzy"]:
        for i, text in enumerate(data.get("%s.%s" % (skin, kind), []), 1):
            a, b = save(text, voice, "line_%s_%s_%d" % (skin, kind, i))
            c, d = save(text, voice, "cus_%s_%s" % (skin, fnv(text)))
            if a:
                ok += 2
            else:
                fail += 2
            print("  %-6s %d hq=%dB  %s" % (kind, i, a, text))
            time.sleep(0.25)

    for kind in SYS:
        lines = data.get("%s.%s" % (skin, kind), [])
        if not lines:
            continue
        if kind in ("panel_low", "panel_high"):
            base = "line_%s_%s" % (skin, kind)
        else:
            base = "%s_%s" % (skin, kind)
        a, b = save(lines[0], voice, base)
        if a:
            ok += 1
        else:
            fail += 1
        print("  sys %-10s hq=%dB  %s" % (kind, a, lines[0]))
        time.sleep(0.25)

print("DONE ok=%d fail=%d" % (ok, fail))

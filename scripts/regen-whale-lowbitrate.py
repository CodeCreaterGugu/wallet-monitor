# -*- coding: utf-8 -*-
"""按低码率重新合成鲸鱼语音，避免 invoke 返回体积超限。"""
import io, json, os, re, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
SKIN = "whale"
TXT = os.path.join(D, "lines-%s.txt" % SKIN)
VOICE = "female-yujie-jingpin"
MODEL = "speech-2.8-hd"
SPEED = 1.15
SAMPLE_RATE = 24000
BITRATE = 32000

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


sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)


def synth(text, path):
    body = {
        "model": MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": VOICE, "speed": SPEED, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": SAMPLE_RATE, "bitrate": BITRATE, "format": "mp3"},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST", headers=HDRS)
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
    audio = (r.get("data") or {}).get("audio")
    if not audio:
        return 0
    raw = bytes.fromhex(audio)
    io.open(path, "wb").write(raw)
    return len(raw)


total = 0
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("%s.%s" % (SKIN, kind), []), 1):
        seq = os.path.join(OUT, "line_%s_%s_%d.mp3" % (SKIN, kind, i))
        cus = os.path.join(OUT, "cus_%s_%s.mp3" % (SKIN, fnv(text)))
        a = synth(text, seq)
        b = synth(text, cus)
        total += 2
        print("%-8s %d  seq=%dB cus=%dB  %s" % (kind, i, a, b, text))

SYS = {
    "done": "whale_done.mp3",
    "full": "whale_full.mp3",
    "sad": "whale_sad.mp3",
    "panel_low": "line_whale_panel_low.mp3",
    "panel_high": "line_whale_panel_high.mp3",
}
for kind, fname in SYS.items():
    lines = data.get("%s.%s" % (SKIN, kind), [])
    if not lines:
        continue
    n = synth(lines[0], os.path.join(OUT, fname))
    total += 1
    print("%-8s %s %dB  %s" % (kind, fname, n, lines[0]))

print("done", total)

# -*- coding: utf-8 -*-
import io, json, os, re, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
SKIN = "whale"
TXT = os.path.join(D, "lines-%s.txt" % SKIN)
VOICE = "female-yujie-jingpin"
MODEL = "speech-2.8-hd"
SPEED = 1.15
KINDS = ["pat", "angry", "legs", "dizzy"]

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

made, skipped = 0, 0
for kind in KINDS:
    for text in data.get("%s.%s" % (SKIN, kind), []):
        h = fnv(text)
        name = "cus_%s_%s.mp3" % (SKIN, h)
        path = os.path.join(OUT, name)
        if os.path.exists(path):
            skipped += 1
            print("SKIP", name, "exists")
            continue
        body = {
            "model": MODEL,
            "text": text,
            "stream": False,
            "voice_setting": {"voice_id": VOICE, "speed": SPEED, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
        }
        req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST", headers=HDRS)
        r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
        audio = (r.get("data") or {}).get("audio")
        if not audio:
            print("FAIL", name, str((r.get("base_resp") or {}).get("status_msg"))[:60])
            continue
        io.open(path, "wb").write(bytes.fromhex(audio))
        made += 1
        print("OK", name, text)

print("made", made, "skipped", skipped)

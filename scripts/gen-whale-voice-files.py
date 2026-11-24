# -*- coding: utf-8 -*-
import io, json, os, re, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
TXT = os.path.join(D, "lines-whale.txt")
OUT = os.path.join(D, "voice")
os.makedirs(OUT, exist_ok=True)

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}

VOICE = "female-yujie-jingpin"
MODEL = "speech-2.8-hd"
SPEED = 1.15

# 解析 whale 段落
sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)

DIALOG = ["pat", "angry", "legs", "dizzy"]
SYSTEM = ["done", "full", "sad", "panel_low", "panel_high"]


def synth(text, path):
    body = {
        "model": MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": VOICE, "speed": SPEED, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST", headers=HDRS)
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
    h = (r.get("data") or {}).get("audio")
    if not h:
        return 0, str((r.get("base_resp") or {}).get("status_msg"))[:60]
    raw = bytes.fromhex(h)
    io.open(path, "wb").write(raw)
    return len(raw), ""


count = 0
for kind in DIALOG:
    lines = data.get("whale." + kind, [])
    for i, text in enumerate(lines, 1):
        p = os.path.join(OUT, "line_whale_%s_%d.mp3" % (kind, i))
        size, err = synth(text, p)
        if size:
            count += 1
            print("OK line_whale_%s_%d  %d  %s" % (kind, i, size, text))
        else:
            print("FAIL line_whale_%s_%d %s" % (kind, i, err))

for kind in SYSTEM:
    lines = data.get("whale." + kind, [])
    if not lines:
        print("SKIP %s (no text)" % kind)
        continue
    text = lines[0]
    p = os.path.join(OUT, "whale_%s.mp3" % kind)
    size, err = synth(text, p)
    if size:
        count += 1
        print("OK whale_%s  %d  %s" % (kind, size, text))
    else:
        print("FAIL whale_%s %s" % (kind, err))

print("DONE", count, "files")

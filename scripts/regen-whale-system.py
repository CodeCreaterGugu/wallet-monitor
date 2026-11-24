# -*- coding: utf-8 -*-
import io, json, os, re, time, urllib.request, urllib.error

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
TXT = os.path.join(D, "lines-whale.txt")
VOICE = "female-yujie-jingpin"
MODEL = "speech-2.8-hd"
SPEED = 1.15

cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")
PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"
HDRS = {"Authorization": PREFIX + key, "Content-Type": "application/json"}

sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)

TARGETS = [
    ("whale.full", "whale_full.mp3"),
    ("whale.sad", "whale_sad.mp3"),
    ("whale.panel_low", "line_whale_panel_low.mp3"),
    ("whale.panel_high", "line_whale_panel_high.mp3"),
]


def synth(text, path, tries=4):
    for i in range(tries):
        body = {
            "model": MODEL,
            "text": text,
            "stream": False,
            "voice_setting": {"voice_id": VOICE, "speed": SPEED, "vol": 1.0, "pitch": 0},
            "audio_setting": {"sample_rate": 24000, "bitrate": 32000, "format": "mp3"},
        }
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"), method="POST", headers=HDRS)
            r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
            br = r.get("base_resp") or {}
            audio = (r.get("data") or {}).get("audio")
            if audio:
                raw = bytes.fromhex(audio)
                io.open(path, "wb").write(raw)
                return len(raw)
            print("  retry", i + 1, br.get("status_code"), str(br.get("status_msg"))[:60])
        except Exception as e:
            print("  retry", i + 1, type(e).__name__, str(e)[:60])
        time.sleep(2.0)
    return 0


for key_name, fname in TARGETS:
    lines = data.get(key_name, [])
    if not lines:
        print("SKIP", key_name)
        continue
    n = synth(lines[0], os.path.join(OUT, fname))
    print(("OK  " if n else "FAIL") + " %-24s %6dB  %s" % (fname, n, lines[0]))
    time.sleep(1.0)

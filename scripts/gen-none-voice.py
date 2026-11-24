# -*- coding: utf-8 -*-
"""生成默认套装(none)的语音：互动 18 句 + 系统 5 句，24kHz/32kbps。"""
import io, json, os, re, time, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
TXT = os.path.join(D, "lines-none.txt")
VOICE = "female-shaonv"
MODEL = "speech-2.8-hd"
SPEED = 1.15

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


def synth(text, path, tries=3):
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
            audio = (r.get("data") or {}).get("audio")
            if audio:
                raw = bytes.fromhex(audio)
                io.open(path, "wb").write(raw)
                return len(raw)
        except Exception:
            pass
        time.sleep(1.5)
    return 0


made = 0
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("none." + kind, []), 1):
        seq = os.path.join(OUT, "line_%s_%d.mp3" % (kind, i))
        cus = os.path.join(OUT, "cus_%s.mp3" % fnv(text))
        a = synth(text, seq)
        b = synth(text, cus)
        if a:
            made += 1
        time.sleep(0.4)
        print("%-6s %d  seq=%dB cus=%dB  %s" % (kind, i, a, b, text))

SYS = {
    "none.done": "done.mp3",
    "none.full": "full.mp3",
    "none.sad": "sad.mp3",
    "none.panel_low": "line_panel_low.mp3",
    "none.panel_high": "line_panel_high.mp3",
}
for k, fname in SYS.items():
    lines = data.get(k, [])
    if not lines:
        continue
    n = synth(lines[0], os.path.join(OUT, fname))
    if n:
        made += 1
    time.sleep(0.4)
    print("%-14s %s %dB  %s" % (k, fname, n, lines[0]))

print("done", made)

import io, json, os, urllib.request

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
OUT = r"C:\Users\21674\Desktop\看图\音色试听\鲸鱼批量"
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

LINES = [
    ("idle1", "来了？余额我盯着，你忙你的。"),
    ("idle2", "水凉。别把手伸进来。"),
    ("idle3", "帽子是我的，别碰。"),
    ("pat", "……只准你摸。别得寸进尺。"),
    ("angry", "再碰一下试试，我不介意把你拖下水。"),
    ("legs", "别碰脚。说了别碰。"),
    ("dizzy", "转得有点晕……扶我一下，就一下。"),
    ("full", "账上够了。今天可以歇着。"),
]

for tag, text in LINES:
    body = {
        "model": MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": VOICE, "speed": 1.15, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST", headers=HDRS)
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
    h = (r.get("data") or {}).get("audio")
    if not h:
        print("FAIL", tag, str((r.get("base_resp") or {}).get("status_msg"))[:60])
        continue
    raw = bytes.fromhex(h)
    p = os.path.join(OUT, "whale_%s.mp3" % tag)
    io.open(p, "wb").write(raw)
    print("OK", tag, len(raw))

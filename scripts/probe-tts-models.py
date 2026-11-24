import io, json, urllib.request, urllib.error

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = key.get("value", "")

PREFIX = "".join(chr(c) for c in [66, 101, 97, 114, 101, 114, 32])
URL = "https://api.minimaxi.com/v1/t2a_v2"

MODELS = [
    "speech-02-hd",
    "speech-02-turbo",
    "speech-2.8-hd",
    "speech-2.8-turbo",
    "speech-2.6-hd",
    "speech-2.6-turbo",
    "speech-01",
    "speech-01-hd",
]

for m in MODELS:
    body = {
        "model": m,
        "text": "测试。",
        "stream": False,
        "voice_setting": {"voice_id": "female-shaonv", "speed": 1.0, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": PREFIX + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            js = json.loads(r.read().decode("utf-8", "replace"))
        br = js.get("base_resp") or {}
        audio = (js.get("data") or {}).get("audio")
        if audio:
            print("OK  ", m, "bytes=", len(audio) // 2)
        else:
            print("FAIL", m, br.get("status_code"), str(br.get("status_msg"))[:90])
    except urllib.error.HTTPError as e:
        print("HTTP", m, e.code, e.read().decode("utf-8", "replace")[:90])
    except Exception as e:
        print("ERR ", m, type(e).__name__, str(e)[:70])

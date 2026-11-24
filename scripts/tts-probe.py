import io, json, os, urllib.request, urllib.error

CFG = r"C:\Users\21674\.openclaw\openclaw.json"
cfg = json.loads(io.open(CFG, encoding="utf-8").read())
key = cfg["models"]["providers"]["minimax"]["apiKey"]
if not isinstance(key, str):
    key = json.loads(json.dumps(key)).get("value", "")

body = {
    "model": "speech-02-hd",
    "text": "你好，我是测试。",
    "stream": False,
    "voice_setting": {"voice_id": "female-shaonv", "speed": 1.0, "vol": 1.0, "pitch": 0},
    "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
}
data = json.dumps(body).encode("utf-8")

urls = [
    "https://api.minimaxi.com/v1/t2a_v2",
    "https://api.minimax.io/v1/t2a_v2",
    "https://api.minimax.chat/v1/t2a_v2",
]

for u in urls:
    req = urllib.request.Request(
        u, data=data, method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
            print(u, "->", r.status, raw[:180].replace("\n", " "))
    except urllib.error.HTTPError as e:
        print(u, "-> HTTP", e.code, e.read().decode("utf-8", "replace")[:180].replace("\n", " "))
    except Exception as e:
        print(u, "-> ERR", type(e).__name__, str(e)[:120])

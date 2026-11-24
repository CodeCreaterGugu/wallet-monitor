# -*- coding: utf-8 -*-
"""生成四套皮肤的「全天问候」语音：voice/cus_{皮肤}_{hash}.mp3（默认套无皮肤前缀）。

音色对照（与 skins.ts 的 voiceId / 既有音频保持一致）：
  none      MiniMax  female-shaonv                        speed 1.15 → cus_{hash}
  christmas 火山     ICL_uranus_zh_female_tiaopigongzhu_tob  rate 15  → cus_christmas_{hash}
  whale     火山     ICL_uranus_zh_female_qinglenggaoya_tob  rate 15  → cus_whale_{hash}
  yukata    火山     ICL_uranus_zh_female_tianmeijiaoqiao_tob rate 15 → cus_yukata_{hash}
"""
import io
import json
import os
import re
import sys
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ws_tts  # noqa: E402

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
KEYFILE = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
CFG = r"C:\Users\21674\.openclaw\openclaw.json"

SKINS = {
    "none": {"engine": "minimax", "voice": "female-shaonv", "speed": 1.15, "prefix": "cus_", "txt": "lines-none.txt"},
    "christmas": {"engine": "volc", "voice": "ICL_uranus_zh_female_tiaopigongzhu_tob", "rate": 15,
                  "prefix": "cus_christmas_", "txt": "lines-christmas.txt"},
    "whale": {"engine": "volc", "voice": "ICL_uranus_zh_female_qinglenggaoya_tob", "rate": 15,
              "prefix": "cus_whale_", "txt": "lines-whale.txt"},
    "yukata": {"engine": "volc", "voice": "ICL_uranus_zh_female_tianmeijiaoqiao_tob", "rate": 15,
               "prefix": "cus_yukata_", "txt": "lines-yukata.txt"},
}
KINDS = ["greet_morning", "greet_noon", "greet_afternoon", "greet_evening", "greet_night"]
FORCE = {"whale"}   # 鲸鱼刚用 rate 0 生成过，重做保持 1.15 倍速一致


def fnv1a(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def read_volc_key():
    lines = io.open(KEYFILE, encoding="utf-8", errors="replace").read().splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().rstrip("：:") == "audio":
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if not s:
                    continue
                if s.lower().startswith("api:"):
                    return s.split(":", 1)[1].strip()
    raise SystemExit("找不到火山 audio 密钥")


def minimax_key():
    cfg = json.loads(io.open(CFG, encoding="utf-8").read())
    k = cfg["models"]["providers"]["minimax"]["apiKey"]
    return k if isinstance(k, str) else k.get("value", "")


def volc_synth(key, speaker, rate, text, path):
    ws = ws_tts.WS(ws_tts.HOST, ws_tts.PATH, {
        "X-Api-Key": key,
        "X-Api-Resource-Id": "seed-tts-2.0",
        "X-Api-Connect-Id": str(uuid.uuid4()),
    })
    ws.send(ws_tts.build(ws_tts.EV_START_CONN, payload=b"{}"))
    m = ws_tts.next_msg(ws, "StartConnection")
    if not m or m["event"] != ws_tts.EV_CONN_STARTED:
        return None
    sid = str(uuid.uuid4())
    params = {"req_params": {"speaker": speaker,
                             "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": rate}}}
    ws.send(ws_tts.build(ws_tts.EV_START_SESSION, sid, json.dumps(params, ensure_ascii=False).encode()))
    ws_tts.next_msg(ws, "StartSession")
    ws.send(ws_tts.build(ws_tts.EV_TASK_REQUEST, sid,
                         json.dumps({"req_params": {"text": text}}, ensure_ascii=False).encode()))
    ws.send(ws_tts.build(ws_tts.EV_FINISH_SESSION, sid, b"{}"))
    audio = bytearray()
    while True:
        m = ws_tts.next_msg(ws, "stream")
        if m is None:
            break
        if m["event"] == ws_tts.EV_SESSION_FINISHED:
            break
        if m["type"] == ws_tts.T_AUDIO_SERVER and m["payload"]:
            audio += m["payload"]
        elif m["event"] == ws_tts.EV_TTS_RESPONSE and m["payload"]:
            audio += m["payload"]
        elif m["type"] == ws_tts.T_ERROR or m["event"] == ws_tts.EV_SESSION_FAILED:
            print("   server error:", m["payload"][:160])
            break
    try:
        ws.send(ws_tts.build(ws_tts.EV_FINISH_CONN, payload=b"{}"))
    except Exception:
        pass
    if not audio:
        return None
    io.open(path, "wb").write(bytes(audio))
    return len(audio)


def minimax_synth(key, voice, speed, text, path, tries=3):
    body = {
        "model": "speech-2.8-hd",
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice, "speed": speed, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 24000, "bitrate": 32000, "format": "mp3"},
    }
    for _ in range(tries):
        try:
            req = urllib.request.Request(
                "https://api.minimaxi.com/v1/t2a_v2",
                data=json.dumps(body).encode("utf-8"),
                method="POST",
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            )
            r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace"))
            audio = (r.get("data") or {}).get("audio")
            if audio:
                raw = bytes.fromhex(audio)
                io.open(path, "wb").write(raw)
                return len(raw)
        except Exception as e:
            print("   minimax err", repr(e)[:100])
    return None


def sections(txt):
    sec, data = None, {}
    for raw in io.open(os.path.join(D, txt), encoding="utf-8"):
        s = raw.strip()
        m = re.match(r"^\[([^\]]+)\]$", s)
        if m:
            sec = m.group(1)
            continue
        if sec and s and not s.startswith("#") and not s.startswith("//"):
            data.setdefault(sec, []).append(s)
    return data


vkey = read_volc_key()
mkey = minimax_key()

for skin, cfg in SKINS.items():
    data = sections(cfg["txt"])
    made = skipped = failed = 0
    for kind in KINDS:
        for text in data.get("%s.%s" % (skin, kind), []):
            name = cfg["prefix"] + fnv1a(text) + ".mp3"
            path = os.path.join(OUT, name)
            if os.path.exists(path) and os.path.getsize(path) > 2000 and skin not in FORCE:
                skipped += 1
                continue
            if cfg["engine"] == "volc":
                n = volc_synth(vkey, cfg["voice"], cfg["rate"], text, path)
            else:
                n = minimax_synth(mkey, cfg["voice"], cfg["speed"], text, path)
            if n:
                made += 1
                print("OK   %-10s %-26s %6d B  %s" % (skin, name, n, text))
            else:
                failed += 1
                print("FAIL %-10s %-26s %s" % (skin, name, text))
    print("== %s: 新增 %d，跳过 %d，失败 %d" % (skin, made, skipped, failed))

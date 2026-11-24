# -*- coding: utf-8 -*-
"""只为这次改写的台词补生成语音：voice/cus_{皮肤}_{hash}.mp3"""
import io
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ws_tts  # noqa: E402

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = os.path.join(D, "voice")
KEYFILE = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"

JOBS = [
    ("lines-yukata.txt", "yukata", "ICL_uranus_zh_female_tianmeijiaoqiao_tob", 15,
     ["legs", "greet_noon", "greet_afternoon", "greet_evening"]),
    ("lines-christmas.txt", "christmas", "ICL_uranus_zh_female_tiaopigongzhu_tob", 15,
     ["pat", "full"]),
]


def fnv1a(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return "%08x" % h


def read_key():
    lines = io.open(KEYFILE, encoding="utf-8", errors="replace").read().splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().rstrip("：:") == "audio":
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if not s:
                    continue
                if s.lower().startswith("api:"):
                    return s.split(":", 1)[1].strip()
    raise SystemExit("找不到 audio 密钥")


def sections(path):
    sec, data = None, {}
    for raw in io.open(path, encoding="utf-8"):
        s = raw.strip()
        m = re.match(r"^\[([^\]]+)\]$", s)
        if m:
            sec = m.group(1)
            continue
        if sec and s and not s.startswith("#") and not s.startswith("//"):
            data.setdefault(sec, []).append(s)
    return data


def synth(key, speaker, rate, text, out):
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
    io.open(out, "wb").write(bytes(audio))
    return len(audio)


key = read_key()
made = skipped = failed = 0
for fname, skin, speaker, rate, kinds in JOBS:
    data = sections(os.path.join(D, fname))
    for kind in kinds:
        for text in data.get("%s.%s" % (skin, kind), []):
            name = "cus_%s_%s.mp3" % (skin, fnv1a(text))
            path = os.path.join(OUT, name)
            if os.path.exists(path) and os.path.getsize(path) > 2000:
                skipped += 1
                continue
            n = synth(key, speaker, rate, text, path)
            if n:
                made += 1
                print("OK   %-10s %-28s %6d B  %s" % (skin, name, n, text))
            else:
                failed += 1
                print("FAIL %-10s %-28s %s" % (skin, name, text))

print("\n新增 %d，跳过 %d，失败 %d" % (made, skipped, failed))

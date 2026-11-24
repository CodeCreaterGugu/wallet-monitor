# -*- coding: utf-8 -*-
"""圣诞候选音色样音。"""
import io, json, os, sys, time, uuid

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = r"D:\AI生成\语音\圣诞候选"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(D, "scripts"))
from ws_tts import (WS, build, next_msg, HOST, PATH, EV_START_CONN, EV_START_SESSION,
                    EV_FINISH_SESSION, EV_TASK_REQUEST, EV_SESSION_FINISHED,
                    EV_TTS_RESPONSE, T_AUDIO_SERVER, T_ERROR)

KEY_PATH = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
TEXT = "圣诞快乐，礼物给你留了一份。"

SPEAKERS = [
    ("tianmeixiaoyuan", "zh_female_tianmeixiaoyuan_uranus_bigtts", "甜美小源"),
    ("qingxinnvsheng", "zh_female_qingxinnvsheng_uranus_bigtts", "清新女声"),
    ("qiaopinv", "zh_female_qiaopinv_uranus_bigtts", "俏皮女声"),
    ("kailangjiejie", "zh_female_kailangjiejie_uranus_bigtts", "开朗姐姐"),
    ("yuanqitianmei", "ICL_uranus_zh_female_yuanqitianmei_tob", "元气甜妹"),
    ("linjianvhai", "zh_female_linjianvhai_uranus_bigtts", "邻家女孩"),
]

cands = []
for line in io.open(KEY_PATH, encoding="utf-8"):
    t = line.strip()
    if not t:
        continue
    if ":" in t:
        v = t.split(":", 1)[1].strip()
        if len(v) >= 20:
            cands.append(v)
    elif len(t) >= 20:
        cands.append(t)
KEY = cands[-1]


def synth(text, speaker, path):
    ws = WS(HOST, PATH, {
        "X-Api-Key": KEY,
        "X-Api-Resource-Id": "seed-tts-2.0",
        "X-Api-Connect-Id": str(uuid.uuid4()),
    })
    ws.send(build(EV_START_CONN, payload=b"{}"))
    m = next_msg(ws)
    if not m or m["event"] != 50:
        raise RuntimeError("conn failed")
    sid = str(uuid.uuid4())
    params = {"req_params": {"speaker": speaker,
                             "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": 0}}}
    ws.send(build(EV_START_SESSION, sid, json.dumps(params, ensure_ascii=False).encode()))
    next_msg(ws)
    ws.send(build(EV_TASK_REQUEST, sid, json.dumps({"req_params": {"text": text}}, ensure_ascii=False).encode()))
    ws.send(build(EV_FINISH_SESSION, sid, b"{}"))
    audio = bytearray()
    while True:
        m = next_msg(ws)
        if m is None or m["event"] == EV_SESSION_FINISHED:
            break
        if m["type"] == T_AUDIO_SERVER and m["payload"]:
            audio += m["payload"]
        elif m["event"] == EV_TTS_RESPONSE and m["payload"]:
            audio += m["payload"]
        elif m["type"] == T_ERROR:
            raise RuntimeError(m["payload"][:150].decode("utf-8", "replace"))
    try:
        ws.send(build(2, payload=b"{}"))
    except Exception:
        pass
    if not audio:
        raise RuntimeError("no audio")
    io.open(path, "wb").write(audio)
    return len(audio)


for slug, speaker, label in SPEAKERS:
    p = os.path.join(OUT, slug + ".mp3")
    try:
        n = synth(TEXT, speaker, p)
        print("OK  %-18s %-10s %dB" % (slug, label, n))
    except Exception as e:
        print("FAIL %-17s %s" % (slug, e))
    time.sleep(0.15)

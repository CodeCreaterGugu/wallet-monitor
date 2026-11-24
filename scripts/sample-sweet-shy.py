# -*- coding: utf-8 -*-
"""甜美/害羞向音色样音，用害羞台词测试。"""
import io, json, os, sys, time, uuid

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
OUT = r"D:\AI生成\语音\甜美害羞试听"
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(D, "scripts"))
from ws_tts import (WS, build, next_msg, HOST, PATH, EV_START_CONN, EV_START_SESSION,
                    EV_FINISH_SESSION, EV_TASK_REQUEST, EV_SESSION_FINISHED,
                    EV_TTS_RESPONSE, T_AUDIO_SERVER, T_ERROR)

KEY_PATH = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
TEXT = "嗯……别、别这样…"

SPEAKERS = [
    ("tianmeijiaoqiao", "ICL_uranus_zh_female_tianmeijiaoqiao_tob", "甜美娇俏"),
    ("ruanmengtangtang", "ICL_uranus_zh_female_ruanmengtangtang_tob", "软萌糖糖"),
    ("ruanmengtuanzi", "ICL_uranus_zh_female_ruanmengtuanzi_tob", "软萌团子"),
    ("qingtianmeimei", "ICL_uranus_zh_female_qingtianmeimei_tob", "清甜莓莓"),
    ("chunzhenshaonv", "ICL_uranus_zh_female_chunzhenshaonv_tob", "纯真少女"),
    ("guaiqiaokeer", "ICL_uranus_zh_female_guaiqiaokeer_tob", "乖巧可儿"),
    ("sajiaoxuemei", "zh_female_sajiaoxuemei_uranus_bigtts", "撒娇学妹"),
    ("tianmeihuopo", "ICL_uranus_zh_female_tianmeihuopo_tob", "甜美活泼"),
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
        print("OK  %-18s %-12s %dB" % (slug, label, n))
    except Exception as e:
        print("FAIL %-17s %s" % (slug, e))
    time.sleep(0.15)

# -*- coding: utf-8 -*-
"""用指定音色把某套台词完整合成到独立文件夹（不覆盖现有语音）。"""
import argparse
import io
import json
import os
import re
import sys
import time
import uuid

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"
sys.path.insert(0, os.path.join(D, "scripts"))
from ws_tts import (WS, build, next_msg, HOST, PATH, EV_START_CONN, EV_START_SESSION,
                    EV_FINISH_SESSION, EV_TASK_REQUEST, EV_SESSION_FINISHED,
                    EV_TTS_RESPONSE, T_AUDIO_SERVER, T_ERROR)

KEY_PATH = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"

ap = argparse.ArgumentParser()
ap.add_argument("--skin", required=True)
ap.add_argument("--speaker", required=True)
ap.add_argument("--rate", type=int, default=15)
ap.add_argument("--outdir", required=True)
args = ap.parse_args()
os.makedirs(args.outdir, exist_ok=True)

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
KEY = ***


def fnv(text):
    h = 0x811C9DC5
    for b in text.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")


TXT = os.path.join(D, "lines-%s.txt" % args.skin)
sec, data = None, {}
for ln in io.open(TXT, encoding="utf-8"):
    s = ln.strip()
    m = re.match(r"^\[([^\]]+)\]$", s)
    if m:
        sec = m.group(1)
        continue
    if sec and s and not s.startswith("#"):
        data.setdefault(sec, []).append(s)


def synth(text, path):
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
    params = {"req_params": {"speaker": args.speaker,
                             "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": args.rate}}}
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


ok = fail = 0
for kind in ["pat", "angry", "legs", "dizzy"]:
    for i, text in enumerate(data.get("%s.%s" % (args.skin, kind), []), 1):
        p = os.path.join(args.outdir, "%s_%d.mp3" % (kind, i))
        try:
            n = synth(text, p)
            ok += 1
            print("OK  %-10s %6dB  %s" % (kind + "_" + str(i), n, text))
        except Exception as e:
            fail += 1
            print("FAIL %-9s %s" % (kind + "_" + str(i), e))
        time.sleep(0.15)

SYS = {"done": "%s.done" % args.skin, "full": "%s.full" % args.skin, "sad": "%s.sad" % args.skin,
       "panel_low": "%s.panel_low" % args.skin, "panel_high": "%s.panel_high" % args.skin}
for name, key in SYS.items():
    lines = data.get(key, [])
    if not lines:
        continue
    p = os.path.join(args.outdir, "%s.mp3" % name)
    try:
        n = synth(lines[0], p)
        ok += 1
        print("OK  %-10s %6dB  %s" % (name, n, lines[0]))
    except Exception as e:
        fail += 1
        print("FAIL %-9s %s" % (name, e))
    time.sleep(0.15)

print("done ok=%d fail=%d skin=%s speaker=%s" % (ok, fail, args.skin, args.speaker))

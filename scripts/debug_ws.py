# -*- coding: utf-8 -*-
"""调试：打印火山 TTS 服务端返回的原始帧"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ws_tts import WS, build, parse, HOST, PATH, EV_START_CONN

key_path = r"C:\Users\21674\Desktop\重要文件\API KEY.txt"
cands = []
for line in open(key_path, encoding="utf-8"):
    t = line.strip()
    if not t:
        continue
    if ":" in t:
        v = t.split(":", 1)[1].strip()
        if len(v) >= 20:
            cands.append(v)
    elif len(t) >= 20:
        cands.append(t)
key = cands[-1]
print("key len", len(key))

ws = WS(HOST, PATH, {
    "X-Api-Key": key,
    "X-Api-Resource-Id": "seed-tts-2.0",
    "X-Api-Connect-Id": "debug-conn",
})
print("handshake OK")

ws.send(build(EV_START_CONN))
print("sent StartConnection")

for i in range(4):
    try:
        data = ws.recv()
    except Exception as e:
        print("recv error:", e)
        break
    print(f"frame {i}: len={len(data)} hex={data[:48].hex()}")
    m = parse(data)
    print("   parsed:", m and {k: (v if k != 'payload' else v[:40]) for k, v in m.items()})

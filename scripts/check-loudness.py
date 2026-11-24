# -*- coding: utf-8 -*-
import os, re, subprocess

FF = r"C:\Users\21674\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"
D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\voice"

for name in ["line_whale_pat_1", "line_whale_pat_2", "line_whale_pat_3",
             "line_whale_angry_1", "line_whale_angry_2", "line_whale_angry_3"]:
    p = os.path.join(D, name + ".mp3")
    if not os.path.exists(p):
        print(name, "MISSING")
        continue
    r = subprocess.run(
        [FF, "-hide_banner", "-i", p, "-af", "volumedetect", "-f", "null", os.devnull],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = (r.stderr or "")
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", out)
    mx = re.search(r"max_volume:\s*(-?[\d.]+) dB", out)
    dur = re.search(r"Duration:\s*([\d:.]+)", out)
    print("%-22s dur=%s mean=%s max=%s" % (name, dur.group(1) if dur else "?",
                                           mean.group(1) if mean else "?", mx.group(1) if mx else "?"))

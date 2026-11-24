# -*- coding: utf-8 -*-
import io

P = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\lines-custom.txt"
t = io.open(P, encoding="utf-8").read().rstrip("\n")

BLOCK = """

# ------------------------------------------------------------
# 六、系统语音清单（代码写死，不在上面的随机台词里）
# ------------------------------------------------------------
# 用途：只是"哪些句子需要合成语音"的清单。
#   改这里不会改变触发时机 —— 触发都在代码里，要改文本请找我。
#   换装音色时，我按 voice\\{皮肤}_{key}.mp3 生成；
#   找不到皮肤版就自动回退基础版 voice\\{key}.mp3。
#
# key                触发时机                        现有文本
# done               任务完成                        气泡「任务完成啦」+ 消耗金额
# thanks             充值成功后 0.15s                无独立文本
# full               充值成功后 2s（吃饱）           气泡「谢谢主人！我吃饱啦～」
# sad                余额低于阈值当天首次            无文本（只有语音）
# line_panel_high    点气泡查看余额（充足）          无文本
# line_panel_low     点气泡查看余额（告急）          无文本
# pat                摸头兜底（txt 没配时）          无文本
# shy                点腿兜底                        无文本
# angry              点身子兜底                      无文本
# dizzy              双击兜底                        无文本
# giggle             连点笑声音效                    无（纯音效）
# dizzy_fx           眩晕音效                        无（纯音效）
"""

io.open(P, "w", encoding="utf-8", newline="\n").write(t + BLOCK + "\n")
print("appended; total", len(t + BLOCK))

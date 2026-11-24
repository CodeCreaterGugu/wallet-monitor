# -*- coding: utf-8 -*-
"""按新图改写台词：和服（团子/烟花/丸子头）、圣诞（Commit/饼干/傲娇）。"""
import io

D = r"C:\Users\21674\.openclaw\extensions\wallet-monitor"

yuka = io.open(D + r"\lines-yukata.txt", encoding="utf-8").read()
chri = io.open(D + r"\lines-christmas.txt", encoding="utf-8").read()

yuka_edits = [
    ("夜市那边好像有苹果糖\n",
     "夜市那边好像有苹果糖\n丸子头扎低一点，风一吹就不乱\n三色团子，你要绿的那颗还是粉的？\n"),
    ("头发被风吹乱了，挠一挠\n发簪好像歪了\n发簪有点松，扶一下\n",
     "头发被风吹乱了，挠一挠\n碎发贴到脸上了，拨一下\n丸子有点歪，重新扎一下\n"),
    ("木屐不稳，别推我\n脚趾涂了指甲油，别踩\n木屐会掉的啦\n",
     "木屐不稳，别推我\n扇子要掉了啦，扶一下\n木屐会掉的啦\n"),
    ("中午好，日头有点大。\n找个阴凉处歇一会儿。\n吃饭了吗？\n",
     "中午好，日头有点大。\n举着扇子遮一遮，脸都晒红了。\n找个阴凉处歇一会儿。\n"),
    ("下午好，风起来了。\n下午适合慢慢逛。\n天还亮，别急着回。\n",
     "下午好，来吃串三色团子？\n咬不断……这团子也太黏了吧。\n先分你一颗，绿的是抹茶。\n"),
    ("晚上好，灯挂起来了。\n夜里风凉。\n早点歇，明天还有集市。\n",
     "晚上好，烟花要开始了。\n快看那边，第一朵炸开了。\n今晚的夜色，值得多看一会儿。\n"),
]

chri_edits = [
    ("雪地里踩一脚，咯吱咯吱的\n",
     "雪地里踩一脚，咯吱咯吱的\nCommit 今天也乖乖趴在旁边\n摸摸 Commit 的角，它的小灯会亮一下\n"),
    ("帽子上的雪，别拍掉嘛\n手是暖的，好舒服\n你的手比暖手宝还暖\n",
     "才、才没有很开心……\n就摸一下，别得寸进尺。\n帽子要被你摸歪了啦。\n"),
    ("到账了。这份我收下。\n",
     "谢谢……这盘饼干我收下了。\n"),
]

log = []


def apply(text, edits, name):
    for old, new in edits:
        if old in text:
            text = text.replace(old, new, 1)
            log.append("OK   %s: %s" % (name, old.split("\n")[0][:18]))
        else:
            log.append("MISS %s: %s" % (name, old.split("\n")[0][:18]))
    return text


yuka = apply(yuka, yuka_edits, "yukata")
chri = apply(chri, chri_edits, "christmas")

io.open(D + r"\lines-yukata.txt", "w", encoding="utf-8").write(yuka)
io.open(D + r"\lines-christmas.txt", "w", encoding="utf-8").write(chri)
print("\n".join(log))

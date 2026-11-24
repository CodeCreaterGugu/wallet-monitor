import io

P = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\lines-custom.txt"
t = io.open(P, encoding="utf-8").read()

NEW = """[whale.idle]
来了？余额我盯着，你忙你的。
水凉。别把手伸进来。
帽子是我的，别碰。
别一直看着我。……看余额去。
潮水要涨了，我该回去了。
你敲键盘太吵。……算了，随你。
这套衣服？方便，不用弯腰。
钱够不够，我心里有数。
天亮之前别叫我。

[whale.idle1]
久坐，腰有点僵。
伸展一下。别盯着看。

[whale.idle2]
水温正好，就是有点困。
……哈欠。别学我。

[whale.idle3]
帽子里进了沙子。
头发被帽子压乱了。

[whale.idle4]
算算时间，潮快涨了。
还早。你急什么。

[whale.pat]
……只准你摸。别得寸进尺。
手拿开。……再放一会儿也行。
别摸头发，会乱。

[whale.angry]
再碰一下试试，我不介意把你拖下水。
我们深海来的，脾气都不太好。
手指还要不要了。

[whale.legs]
别碰脚。说了别碰。
拖鞋会掉的。
再碰我踩你了。

[whale.dizzy]
转得有点晕……扶我一下，就一下。
别晃。我站不稳。
眼前都是水波……收一收。
"""

start = t.index("[whale.idle]")
marker = "# 四、和服装"
pos = t.index(marker)
sep = t.rindex("# ---", 0, pos)

out = t[:start] + NEW + "\n" + t[sep:]
io.open(P, "w", encoding="utf-8", newline="\n").write(out)
print("whale block replaced; total chars", len(out))

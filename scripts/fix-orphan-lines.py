import io, re

P = r"C:\Users\21674\.openclaw\extensions\wallet-monitor\lines-custom.txt"
lines = io.open(P, encoding="utf-8").read().replace("\r\n", "\n").split("\n")

SEP = re.compile(r"^#\s*-{10,}\s*$")
HDR = re.compile(r"^#")

out = []
i = 0
moved = []

while i < len(lines):
    ln = lines[i]
    if SEP.match(ln.strip()):
        # 向后看：分隔线之后、下一个注释行之前，如果夹着正文，就是放错位的
        j = i + 1
        orphans = []
        while j < len(lines):
            s = lines[j].strip()
            if s == "":
                j += 1
                continue
            if HDR.match(s):
                break
            orphans.append(lines[j])
            j += 1
        if orphans:
            # 插到分隔线之前
            for o in orphans:
                out.append(o)
            moved.extend(orphans)
            # 跳过原文里的这些行
            i = j
            out.append(ln)
            continue
    out.append(ln)
    i += 1

text = "\n".join(out)
text = re.sub(r"\n{3,}", "\n\n", text)
io.open(P, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n")

print("moved", len(moved))
for m in moved:
    print("  ->", m.strip())

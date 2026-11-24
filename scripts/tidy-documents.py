# -*- coding: utf-8 -*-
"""整理 D:\\AI生成\\文档：
1) 把工具残留的临时输出移到 _临时输出_待删（不删除，等确认）
2) 把明显不是 AI 生成的个人资料移到 非AI资料（按主题分子目录）
"""
import os
import shutil

DOC = r"D:\AI生成\文档"
JUNK = os.path.join(DOC, "_临时输出_待删")
KEEP = os.path.join(DOC, "非AI资料")

os.makedirs(JUNK, exist_ok=True)

# 工具残留：OCR 中间结果、GUI/脚本输出、调试打印
junk_names = [
    "appcmp.txt", "appocr_154.json", "compare_report.txt",
    "er2ocr_154.json", "er2ocr_155.json", "er2ocr_156.json",
    "erocr_150_154.json", "erocr_150_155.json", "erocr_150_156.json",
    "erocr_200_154.json", "erocr_200_155.json", "erocr_200_156.json",
    "gui_err.txt", "gui_out.txt",
    "ocr_154.json", "ocr_155.json", "ocr_156.json",
    "outocr_154.json", "outocr_155.json", "outocr_156.json",
    "prep_result.txt", "scr_err.txt", "scr_out.txt", "tmp_ocr.json",
    "tr_cli.txt", "v_ja.json", "v_lines.json", "v_words.json", "verify_out.txt",
    "peugeot_dump.json",
]

moved_junk = []
for name in junk_names:
    src = os.path.join(DOC, name)
    if os.path.isfile(src):
        shutil.move(src, os.path.join(JUNK, name))
        moved_junk.append(name)

# 个人资料归类
groups = {
    "高考志愿": [
        "高考志愿_610分合理版.xlsx", "高考志愿_610分推荐.xlsx",
        "高考志愿分分数段合理版.xlsx", "高考志愿分分数段合理版_2.xlsx",
        "高考志愿分分数段推荐.xlsx", "高考志愿汇总_按省份分类.xlsx",
        "高考志愿汇总_最全面.xlsx", "高考志愿汇总_最全面_2.xlsx",
        "汇总表格.xlsx",
    ],
    "学习分享": [
        "高三学习经验分享 (2).pptx", "高三学习经验分享.pptx",
        "高三学习经验分享_明亮版.pptx", "高三学习经验分享_手工版.pptx",
        "kebiao.txt",
    ],
    "论文与面试": [
        "论文_summary_Alzheimer_EV_therapy.md",  # 占位，实际见下
        "paper_summary_Alzheimer_EV_therapy.md", "paper_summary_Alzheimer_EV_therapy.pdf",
        "阿尔茨海默病论文面试准备.docx", "阿尔茨海默病论文面试准备_专业详解版.docx",
        "English translation（校正版）.docx",
    ],
    "其他资料": [
        "郑永康职业生涯.pptx", "赛季规划文档_v1.0_改前备份_20261013.docx",
        "主内小组_金句研读（五选一）.docx", "feishu.html",
    ],
}

moved_keep = []
for group, names in groups.items():
    target = os.path.join(KEEP, group)
    os.makedirs(target, exist_ok=True)
    for name in names:
        src = os.path.join(DOC, name)
        if os.path.isfile(src):
            shutil.move(src, os.path.join(target, name))
            moved_keep.append(os.path.join(group, name))

print("临时输出移入 _临时输出_待删：%d 个" % len(moved_junk))
for n in moved_junk:
    print("  -", n)
print("个人资料归入 非AI资料：%d 个" % len(moved_keep))
for n in moved_keep:
    print("  -", n)

print("\n剩余（留在文档根目录）：")
for n in sorted(os.listdir(DOC)):
    p = os.path.join(DOC, n)
    if os.path.isfile(p):
        print("  ", n)
    else:
        print("  [dir]", n)

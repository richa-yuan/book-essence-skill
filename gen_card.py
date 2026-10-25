# -*- coding: utf-8 -*-
"""Quiet Folio — book essence visual card generator (v3).

数据参数化 + 画布高度自适应：传入 data dict 即可渲染任意书籍卡片。
用法：from gen_card import render; render(data, out_path)
"""
import os
from PIL import Image, ImageDraw, ImageFont

def _first_loadable(paths, size=24, idx=0):
    """按顺序尝试加载字体，返回第一个真实可用的路径。
    注意：macOS 沙箱下 os.path.exists 可能对系统字体目录不可见，
    故必须以 ImageFont.truetype 实测为准。"""
    for p in paths:
        if not p:
            continue
        try:
            ImageFont.truetype(p, size, index=idx)
            return p
        except Exception:
            continue
    return None

# 拉丁展示字体：canvas-design 字体库优先，缺失时退回系统字体
CF = "/Users/richa/.workbuddy/skills/canvas-design/canvas-fonts/"
DISPLAY = _first_loadable([CF + "YoungSerif-Regular.ttf",
                           "/System/Library/Fonts/Supplemental/Georgia.ttf"])
SANS = _first_loadable([CF + "WorkSans-Regular.ttf",
                        "/System/Library/Fonts/Supplemental/Arial.ttf"])
SANS_B = _first_loadable([CF + "WorkSans-Bold.ttf",
                          "/System/Library/Fonts/Supplemental/Arial Bold.ttf"])
MONO = _first_loadable([CF + "DMMono-Regular.ttf",
                        "/System/Library/Fonts/Menlo.ttc"])
# 中文字体：宋体（衬线，设计本意）→ 苹方 → 冬青黑 → 黑体
CN = _first_loadable([
    "/System/Library/Fonts/Songti.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
])
if CN is None:
    raise RuntimeError("未找到可用中文字体，中文将渲染为方框；请安装 Songti/PingFang 等字体")
# Songti.ttc 内含多字重：index 6 = Songti SC Regular（简体常规体，正文用）
CN_IDX = 6 if CN.endswith("Songti.ttc") else 0

def fc(size):
    """中文字体统一加载入口。"""
    return F(CN, size, CN_IDX)

W = 1240
PAPER = (244, 239, 229)
INK = (28, 26, 23)
SOFT = (96, 90, 82)
FAINT = (150, 142, 130)
ACCENT = (156, 59, 46)
LINE = (198, 190, 176)

ML, MR = 100, 100
CW = W - ML - MR  # 1040

def F(path, size, idx=0):
    return ImageFont.truetype(path, size, index=idx)

def has_cjk(s):
    return any(ord(c) > 0x2E80 for c in s)

def wrap(text, font, max_w):
    tokens, cur = [], ""
    for ch in text:
        if ch == ' ':
            if cur: tokens.append(cur); cur = ""
            tokens.append(' ')
        elif ord(ch) > 0x2E80:
            if cur: tokens.append(cur); cur = ""
            tokens.append(ch)
        else:
            cur += ch
    if cur: tokens.append(cur)
    lines, line = [], ""
    for t in tokens:
        test = line + t
        if font.getlength(test) <= max_w:
            line = test
        else:
            if line: lines.append(line.rstrip())
            if t != ' ' and font.getlength(t) > max_w and len(t) > 1:
                piece = ""
                for c in t:
                    if font.getlength(piece + c) <= max_w: piece += c
                    else: lines.append(piece); piece = c
                line = piece
            else:
                line = t if t != ' ' else ""
    if line: lines.append(line.rstrip())
    return lines

def fit_font(path, text, max_w, size, idx=0):
    """若文字超宽则逐级缩小字号。"""
    while size > 20 and F(path, size, idx).getlength(text) > max_w:
        size -= 2
    return F(path, size, idx)

def render(data, out_path):
    TALL = 3600
    img = Image.new("RGB", (W, TALL), PAPER)
    d = ImageDraw.Draw(img)

    def rule(y):
        d.line([(ML, y), (W - MR, y)], fill=LINE, width=1)

    def section_heading(y, cn_text, en_text):
        d.text((ML, y), cn_text, font=fc(21), fill=ACCENT, stroke_width=1, stroke_fill=ACCENT)
        w = fc(21).getlength(cn_text)
        d.text((ML + w + 22, y + 4), en_text, font=F(SANS_B, 15), fill=FAINT)
        d.rectangle([ML, y + 34, ML + 34, y + 37], fill=ACCENT)

    # ================= header =================
    d.text((ML, 76), "BOOK  ESSENCE", font=F(SANS_B, 19), fill=INK)
    wb = F(SANS_B, 19).getlength("BOOK  ESSENCE")
    d.text((ML + wb + 14, 78), "书籍精华", font=fc(19), fill=SOFT)
    tag = data.get("tag", "No. 001")
    d.text((W - MR, 80), tag + "  /", font=F(MONO, 17), fill=FAINT, anchor="ra")
    tw = F(MONO, 17).getlength(tag + "  /")
    d.text((W - MR - tw - 10, 79), data["title"], font=fc(18), fill=FAINT, anchor="ra")
    rule(114)

    # ================= title =================
    d.text((ML, 148), data["author"], font=fc(21), fill=SOFT)
    kw = fc(21).getlength(data["author"])
    d.text((ML + kw + 14, 150), "·  " + str(data["year"]), font=F(SANS, 20), fill=FAINT)

    tf = fit_font(CN, data["title"], CW, 100)
    d.text((ML, 176), data["title"], font=tf, fill=INK)
    sf = fit_font(CN, data["subtitle"], CW, 28)
    d.text((ML, 300), data["subtitle"], font=sf, fill=ACCENT)
    x = ML
    for c in data["en_title"].upper():
        d.text((x, 342), c, font=F(SANS_B, 26), fill=FAINT)
        x += F(SANS_B, 26).getlength(c) + 8
    d.rectangle([ML, 392, ML + 64, 395], fill=ACCENT)
    rule(424)

    # ================= rating monument =================
    score = data["score"]
    gc = (285, 560); r = 94
    d.arc([gc[0]-r, gc[1]-r, gc[0]+r, gc[1]+r], 145, 395, fill=LINE, width=14)
    end = 145 + 250 * (score / 10.0)
    d.arc([gc[0]-r, gc[1]-r, gc[0]+r, gc[1]+r], 145, end, fill=ACCENT, width=14)
    d.text((gc[0], gc[1] - 8), str(score), font=F(DISPLAY, 100), fill=INK, anchor="mm")
    cap = "综合评分"
    cw2 = fc(20).getlength(cap)
    total = cw2 + 10 + F(SANS, 19).getlength("/ 10")
    d.text((gc[0] - total/2, gc[1] + 52), cap, font=fc(20), fill=SOFT)
    d.text((gc[0] - total/2 + cw2 + 10, gc[1] + 54), "/ 10", font=F(SANS, 19), fill=SOFT)

    rx = 470
    cy = 452
    for name, val, v in data["platforms"]:
        if has_cjk(name):
            d.text((rx, cy), name, font=fc(21), fill=INK, stroke_width=1, stroke_fill=INK)
        else:
            d.text((rx, cy), name, font=F(SANS_B, 21), fill=INK)
        d.text((rx + 250, cy - 6), val, font=F(DISPLAY, 30), fill=ACCENT, anchor="lm")
        bw = 380
        d.rectangle([rx, cy + 38, rx + bw, cy + 44], fill=LINE)
        d.rectangle([rx, cy + 38, rx + int(bw * v), cy + 44], fill=ACCENT)
        cy += 72

    cal = data["calibration"]
    d.text((rx, 688), "校准说明", font=fc(17), fill=ACCENT)
    cf3 = fc(18)
    for i, ln in enumerate(wrap(cal, cf3, 600)):
        d.text((rx, 716 + i * 26), ln, font=cf3, fill=FAINT)
    rule(800)

    # ================= conclusion =================
    conc = data["conclusion"]
    d.rectangle([ML, 834, ML + 5, 924], fill=ACCENT)
    cf4 = fc(29)
    yy = 834
    for ln in wrap(conc, cf4, CW - 30):
        d.text((ML + 26, yy), ln, font=cf4, fill=INK)
        yy += 44
    rule(yy + 30)

    # ================= core ideas =================
    y = yy + 64
    section_heading(y, "核心观点", "CORE  IDEAS")
    y += 72
    cf5 = fc(24)
    for i, text in enumerate(data["ideas"], 1):
        d.text((ML, y - 2), f"{i:02d}", font=F(DISPLAY, 29), fill=ACCENT)
        lines = wrap(text, cf5, CW - 100)
        for j, ln in enumerate(lines):
            d.text((ML + 76, y + j * 34), ln, font=cf5, fill=INK)
        y += 34 * len(lines) + 26

    # ================= quote =================
    rule(y + 12)
    y += 50
    section_heading(y, "关键金句", "KEY  LINES")
    y += 66
    d.text((ML - 8, y - 34), "“", font=F(DISPLAY, 140), fill=ACCENT)
    qbody = data["quote"]
    cf6 = fc(33)
    qlines = wrap(qbody, cf6, CW - 90)
    for j, ln in enumerate(qlines):
        d.text((ML + 92, y + j * 50), ln, font=cf6, fill=INK)
    y += 50 * len(qlines)

    # ================= takeaways (2x2 grid, dynamic rows) =================
    rule(y + 20)
    y += 56
    section_heading(y, "带走什么", "TAKEAWAYS")
    y += 68
    takes = data["takeaways"]
    cf7 = fc(22)
    col_w = (CW - 50) / 2
    # 预排：按行计算行高
    rows = [takes[i:i+2] for i in range(0, len(takes), 2)]
    for ri, row in enumerate(rows):
        wrapped = [wrap(t, cf7, col_w - 40) for t in row]
        row_h = max(len(wl) for wl in wrapped) * 31 + 18
        for ci, t in enumerate(row):
            cx = ML + ci * (col_w + 50)
            d.rectangle([cx, y + 3, cx + 17, y + 20], outline=ACCENT, width=2)
            d.line([cx + 4, y + 12, cx + 7, y + 17], fill=ACCENT, width=2)
            d.line([cx + 7, y + 17, cx + 14, y + 5], fill=ACCENT, width=2)
            for j, ln in enumerate(wrapped[ci]):
                d.text((cx + 34, y + j * 31), ln, font=cf7, fill=INK)
        y += row_h

    content_end = y + 10

    # ================= crop to content + footer =================
    FOOTER_ZONE = 120
    H = content_end + FOOTER_ZONE
    img = img.crop((0, 0, W, H))
    d = ImageDraw.Draw(img)

    # 边框 + 页脚
    d.rectangle([40, 40, W - 40, H - 40], outline=LINE, width=2)
    fy = H - 62
    d.line([(ML, fy - 16), (W - MR, fy - 16)], fill=LINE, width=1)
    d.text((ML, fy), "book-essence", font=F(MONO, 15), fill=FAINT)
    mw = F(MONO, 15).getlength("book-essence")
    d.text((ML + mw + 12, fy - 1), "·  联网查证 + 模型校准", font=fc(15), fill=FAINT)
    d.text((W - MR, fy), data.get("date", "2026.10.25"), font=F(SANS, 15), fill=FAINT, anchor="ra")

    img.save(out_path, "PNG")
    print("saved", out_path, img.size, "| content_end =", content_end)
    return out_path


DEMO = {
    "title": "反脆弱",
    "author": "纳西姆·尼古拉斯·塔勒布",
    "year": 2012,
    "subtitle": "从不确定性中获益",
    "en_title": "ANTIFRAGILE",
    "score": 8.3,
    "platforms": [("豆瓣", "7.9", 0.79), ("GOODREADS", "4.1", 0.82), ("AMAZON", "4.5", 0.90)],
    "calibration": "口碑公认现代必读，但写作散、语气犀利，部分读者嫌其傲慢；对现代学术的全盘否定亦有争议，故综合未给到 9 分。",
    "conclusion": "值得每个在不确定世界里做决策的人读——它给你一套「不预测、改暴露」的生存框架。",
    "ideas": [
        "三元分类：脆弱受冲击受损，强韧不受影响，反脆弱从冲击中获益——超越「韧性」，越挫越强。",
        "杠铃策略：大部分资源放极安全处，小部分做极端暴露，规避最危险的「中等风险」地带。",
        "减法智慧（Via Negativa）：少做蠢事比多做聪明事更有效，戒烟胜过吃补品，远离烂人胜过贵人。",
        "利益共担（Skin in the Game）：决策者必须承担后果，用别人钱冒险者是现代脆弱之源。",
        "拥抱适度波动：进化与创新靠有序的随机与压力，过度保护反而致脆。",
    ],
    "quote": "风会熄灭蜡烛，却能使火越烧越旺。你要成为火，渴望得到风的吹拂。",
    "takeaways": [
        "杠铃配置：90% 保底安全，10% 做开放式的试错赌注。",
        "先做减法：清除有毒关系、高费率产品、看不懂的标的。",
        "决策前问：若失败，谁承担后果？优先选利益共担者。",
        "主动引入小幅压力：新技能、小额试错、定期复盘。",
    ],
}

if __name__ == "__main__":
    render(DEMO, "/Users/richa/WorkBuddy/2026-10-25-11-16-35/book-essence-card.png")

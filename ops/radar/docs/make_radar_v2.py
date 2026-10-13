"""The radar's flow as an animated SVG, a GIF and an MP4: dots travel the connectors.

  python make_radar_v2.py <variant> <out-basename>     variant: prod-zh | oss-zh | oss-en

rsvg-convert renders each frame (it does not run SVG animation) and ffmpeg joins them.
"""
import math, subprocess, sys, tempfile
from pathlib import Path

W, H = 680, 770
AMB = dict(fill="#FAECE7", stroke="#993C1D", title="#712B13", sub="#993C1D")
GRY = dict(fill="#F1EFE8", stroke="#5F5E5A", title="#444441", sub="#5F5E5A")
GRN = dict(fill="#E1F5EE", stroke="#0F6E56", title="#085041", sub="#0F6E56")
BLU = dict(fill="#E6F1FB", stroke="#185FA5", title="#0C447C", sub="#185FA5")
CREDIT_TABLE = "子木 @CoderJeffLee"
CREDIT_SOURCE = "by 饭特稀 | Fentix @fantexi997"

ZH = {
    "s1": ("① X 与 HF", "每 8 小时"), "s2": ("② GitHub", "爆发仓库"), "s3": ("③ 竞品与新站", "sitemap 新页"),
    "s4": ("④ 搜索控制台", "首次曝光的词 · 可选"),
    "judge": ("名字判断：是具体名字吗", "得分 ≥ 0.5 才留下"), "known": ("剔除你已经覆盖的词",),
    "sources": ("源头报告（每 8 小时）", "有新名字才出 · 附推文原文"),
    "table": ("新词表：名字 + 它背后的通用词", "模型提词 → 相关性筛选 → 搜索量 → Trends", "每行给出：优先 / 观察 / 跳过"),
    "evidence": ("取证（AIsa）", "高赞推文 · README"), "goany": ("GoAnyAPI（可选）", "相关查询 · 美国日走势", CREDIT_SOURCE),
    "note": ("没配或挂了：表照出，", "并在表头注明「不完整」"),
    "daily": ("日报（每天一次）", "新词表在最前 · 线索存入 radar.db"),
    "review": ("14 天后 Google Trends 复核", "名字和通用词都复核 · 不计未结算的最后两天"),
    "credit": f"建议：{CREDIT_TABLE}",
    "legend": ("信号与取证", "报告产出", "这次新增", "可选来源", "命中率写回日报"),
}
PROD = {**ZH, "s2": ("② GitHub", "爆发仓库 · 共用词"), "s4": ("④ 搜索控制台", "首次曝光的词"),
        "judge": ("Jev 判断：是具体名字吗", "得分 ≥ 0.5 才留下"), "known": ("剔除已有场景页覆盖的词",),
        "sources": ("源头邮件（每 8 小时）", "有新名字才发 · 附推文原文"),
        "daily": ("日报邮件（每天 9:00）", "新词表在最前 · 线索存入线索库"),
        "legend": ("信号与取证", "邮件产出", "这次新增", "可选来源", "命中率写回日报")}
EN = {
    "s1": ("① X and HF", "every 8 hours"), "s2": ("② GitHub", "breakout repos"), "s3": ("③ Sitemaps", "pages just added"),
    "s4": ("④ Search Console", "optional"),
    "judge": ("Name judge: a name, or a common word?", "a score of 0.5 or more stays"), "known": ("Drop the terms you already cover",),
    "sources": ("Sources report (every 8 h)", "only on a new name · with the posts"),
    "table": ("Keyword table: names + generic terms", "model phrases → relevance screen → volume → Trends", "each row: prioritize / watch / skip"),
    "evidence": ("Evidence (AIsa)", "top posts · README"), "goany": ("GoAnyAPI (optional)", "related queries · US curve", CREDIT_SOURCE),
    "note": ("Not set, or down: the table is still", "written and says it is incomplete"),
    "daily": ("Daily report (once a day)", "keyword table first · leads kept in radar.db"),
    "review": ("Google Trends check, 14 days later", "names and generic terms · last two days left out"),
    "credit": f"Idea: {CREDIT_TABLE}",
    "legend": ("signals", "reports", "new", "optional", "hit rate fed back"),
}
VARIANTS = {"prod-zh": PROD, "oss-zh": ZH, "oss-en": EN}


def box(x, y, w, h, c, lines, dashed=False):
    title, *subs = lines
    cx = x + w / 2
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{c["fill"]}" stroke="{c["stroke"]}" stroke-width="{1 if dashed else 0.5}"{dash}/>']
    ty = y + h / 2 + 5 - 9.5 * len(subs)
    out.append(f'<text x="{cx}" y="{ty}" fill="{c["title"]}" font-weight="500">{title}</text>')
    out += [f'<text x="{cx}" y="{ty + 20 + 17 * i}" fill="{c["sub"]}" font-size="{11 if "@" in s else 12}">{s}</text>' for i, s in enumerate(subs)]
    return "\n".join(out)


def width(text, size):   # a CJK glyph is about a square, a Latin one about half
    return sum(size if ord(ch) > 0x2E7F else size * 0.64 for ch in text)


# id, points, colour, dashed, dot duration (s), dot begin (s)
PATHS = [
    ("p1", [(107.5, 96), (300, 150)], "#D85A30", False, 2.4, 0.0),
    ("p2", [(262.5, 96), (325, 150)], "#D85A30", False, 2.4, 0.6),
    ("p3", [(417.5, 96), (355, 150)], "#D85A30", False, 2.4, 1.2),
    ("p4", [(572.5, 96), (380, 150)], "#D85A30", False, 2.4, 1.8),
    ("p5", [(340, 206), (340, 236)], "#888780", False, 1.2, 0.3),
    ("p6", [(290, 284), (175, 322)], "#1D9E75", False, 1.6, 0.0),
    ("p7", [(400, 284), (455, 316)], "#378ADD", False, 1.6, 0.4),
    ("p8", [(380, 444), (410, 402)], "#D85A30", False, 1.6, 0.8),
    ("p9", [(552.5, 444), (530, 402)], "#378ADD", True, 1.6, 1.2),
    ("p10", [(310, 380), (290, 380), (290, 568)], "#1D9E75", False, 2.4, 0.2),
    ("p11", [(340, 624), (340, 662)], "#888780", False, 1.2, 0.6),
    ("p12", [(490, 690), (650, 690), (650, 596), (490, 596)], "#888780", True, 4.8, 0.0),
]
DASH = ' stroke-dasharray="4 3"'


def scene(T):
    boxes = "\n".join([
        box(40, 40, 135, 56, AMB, T["s1"]), box(195, 40, 135, 56, AMB, T["s2"]),
        box(350, 40, 135, 56, AMB, T["s3"]), box(505, 40, 135, 56, AMB, T["s4"]),
        box(190, 150, 300, 56, GRY, T["judge"]), box(190, 236, 300, 48, GRY, T["known"]),
        box(40, 322, 230, 56, GRN, T["sources"]), box(310, 316, 330, 86, BLU, T["table"]),
        box(310, 444, 140, 56, AMB, T["evidence"]), box(465, 444, 175, 72, BLU, T["goany"], dashed=True),
        box(190, 568, 300, 56, GRN, T["daily"]), box(190, 662, 300, 56, GRY, T["review"]),
    ])
    lines = "\n".join(f'<path id="{i}" d="M{" L".join(f"{x} {y}" for x, y in p)}" fill="none" stroke="{c}" stroke-width="1"'
                      f'{DASH if dash else ""} marker-end="url(#arrow)"/>' for i, p, c, dash, *_ in PATHS)
    notes = (f'<text x="640" y="309" text-anchor="end" font-size="11" fill="#185FA5">{T["credit"]}</text>'
             + "".join(f'<text x="552.5" y="{536 + 15 * i}" text-anchor="middle" font-size="11" fill="#A32D2D">{s}</text>' for i, s in enumerate(T["note"])))
    swatches = [f'fill="{AMB["fill"]}" stroke="{AMB["stroke"]}" stroke-width="0.5"', f'fill="{GRN["fill"]}" stroke="{GRN["stroke"]}" stroke-width="0.5"',
                f'fill="{BLU["fill"]}" stroke="{BLU["stroke"]}" stroke-width="0.5"', 'fill="none" stroke="#185FA5" stroke-width="1" stroke-dasharray="4 3"']
    widths = [22 + width(s, 12) for s in T["legend"][:4]] + [38 + width(T["legend"][4], 12)]
    gap = (W - 80 - sum(widths)) / 4
    x, legend = 40, ""
    for i, label in enumerate(T["legend"]):
        if i < 4:
            legend += f'<rect x="{x:.0f}" y="740" width="14" height="14" rx="3" {swatches[i]}/><text x="{x + 22:.0f}" y="752" font-size="12" fill="#444441">{label}</text>'
        else:
            legend += f'<path d="M{x:.0f} 747 H{x + 30:.0f}" stroke="#888780" stroke-width="1" stroke-dasharray="4 3" fill="none"/><text x="{x + 38:.0f}" y="752" font-size="12" fill="#444441">{label}</text>'
        x += widths[i] + gap
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 2}" height="{H * 2}" viewBox="0 0 {W} {H}" '
            'font-family="PingFang SC, Noto Sans CJK SC, Noto Sans SC, sans-serif">\n'
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>\n'
            f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>\n')
    return head, f'{lines}\n<g font-size="14" text-anchor="middle">\n{boxes}\n</g>\n{notes}\n{legend}\n'


def at(points, f):
    seg = [math.dist(a, b) for a, b in zip(points, points[1:])]
    left = f * sum(seg)
    for (a, b), s in zip(zip(points, points[1:]), seg):
        if left <= s:
            k = left / s if s else 0
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        left -= s
    return points[-1]


def main(variant, base):
    head, body = scene(VARIANTS[variant])
    smil = "\n".join(f'<circle r="4" fill="{c}"><animateMotion dur="{dur}s" repeatCount="indefinite" begin="{b}s"><mpath href="#{i}"/></animateMotion></circle>'
                     for i, _, c, _, dur, b in PATHS)
    Path(base + ".svg").write_text(head + body + smil + "\n</svg>\n")
    fps, seconds = 15, 4.8
    with tempfile.TemporaryDirectory() as tmp:
        for n in range(int(fps * seconds)):
            tm = n / fps
            dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{c}"/>'
                           for _, p, c, _, dur, b in PATHS for x, y in [at(p, ((tm - b) % dur) / dur)])
            f = Path(tmp) / f"f{n:03d}.svg"
            f.write_text(head.replace("context-stroke", "#888780") + body + dots + "\n</svg>\n")
            subprocess.run(["rsvg-convert", "-w", str(W * 2), "-b", "white", str(f), "-o", str(f.with_suffix(".png"))], check=True)
        frames = ["-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/f%03d.png"]
        subprocess.run(["ffmpeg", *frames, "-vf", "scale=1020:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none", base + ".gif"], check=True)
        subprocess.run(["ffmpeg", *frames, "-vf", "scale=1360:-2", "-pix_fmt", "yuv420p", "-movflags", "+faststart", base + ".mp4"], check=True)
        subprocess.run(["cp", f"{tmp}/f030.png", base + ".png"], check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

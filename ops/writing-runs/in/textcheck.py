"""Text helpers for the tests whose deliverable is a document (ops/summary-runs, ops/writing-runs).

The same file sits in ops/summary-runs/in/ and ops/writing-runs/in/: each sandbox mounts only its
own in/, so each needs its copy. Keep the two identical (score.py of each test says so when they
are not). Standard library only: it runs in the sandbox (Python 3.11) and on the Mac (3.14).

    read(path)            the text of a delivered file: Markdown and text as they are; Word (.docx)
                          paragraphs as lines (headings as "# ", list paragraphs as "- ", table rows
                          as "| a | b |"); HTML without its tags; PDF through pdftotext
    deliverable(folder)   the file a person would open in output/ (see its docstring)
    plain(text)           the text without Markdown marks, for counting
    zi(text)              字数 the way Word and WPS count it: every Chinese character and full-width
                          punctuation mark is one, every run of Latin letters or digits is one
    figures(text)         every figure in a text, normalised: dates, times, percentages, numbers
                          (万 and 千 multiplied out, Chinese numerals before a measure word converted)
    figure_set(text)      the figures of a source text, for figure_in()
    figure_in(f, s)       is figure f (from figures()) also in source set s?
    units(text)           the text cut into units a reader takes in one go: table rows, list items
                          (with their sub-items), sentences; each knows the heading it sits under
    to_html(), shoot()    the document as a page with marked passages, and that page as a PNG
"""
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

# ---- reading ---------------------------------------------------------------------------------

DOC_TYPES = (".docx", ".md", ".markdown", ".txt", ".html", ".htm", ".pdf")   # preference order when nothing names one
GUIDE_STEMS = {"说明", "start", "readme", "使用说明"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def _docx_styles(z: zipfile.ZipFile) -> dict:
    """styleId -> style name (Chinese Word saves headings as ids "1", "2" with names "heading 1")."""
    try:
        root = ElementTree.fromstring(z.read("word/styles.xml"))
    except KeyError:
        return {}
    out = {}
    for s in root.iter(W + "style"):
        name = s.find(W + "name")
        out[s.get(W + "styleId")] = (name.get(W + "val") if name is not None else "") or ""
    return out


def _docx_para(p, styles: dict) -> str:
    parts = []
    for node in p.iter():
        if node.tag == W + "t":
            parts.append(node.text or "")
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            parts.append("\n")
    text = "".join(parts).strip()
    if not text:
        return ""
    ppr = p.find(W + "pPr")
    style = ""
    if ppr is not None and ppr.find(W + "pStyle") is not None:
        sid = ppr.find(W + "pStyle").get(W + "val") or ""
        style = (styles.get(sid) or sid).lower()
    level = re.search(r"(?:heading|标题)\s*(\d)", style)
    if level:
        return "#" * min(int(level.group(1)), 6) + " " + text
    if style in ("title", "标题") or style.startswith("title"):
        return "# " + text
    if (ppr is not None and ppr.find(W + "numPr") is not None) or "list" in style or "列表" in style:
        return "- " + text
    return text


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        styles = _docx_styles(z)
        body = ElementTree.fromstring(z.read("word/document.xml")).find(W + "body")
    lines = []
    for child in list(body) if body is not None else []:
        if child.tag == W + "p":
            line = _docx_para(child, styles)
            if line:
                lines.append(line)
        elif child.tag == W + "tbl":
            for tr in child.iter(W + "tr"):
                cells = [" ".join(_docx_para(p, styles).lstrip("#- ").strip() for p in tc.iter(W + "p")).strip()
                         for tc in tr.findall(W + "tc")]
                lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
            lines.append("")
    return "\n".join(lines)


class _HtmlText(HTMLParser):
    BLOCK = {"p", "div", "section", "article", "br", "tr", "table", "ul", "ol", "blockquote", "header", "footer", "main"}

    def __init__(self):
        super().__init__()
        self.out, self.skip, self.cells = [], 0, None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self.skip += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.out.append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag == "tr":
            self.cells = []
        elif tag in ("td", "th") and self.cells is not None:
            self.cells.append("")
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head"):
            self.skip = max(0, self.skip - 1)
        elif tag == "tr" and self.cells is not None:
            self.out.append("\n| " + " | ".join(c.strip() for c in self.cells) + " |\n")
            self.cells = None
        elif tag in self.BLOCK or re.fullmatch(r"h[1-6]", tag):
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        if self.cells is not None and self.cells:
            self.cells[-1] += data
        elif self.cells is None:
            self.out.append(data)


def _html_text(raw: str) -> str:
    p = _HtmlText()
    p.feed(raw)
    return re.sub(r"\n{3,}", "\n\n", "".join(p.out)).strip()


def read(path) -> str:
    """The text of a delivered document (see the module docstring); "" when it cannot be read."""
    path = Path(path)
    ext = path.suffix.lower()
    try:
        if ext == ".docx":
            return _docx_text(path)
        if ext in (".html", ".htm"):
            return _html_text(_decode(path.read_bytes()))
        if ext == ".pdf":
            exe = shutil.which("pdftotext")
            if not exe:
                return ""
            return subprocess.run([exe, "-layout", str(path), "-"], capture_output=True, text=True, timeout=60).stdout
        return _decode(path.read_bytes())
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError, KeyError, subprocess.SubprocessError):
        return ""


def candidates(folder) -> list:
    """Every document in a delivered folder that could be the deliverable (not a guide, not hidden)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    out = []
    for f in sorted(folder.rglob("*")):
        rel = f.relative_to(folder).parts
        if not f.is_file() or any(p.startswith(".") or p in ("node_modules", "__pycache__") for p in rel):
            continue
        if f.suffix.lower() in DOC_TYPES and f.stem.lower() not in GUIDE_STEMS and not f.name.startswith("~$"):
            out.append(f)
    return out


def deliverable(folder):
    """The document a person would open: the only one there; else the one 说明.txt names (first named);
    else by type (.docx, then .md, .txt, .html, .pdf), the largest of that type. None when there is none."""
    files = candidates(folder)
    if len(files) <= 1:
        return files[0] if files else None
    guide = Path(folder) / "说明.txt"
    if guide.exists():
        said = _decode(guide.read_bytes())
        named = sorted((said.find(f.name), f) for f in files if f.name in said)
        if named:
            return named[0][1]
    rank = {e: i for i, e in enumerate(DOC_TYPES)}
    return sorted(files, key=lambda f: (rank[f.suffix.lower()], -f.stat().st_size))[0]


# ---- counting ----------------------------------------------------------------------------------

CJK = "㐀-䶿一-鿿豈-﫿"
CJK_PUNCT = "　-〿＀-￯‘’“”—…·"


def plain(text: str) -> str:
    """Markdown marks taken out: headings, emphasis, list and quote markers, table pipes, links, HTML tags."""
    out = []
    for line in text.splitlines():
        if re.fullmatch(r"\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*", line):
            continue                                            # a table's separator row
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*>\s?", "", line)
        line = re.sub(r"^\s*(?:[-*+•]|\d+[.)])\s+(\[[ xX]\]\s*)?", "", line)
        line = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"<[^>]+>", "", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        line = re.sub(r"(?<![\w*])\*(?!\s)([^*]+)(?<!\s)\*(?![\w*])", r"\1", line)
        if line.strip().startswith("|"):
            line = " ".join(c.strip() for c in line.strip().strip("|").split("|"))
        out.append(line)
    return "\n".join(out)


def zi(text: str) -> int:
    """字数 as Word and WPS count it, Markdown marks left out."""
    t = plain(text)
    return len(re.findall(f"[{CJK}{CJK_PUNCT}]", t)) + len(re.findall(r"[A-Za-z0-9]+(?:[.,'’%][A-Za-z0-9]+)*%?", t))


# ---- figures -----------------------------------------------------------------------------------

CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNIT = {"十": 10, "百": 100, "千": 1000, "万": 10000}
MEASURE = ("个月|个|项|条|名|人|位|次|遍|天|周|月|年|倍|分钟|小时|秒|步|篇|件|起|笔|元|块|家|款|版|期|轮|场|份|页|张|台|"
           "折|成|类|种|处|点|层|级|套|批|单|岁|季度|部|组|节|款|分")
PERIOD = {"凌晨": 0, "早上": 0, "早晨": 0, "上午": 0, "早": 0, "中午": 12, "下午": 12, "傍晚": 12, "晚上": 12, "夜里": 12,
          "夜间": 12, "晚": 12}
SELF_COUNT = re.compile(r"^\s*(?:(?:项|条|个|件|点|大|类|块)\s*(?:决定|决议|结论|待办|行动项?|任务|事项|未决|待定|议题|"
                        r"共识|要点|方面|部分|板块|重点|事情|事|内容|亮点|建议)|方面|部分|大块)")
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"


def cn_number(s: str):
    """A Chinese numeral as an int (三 3, 十二 12, 二十五 25, 两百 200, 一万二 12000); None for 两三 and the like."""
    if not s or any(c not in CN_DIGIT and c not in CN_UNIT for c in s):
        return None
    if len(s) > 1 and all(c in CN_DIGIT for c in s):
        return None                                  # 两三, 五六: a vague range, not a number
    total, section, digit = 0, 0, None
    for c in s:
        if c in CN_DIGIT:
            if digit is not None:
                return None
            digit = CN_DIGIT[c]
        else:
            unit = CN_UNIT[c]
            if unit == 10000:
                total += (section + (digit or 0)) * unit
                section, digit = 0, None
            else:
                section += (1 if digit is None else digit) * unit
                digit = None
    tail = digit or 0
    if digit is not None and len(s) >= 2 and s[-2] in CN_UNIT and CN_UNIT[s[-2]] >= 100:
        tail = digit * CN_UNIT[s[-2]] // 10                  # 一万二 = 12000, 三百五 = 350
    return total + section + tail


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def _hour(period: str, h: int) -> int:
    add = PERIOD.get(period or "", None)
    if add is None:
        return h
    return h + 12 if add == 12 and h < 12 else (0 if add == 0 and h == 12 else h)


def figures(text: str) -> list:
    """Every figure in the text, in order: {"raw", "kind", "value", "start", "end"}.
    kind: date (value [month, day]), day ([day]), time ([hour, minute], or "hours" [h, h+12] for a bare
    "8 点"), percent, number (万/千/w/k multiplied out, "raw_value" keeping the figure as written; a
    duration such as 2 分 40 秒 in seconds, 160), stamp (a transcript time stamp, [00:01:23] or a
    citation of one, [01:23], in seconds).
    Left out, as not figures a reader takes for facts: list numbers at a line's
    start, ordinals (第 3), weekdays (周三), version strings (1.9.3), labels (3P, Q4, iPhone 15), a lone 一,
    vague ranges (两三天) and counts of a document's own parts ("7 项决定", "三个方面"), kept as kind "self"."""
    taken = []
    out = []

    def free(a, b):
        return all(b <= x or a >= y for x, y in taken)

    def add(m, kind, value, group=0, **extra):
        a, b = m.span(group)
        if not free(a, b):
            return False
        taken.append((a, b))
        out.append({"raw": m.group(group), "kind": kind, "value": value, "start": a, "end": b, **extra})
        return True

    def skip(m):
        if free(*m.span()):
            taken.append(m.span())

    for m in re.finditer(r"[\[【`]\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*[\]】`]|(?<![\d:])(\d{1,2}):(\d{2}):(\d{2})(?![\d:])", text):
        g = m.groups()                                                                    # time stamps: [00:01:23], [01:23]
        secs = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) if g[2] else int(g[0]) * 60 + int(g[1]) if g[0] else \
            int(g[3]) * 3600 + int(g[4]) * 60 + int(g[5])
        add(m, "stamp", secs)
    for m in re.finditer(r"(?<![\d.])\d+(?:\.\d+){2,}(?![\d.])", text):                    # version strings
        skip(m)
    for m in re.finditer(r"(?m)^[ \t>#]*(?:[-*+]\s+)?(?:\*\*)?(?:\d{1,2}[.、)）．](?!\d)|[（(]\d{1,2}[)）]|[①-⑳])", text):   # list numbers
        skip(m)
    for m in re.finditer(r"第\s*(?:\d+|[一二三四五六七八九十百]+)", text):                     # ordinals
        skip(m)
    for m in re.finditer(r"(?:周|星期|礼拜)[一二三四五六日天末]", text):
        skip(m)
    for m in re.finditer(r"(?<![A-Za-z])[A-Za-z]{1,12}\d+(?:\.\d+)?(?![\d.%])|(?<![\d.])\d+[A-Za-z]{2,}|(?<![\d.])\d+[A-VX-Za-jl-vx-z](?![A-Za-z])", text):
        skip(m)                                                                            # labels: Q4, H5, v2.0, 3P, 5G
    for m in re.finditer(r"(?m)^\s*\|\s*(\d{1,2})\s*\|", text):                          # a table's row numbers
        if free(*m.span(1)):
            taken.append(m.span(1))
    for m in re.finditer(r"(\d{4})\s*[年/.-]\s*(\d{1,2})\s*[月/.-]\s*(\d{1,2})(?:\s*[日号])?", text):
        if add(m, "date", [int(m.group(2)), int(m.group(3))], year=int(m.group(1))):
            out.append({"raw": m.group(1), "kind": "number", "value": float(m.group(1)), "start": m.start(1), "end": m.end(1)})
    for m in re.finditer(r"(?<![\d.])(1[0-2]|0?[1-9])\s*月\s*(3[01]|[12]\d|0?[1-9])(?:\s*[日号])?(?![\d.])(?!,\d)"
                         r"(?!\s*[%％万千亿元块单篇人次起分秒个件条名位倍岁台家笔])", text):
        add(m, "date", [int(m.group(1)), int(m.group(2))])
    for m in re.finditer(r"(?<![\d./:])(1[0-2]|0?[1-9])\s*/\s*(3[01]|[12]\d|0?[1-9])(?![\d./%])", text):
        add(m, "date", [int(m.group(1)), int(m.group(2))])
    for m in re.finditer(r"(?<![\d\-./:])(1[0-2]|0?[1-9])-(3[01]|[12]\d|0?[1-9])(?![\d\-./:%％])"
                         r"(?!\s*[月日号天周年个人次步分小时万千元])", text):          # 11-27; not 7-9 月 or 2-3 天
        add(m, "date", [int(m.group(1)), int(m.group(2))])
    for m in re.finditer(r"(?<![\d.])(1[0-2]|0?[1-9])\.(3[01]|[12]\d|0?[1-9])(?=\s*(?:前|之前|以前|截止|到期|上线|发布|完成|交|日|号|[（(]\s*(?:周|星期|礼拜)))", text):
        add(m, "date", [int(m.group(1)), int(m.group(2))])
    for m in re.finditer(r"(凌晨|早上|早晨|上午|中午|下午|傍晚|晚上|夜里|夜间|晚)?\s*(\d{1,2})\s*[:：]\s*(\d{2})(?![\d:])", text):
        add(m, "time", [_hour(m.group(1), int(m.group(2))), int(m.group(3))])
    for m in re.finditer(r"(凌晨|早上|早晨|上午|中午|下午|傍晚|晚上|夜里|夜间|晚)\s*(\d{1,2}|[一二两三四五六七八九十]{1,3})\s*点(半|\s*\d{1,2}\s*分)?", text):
        h = int(m.group(2)) if m.group(2).isdigit() else cn_number(m.group(2))
        if h is not None:
            mins = 30 if m.group(3) == "半" else int(re.sub(r"\D", "", m.group(3))) if m.group(3) else 0
            add(m, "time", [_hour(m.group(1), h), mins])
    for m in re.finditer(r"(?<![\d.])(\d{1,2})\s*点(半)?(?![\d多])", text):
        h = int(m.group(1))
        if h <= 24:
            add(m, "hours", [h, h + 12 if h < 12 else h], minute=30 if m.group(2) else 0)
    for m in re.finditer(r"(?<![\d.])(\d{1,3})\s*分(?:钟)?\s*(\d{1,2})\s*秒", text):          # 2 分 40 秒 = 160 秒
        add(m, "number", float(int(m.group(1)) * 60 + int(m.group(2))), unit="sec")
    for m in re.finditer(r"(?<![\d.])(\d{1,2})\s*[日号](?![\d])", text):
        add(m, "day", [int(m.group(1))])
    for m in re.finditer(rf"(?<![\d.])({NUM})\s*[%％]", text):
        add(m, "percent", _num(m.group(1)))
    for m in re.finditer(r"百分之([零一二两三四五六七八九十百]+)", text):
        v = cn_number(m.group(1))
        if v is not None:
            add(m, "percent", float(v))
    for m in re.finditer(r"([一二两三四五六七八九十]+|\d+)\s*分之\s*([一二两三四五六七八九十]+|\d+)", text):   # 三分之一: a share
        a, b = (int(g) if g.isdigit() else cn_number(g) for g in m.groups())
        if a and b and b <= a:
            add(m, "percent", round(b / a * 100, 4), fraction=True)
    for m in re.finditer(rf"(?<![\d.])({NUM})\s*(万|千|亿|[wW](?![A-Za-z])|[kK](?![A-Za-z]))", text):
        mult = {"万": 1e4, "千": 1e3, "亿": 1e8, "w": 1e4, "W": 1e4, "k": 1e3, "K": 1e3}[m.group(2)]
        rest = text[m.end():m.end() + 8]
        if SELF_COUNT.match(rest):
            add(m, "self", _num(m.group(1)) * mult)
        else:
            add(m, "number", round(_num(m.group(1)) * mult, 4), raw_value=_num(m.group(1)))
    for m in re.finditer(rf"(?<![\d.])({NUM})(?![\d])", text):
        rest = text[m.end():m.end() + 8]
        add(m, "self" if SELF_COUNT.match(rest) else "number", _num(m.group(1)))
    for m in re.finditer(rf"(?<![第周双星期礼拜几])([零〇一二两三四五六七八九十百千万]+)(?=\s*(?:{MEASURE}))(?!分[点比之])", text):
        s_ = m.group(1)
        if not any(c in CN_DIGIT for c in s_) and not s_.startswith("十"):
            continue                                      # 百 of 百分点, 万 of 万一: not a number
        v = cn_number(s_)
        if v is None or v == 1:
            continue
        rest = text[m.end():m.end() + 8]
        add(m, "self" if SELF_COUNT.match(rest) else "number", float(v), cn=True)
    for m in re.finditer(r"([一二两三四五六七八九十]+)(?=\s*(?:成|折))", text):        # 七折, 三成
        v = cn_number(m.group(1))
        if v is not None and v > 1:
            add(m, "number", float(v), cn=True)
    return sorted(out, key=lambda f: f["start"])


UNIT_HEAD = re.compile(r"[（(]\s*(万元|万|千元|千|元|%|％|秒|分钟|小时|天|人|单|篇|起|次|个)\s*[)）]")


def with_table_units(text: str) -> str:
    """The text with a table's column unit written after each bare number in that column: under a
    header 金额（万元）, a cell 15 becomes 15 万, so it reads as the figure it is."""
    out, units = [], None
    for line in text.splitlines(keepends=True):
        st = line.strip()
        if not st.startswith("|"):
            units = None
            out.append(line)
            continue
        if TABLE_SEP.match(st):
            out.append(line)
            continue
        cells = st.strip("|").split("|")
        if units is None:                                   # the header row
            units = [(m.group(1) if (m := UNIT_HEAD.search(c)) else "") for c in cells]
            out.append(line)
            continue
        for i, c in enumerate(cells):
            u = {"万元": "万", "千元": "千", "％": "%"}.get(units[i] if i < len(units) else "", units[i] if i < len(units) else "")
            if u and re.fullmatch(r"\s*\**\s*\d+(?:\.\d+)?\s*\**\s*", c):
                cells[i] = re.sub(r"(\d+(?:\.\d+)?)", lambda m: m.group(1) + ("%" if u == "%" else " " + u), c, count=1)
        out.append("| " + " | ".join(x.strip() for x in cells) + " |\n")
    return "".join(out)


def figure_set(text: str) -> dict:
    """The figures of a source text, by kind, for figure_in()."""
    s = {"number": set(), "percent": set(), "wan": set(), "date": set(), "day": set(), "time": set(), "stamp": set()}
    for f in figures(text):
        k, v = f["kind"], f["value"]
        if k == "number":
            s["number"].add(round(v, 4))
            if "raw_value" in f:
                s["wan"].add(round(f["raw_value"], 4))
        elif k == "percent":
            s["percent"].add(round(v, 4))
        elif k == "date":
            s["date"].add(tuple(v))
            s["day"].add(v[1])
        elif k == "day":
            s["day"].add(v[0])
        elif k == "time":
            s["time"].add(tuple(v))
        elif k == "hours":
            s["time"].update({(v[0], f["minute"]), (v[1], f["minute"])})
        elif k == "stamp":
            s["stamp"].add(v)
    return s


def figure_in(f: dict, s: dict) -> bool:
    """Is a figure (from figures()) in the source set? A date by month and day, a day by itself, a time
    by hour and minute (a bare "8 点" as 8:00 or 20:00), a percentage or number by value (41% matches
    41; 3.8 万 matches 38,000 and another 3.8 万, not a bare 3.8 or 3), a number written like a date
    (11.13) by the date."""
    k, v = f["kind"], f["value"]
    if k == "date":
        return tuple(v) in s["date"]
    if k == "day":
        return v[0] in s["day"]
    if k == "time":
        return tuple(v) in s["time"]
    if k == "stamp":                                       # a citation of the record's time stamp: it must exist
        return v in s["stamp"]
    if k == "hours":
        return (v[0], f["minute"]) in s["time"] or (v[1], f["minute"]) in s["time"] or float(v[0]) in s["number"]
    if k in ("number", "percent"):
        if round(v, 4) in s["number"] | s["percent"] or ("raw_value" in f and round(f["raw_value"], 4) in s["wan"]):
            return True
        md = as_date(f)
        return bool(md and md in s["date"])                  # 11.13 written for 11 月 13 日
    return True


def as_date(f: dict):
    """A number written like a date (11.13, 9.26) as (month, day), else None."""
    m = re.fullmatch(r"(1[0-2]|0?[1-9])\.(3[01]|[12]\d|0?[1-9])", f.get("raw", "").strip()) if f.get("kind") == "number" else None
    return (int(m.group(1)), int(m.group(2))) if m else None


# ---- units -------------------------------------------------------------------------------------

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")
BOLD_LINE = re.compile(r"^\s*\*\*([^*]{1,40})\*\*\s*[:：]?\s*$")
CN_HEADING = re.compile(r"^\s*((?:[一二三四五六七八九十]+、|[（(][一二三四五六七八九十]+[)）]|Part\s*\d+[.:：]?)\s*[^。！？]{1,24})\s*$")
COLON_HEADING = re.compile(r"^\s*([^\s|#>*-][^。！？|]{0,15}?)\s*[:：]\s*$")
LIST = re.compile(r"^(\s*)(?:[-*+](?=\s)|[•·]|\d{1,2}[.、)）．](?!\d)|[（(]\d{1,2}[)）]|[①-⑳]|[a-zA-Z][.)](?=\s))\s*(?:\[[ xX]\]\s*)?(.*)$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
SENTENCE_END = re.compile(r"(?<=[。！？；!?;])")


def _inline(s: str) -> str:
    return plain(s).strip()


def units(text: str, coarse: bool = False) -> list:
    """The text cut into units: {"text", "kind" (row, header, item, sentence), "section" (the nearest
    heading's text, "" before any), "parent" (a list item's parent item), "line"}. A list item's text
    includes its sub-items ("whole" too, for an item); a paragraph is cut into sentences, or kept
    whole with coarse=True."""
    lines = text.splitlines()
    out, section, para, para_line = [], "", [], 0
    stack = []                       # open list items: (indent, unit)
    table_head = False

    def flush_para():
        nonlocal para
        if para:
            joined = _inline(" ".join(para))
            for s in ([joined] if coarse else SENTENCE_END.split(joined)):
                if s.strip():
                    out.append({"text": s.strip(), "kind": "sentence", "section": section, "parent": "", "line": para_line})
        para = []

    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if not line.strip():
            flush_para(); stack.clear(); table_head = False
            continue
        h = HEADING.match(line) or BOLD_LINE.match(line) or CN_HEADING.match(line) or COLON_HEADING.match(line)
        if h and not line.strip().startswith("|"):
            flush_para(); stack.clear()
            section = _inline(h.group(h.lastindex))
            out.append({"text": section, "kind": "heading", "section": section, "parent": "", "line": i})
            continue
        if line.strip().startswith("|"):
            flush_para(); stack.clear()
            if TABLE_SEP.match(line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            kind = "header" if not table_head else "row"
            table_head = True
            out.append({"text": _inline(" | ".join(cells)), "kind": kind, "section": section, "parent": "", "line": i})
            continue
        m = LIST.match(line)
        if m and m.group(2).strip():
            flush_para()
            indent = len(m.group(1).replace("\t", "    "))
            while stack and stack[-1][0] >= indent:
                stack.pop()
            parent = stack[-1][1] if stack else None
            u = {"text": _inline(m.group(2)), "kind": "item", "section": section, "parent": parent["text"] if parent else "", "line": i}
            u["whole"] = u["text"]
            for _, anc in stack:
                anc["whole"] += " " + u["text"]
            out.append(u)
            stack.append((indent, u))
            continue
        if stack and raw.startswith((" ", "\t")):
            stack[-1][1]["text"] += " " + _inline(line)
            for _, anc in stack:
                anc["whole"] += " " + _inline(line)
            continue
        stack.clear(); table_head = False
        if not para:
            para_line = i
        para.append(line)
    flush_para()
    return out


def scope(u: dict) -> str:
    """What a unit says together with where it sits: its text, its sub-items, its parent and its heading."""
    return " ".join(x for x in (u.get("whole") or u["text"], u.get("parent", ""), u.get("section", "")) if x)


def has_all(text: str, groups) -> bool:
    return all(re.search(g, text) for g in groups)


# ---- the page and its picture -------------------------------------------------------------------

PAGE_CSS = """:root{--bg:#fff;--fg:#1f2328;--mute:#59636e;--line:#d0d7de;--card:#f6f8fa;--ok:#1a7f37;--no:#cf222e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.75 "PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif}
main{width:%dpx;padding:28px 36px 36px}h1,h2,h3,h4{line-height:1.4;margin:18px 0 8px}h1{font-size:26px}h2{font-size:21px}h3{font-size:18px}
p{margin:6px 0}ul,ol{margin:4px 0;padding-left:24px}li{margin:2px 0}table{border-collapse:collapse;margin:8px 0;font-size:15px;width:100%%}
th,td{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}th{background:var(--card)}
blockquote{margin:6px 0;padding:2px 12px;border-left:4px solid var(--line);color:var(--mute)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:0 0 18px;font-size:15px;line-height:1.6}
.card b{font-size:17px}.ok{color:var(--ok);font-weight:700}.no{color:var(--no);font-weight:700}.mute{color:var(--mute)}
.doc{border:1px solid var(--line);border-radius:10px;padding:8px 24px 16px}
mark{padding:0 2px;border-radius:3px}mark.bad{background:#ffd7d5;color:#82071e;font-weight:600}mark.warn{background:#fff1a8}
mark.good{background:#d1f5d3}mark.info{background:#ddf4ff}mark.line{background:none;border-bottom:3px solid #fb8f44}
.legend span{display:inline-block;margin-right:14px}"""


def _fits(escaped: str, i: int, j: int, before: str, after: str) -> bool:
    """Do the characters around escaped[i:j] match a mark's context? A context opened by START (or
    closed by END) must reach the edge of the piece (a line's content or a table cell); empty: any."""
    if before.startswith(START):
        ok = escaped[:i].lstrip() == html.escape(before[1:])
    else:
        ok = escaped[:i].endswith(html.escape(before))
    if after.endswith(END):
        return ok and escaped[j:].rstrip() == html.escape(after[:-1])
    return ok and escaped.startswith(html.escape(after), j)


START, END = "\x02", "\x03"


def _mark(escaped: str, marks) -> str:
    """Wrap every occurrence of each marked text (longest first) in <mark class=…>; one pass, no nesting.
    A mark (text, class, tooltip, before, after) with a context marks only the occurrences it fits."""
    spans = []
    for m in sorted(marks, key=lambda m: -len(m[0])):
        needle = html.escape(m[0])
        if not needle.strip():
            continue
        before, after = (m[3] if len(m) > 3 else "") or "", (m[4] if len(m) > 4 else "") or ""
        start = 0
        while (i := escaped.find(needle, start)) >= 0:
            j = i + len(needle)
            if _fits(escaped, i, j, before, after) and all(j <= a or i >= b for a, b, _, _ in spans):
                spans.append((i, j, m[1], m[2] if len(m) > 2 else ""))
            start = j
    for a, b, cls, title in sorted(spans, reverse=True):
        t = f' title="{html.escape(title)}"' if title else ""
        escaped = escaped[:a] + f'<mark class="{cls}"{t}>' + escaped[a:b] + "</mark>" + escaped[b:]
    return escaped


def _md_inline(s: str, marks) -> str:
    e = _mark(html.escape(s), marks)
    e = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e)
    e = re.sub(r"`([^`]+)`", r"<code>\1</code>", e)
    return e


def to_html(text: str, marks=(), title: str = "", card: str = "", width: int = 1000) -> str:
    """The document as a page: Markdown headings, lists, tables and quotes kept, the marked passages
    highlighted (marks: (text, class, tooltip); classes bad, warn, good, info, line), a summary card on top."""
    body, in_list, rows = [], None, []

    def close():
        nonlocal in_list, rows
        if in_list:
            body.append(f"</{in_list}>"); in_list = None
        if rows:
            head, *rest = rows
            body.append("<table><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr>" +
                        "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rest) + "</table>")
            rows = []

    for line in text.splitlines():
        if not line.strip():
            close(); continue
        if line.strip().startswith("|"):
            if in_list:
                body.append(f"</{in_list}>"); in_list = None
            if not TABLE_SEP.match(line):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                here = [m for m in marks if len(m) < 6 or not m[5] or m[5] == cells[0]]   # a cell mark: its row only
                rows.append([_md_inline(c, here) for c in cells])
            continue
        if rows:
            close()
        h = HEADING.match(line)
        if h:
            close(); n = len(h.group(1))
            body.append(f"<h{n}>{_md_inline(h.group(2), marks)}</h{n}>"); continue
        m = LIST.match(line)
        if m and m.group(2).strip():
            tag = "ol" if re.match(r"\s*\d", line) else "ul"
            if in_list != tag:
                if in_list:
                    body.append(f"</{in_list}>")
                body.append(f"<{tag}>"); in_list = tag
            pad = len(m.group(1).replace("\t", "    ")) * 6
            body.append(f'<li style="margin-left:{pad}px">{_md_inline(m.group(2), marks)}</li>'); continue
        if line.lstrip().startswith(">"):
            close(); body.append(f"<blockquote>{_md_inline(line.lstrip()[1:].strip(), marks)}</blockquote>"); continue
        close()
        body.append(f"<p>{_md_inline(line.strip(), marks)}</p>")
    close()
    head = f"<title>{html.escape(title)}</title>" if title else ""
    return (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">{head}<style>{PAGE_CSS % width}</style></head>'
            f'<body><main>{card}<div class="doc">{"".join(body)}</div></main></body></html>')


CHROME = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium",
          "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]


def _crop(png: Path, bg=(255, 255, 255)) -> None:
    """Cut the empty space under the page (the window is taller than the page)."""
    try:
        from PIL import Image
    except ImportError:
        return
    im = Image.open(png).convert("RGB")
    w, h = im.size
    px = im.load()
    bottom = h - 1
    step = max(1, w // 200)
    while bottom > 0 and all(px[x, bottom] == bg for x in range(0, w, step)):
        bottom -= 1
    im.crop((0, 0, w, min(h, bottom + 24))).save(png)


def shoot(page_html: str, png, width: int = 1000, scale: int = 2, max_height: int = 12000) -> Path:
    """The page as a PNG, width CSS pixels at `scale` (2: sharp enough for a video frame). Uses
    Playwright when it is installed (the sandbox), else Chrome or Chromium headless (the Mac)."""
    png = Path(png)
    png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(page_html, encoding="utf-8")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                exe = next((c for c in CHROME if os.path.exists(c)), None)
                b = pw.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else pw.chromium.launch()
                p = b.new_page(viewport={"width": width, "height": 800}, device_scale_factor=scale)
                p.goto(page.as_uri())
                p.screenshot(path=str(png), full_page=True)
                b.close()
            return png
        except ImportError:
            pass
        exe = next((c for c in CHROME if os.path.exists(c)), None)
        if not exe:
            raise RuntimeError("no Playwright and no Chrome/Chromium to take the picture with")
        subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--force-device-scale-factor={scale}",
                        f"--window-size={width},{max_height}", f"--screenshot={png}", "--no-first-run",
                        "--no-default-browser-check", f"--user-data-dir={tmp}/profile", page.as_uri()],
                       capture_output=True, timeout=120)
        if not png.exists():
            raise RuntimeError("Chrome made no picture")
        _crop(png)
        return png


def save_json(obj, path) -> None:
    Path(path).expanduser().write_text(json.dumps(obj, indent=1, ensure_ascii=False))

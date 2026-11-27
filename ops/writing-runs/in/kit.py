"""The scripted part of the quarterly-report checklist (ops/writing-runs, in/test.md).

The tester session imports this in the sandbox; score.py and render.py import the same file on
the Mac, so a [script] verdict is the same wherever it is computed.

    import sys; sys.path.insert(0, "/in")
    import kit
    path = kit.deliverable()          # the file in ~/work/output a person would open, or None
    text = kit.read(path)             # its text (Markdown, text, Word, HTML or PDF)
    r = kit.check(text)               # the scripted checks: r["checks"][id] = {"pass", "observed", ...}
    print(kit.explain(r))             # the same, as lines to read, with what each verdict rests on
    kit.save(r, "~/tester/kit.json")
    kit.SOURCE                        # the fact list (in/fixtures/季度事实清单.md)
    kit.TRUTH                         # the answer key and the tone lists (in/truth.json), written before any run
    r["fact_candidates"]              # lines worth a look for check 6 (facts), which is the tester's

Scripted checks: length, structure, coverage, problems, numbers, tone, parallel. How each is
decided is in its function's docstring and, in plain words, in in/test.md. The figure rules (what
counts as the same number) are textcheck.figure_in's.
"""
import json
import os
import re
from pathlib import Path

import textcheck as tc

IN = Path(os.environ.get("KIT_IN") or Path(__file__).resolve().parent)
TRUTH = json.loads((IN / "truth.json").read_text(encoding="utf-8"))
SOURCE = (IN / TRUTH["source"]).read_text(encoding="utf-8")
SOURCE_FIGURES = tc.figure_set(SOURCE)
WORK = Path.home() / "work"
CHECKS = ["length", "structure", "coverage", "problems", "numbers", "facts", "tone", "parallel"]
SCRIPTED = [c for c in CHECKS if c != "facts"]
OLD = re.compile(TRUTH["old_marks"])
NEAR = 20                      # an old-figure word (原定, 改为, 上季度 ...) counts within this many characters of the figure
SPIN = re.compile(TRUTH["spin"])
PARTS = {k: re.compile(v) for k, v in TRUTH["parts"].items()}
STOCK = [re.compile(p) for p in TRUTH["tone"]["stock"]]
VAGUE = re.compile(TRUTH["tone"]["vague"])
ELEVATION = [re.compile(p) for p in TRUTH["tone"]["elevation"]]
CONTRAST = [re.compile(p) for p in TRUTH["parallel"]["contrast"]]
FOUR = set(TRUTH["parallel"]["four_char"])
PRAISE = re.compile(TRUTH["praise"])
CLAUSE = re.compile(r"[，,；;。！？!?：:\n]")


def _check_truth() -> None:
    """Every fact pattern of the answer key must be found in the list, or every verdict is off."""
    miss = []
    for item in TRUTH["coverage"] + TRUTH["problems"]:
        miss += [f"{item['id']} {g}" for g in item["groups"] if not re.search(g, SOURCE)]
    for x in TRUTH["stale"]:
        if not re.search(x["old"], SOURCE) or not re.search(x["now"], SOURCE):
            miss.append(x["id"])
    for k in TRUTH["key_numbers"]:
        if not re.search(k["pattern"], SOURCE):
            miss.append(k["say"])
    if miss:
        raise RuntimeError(f"truth.json and the fact list disagree: {miss}")


_check_truth()


def deliverable(folder=None):
    """The report a person would open in ~/work/output (textcheck.deliverable), or None."""
    return tc.deliverable(Path(folder) if folder else WORK / "output")


def read(path) -> str:
    return tc.read(path) if path else ""


def _cut(s: str, n: int = 160) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def _own(u: dict) -> str:
    return u.get("whole") or u["text"]


# ---- the checks --------------------------------------------------------------------------------

def check_length(text: str) -> dict:
    """Pass: the whole report, title and all, is zi_min to zi_max 字 (textcheck.zi, as Word counts)."""
    n = tc.zi(text)
    lo, hi = TRUTH["zi_min"], TRUTH["zi_max"]
    return {"pass": lo <= n <= hi, "zi": n, "observed": f"{n} 字（要求 {lo}–{hi}）"}


def _rank(line: str) -> int:
    """A heading line's level, smaller is higher: Markdown # to ######, then 一、, （一）, a bold line,
    anything else (a short line ending in a colon)."""
    s = line.strip()
    if m := re.match(r"(#{1,6})\s", s):
        return len(m.group(1))
    if re.match(r"[一二三四五六七八九十]+、", s):
        return 7
    if re.match(r"[（(][一二三四五六七八九十]+[)）]", s):
        return 8
    if s.startswith("**"):
        return 9
    return 10


def check_structure(text: str, units: list) -> dict:
    """Pass: the report has headings for the three parts, in this order: what got done (truth parts
    done), what did not go well (problems), the next quarter (plans). One heading may hold the last
    two (问题和下一步); headings in between are fine. Headings are Markdown #, a line in bold on its
    own, a short line opened by 一、 or （一）, or a short line ending in a colon."""
    lines = text.splitlines()
    hs = [(u["text"], _rank(lines[u["line"] - 1]) if 0 < u["line"] <= len(lines) else 10) for u in units if u["kind"] == "heading"]
    heads = [h for h, _ in hs]

    def search(top):                                      # the three parts among headings of level <= top
        first = lambda part, start: next((i for i in range(start, len(heads)) if hs[i][1] <= top and PARTS[part].search(heads[i])), None)   # noqa: E731
        d = first("done", 0)
        p = first("problems", d + 1) if d is not None else None
        return {"done": d, "problems": p, "plans": first("plans", p) if p is not None else None}

    for top in sorted({k for _, k in hs}) or [10]:        # the highest level holding all three is shown; the last
        found = search(top)                               # try takes every heading, so pass or fail is as before
        if None not in found.values():
            break
    d, p, f = found["done"], found["problems"], found["plans"]
    ok = None not in found.values()
    shown = " → ".join(f"「{heads[i]}」" for i in (d, p, f) if i is not None)
    missing = "、".join({"done": "做成的", "problems": "没做好的", "plans": "下季度计划"}[k] for k, v in found.items() if v is None)
    return {"pass": ok, "headings": heads,
            "observed": f"三块按顺序都有：{shown}" if ok else f"按顺序找不到：{missing}（找到的：{shown or '无'}；全部标题：{'｜'.join(heads) or '无'}）"}


def _items(units: list, items: list) -> list:
    rows = []
    for it in items:
        hit = next((u for u in units if u["kind"] != "header" and tc.has_all(tc.scope(u), it["groups"])), None)
        rows.append({"id": it["id"], "say": it["say"], "found": bool(hit), "where": _cut(hit["text"]) if hit else "", "unit": hit})
    return rows


def check_coverage(text: str, units: list) -> dict:
    """Pass: the 4 projects and the 4 plans of the list are all in the report, each with its key fact
    (truth coverage: all groups of an item inside one unit: a paragraph, list item or table row, with
    its sub-items, parent item and heading)."""
    rows = _items(units, TRUTH["coverage"])
    n = sum(r["found"] for r in rows)
    for r in rows:
        r.pop("unit")
    return {"pass": n == len(rows), "rows": rows, "observed": f"{n}/{len(rows)} 个项目和计划写到了" +
            ("" if n == len(rows) else "；没写到：" + "；".join(f"{r['id']} {r['say']}" for r in rows if not r["found"]))}


def check_problems(text: str, units: list) -> dict:
    """Pass: the 4 problems are all in the report, each with a fact from the list that says how bad or
    why (truth problems: the figure or the cause in the same unit), and none is turned into a success:
    the unit that states it holds no spin (truth spin: 奠定基础, 积累了经验, 影响有限, 契机 ...)."""
    rows = _items(units, TRUTH["problems"])
    for r, it in zip(rows, TRUTH["problems"]):
        r.pop("unit")
        spun = [m for u in units if u["kind"] != "header" and tc.has_all(tc.scope(u), it["groups"]) and (m := SPIN.search(_own(u)))]
        r["spin"] = spun[0].group(0) if spun else ""
    ok = [r for r in rows if r["found"] and not r["spin"]]
    bad = [r for r in rows if r not in ok]
    return {"pass": not bad, "rows": rows, "observed": f"{len(ok)}/{len(rows)} 个问题写实" + ("" if not bad else "；" + "；".join(
        f"{r['id']} 往好里说了（「{r['spin']}」：{r['where']}）" if r["found"] else f"{r['id']} 没写到或没带清单里的数字和原因（{r['say']}）" for r in bad))}


def check_numbers(text: str, units: list) -> dict:
    """Pass: every figure in the report is one the list gives (textcheck.figure_in: the same date, time
    or value; 3.5 小时 and 3.5, 21.6 万 and 216,000 are the same; a figure worked out from the list's,
    such as a growth rate, a difference or a share, is not; truth worked_phrases catches one that equals
    another figure of the list by chance: 结余 2.4 万, which is 24 − 21.6 and also the training cost), and
    no old figure is given as the current
    one (truth stale: 解决率 31%, 接待量 12,400, 95 秒, 满意度 4.1, 4 分 10 秒): a paragraph, list item or
    table row holding an old figure passes only when it also holds the new one, or a word saying it is
    the old one (truth old_marks) stands within NEAR characters of it."""
    text = tc.with_table_units(text)                     # 金额（万元） | 15 reads as 15 万
    figs = [f for f in tc.figures(text) if f["kind"] != "self"]
    extra = [f for f in figs if not tc.figure_in(f, SOURCE_FIGURES)]
    stale = []
    for x in TRUTH["stale"]:
        for u in tc.units(text, coarse=True):            # a paragraph, list item or table row: the context a reader has
            m = re.search(x["old"], u["text"]) if u["kind"] != "header" else None
            near = u["text"][max(0, m.start() - NEAR):m.end() + NEAR] if m else ""
            if m and not re.search(x["now"], u["text"]) and not OLD.search(near):
                stale.append({"id": x["id"], "about": x["about"], "old": m.group(0), "where": _cut(u["text"])})
    seen, rows = set(), []
    for f in extra:
        ctx = text[max(0, f["start"] - 14):f["end"] + 14].replace("\n", " ")
        if (f["raw"], ctx) not in seen:
            seen.add((f["raw"], ctx))
            line = text[text.rfind("\n", 0, f["start"]) + 1:(text.find("\n", f["end"]) + 1 or len(text) + 1) - 1]
            rows.append({"raw": f["raw"], "kind": f["kind"], "context": ctx, "worked_out": worked_out(f, line),
                         "around": _around(text, f["start"], f["end"])})
    for w in TRUTH.get("worked_phrases", []):         # a figure worked out from the list that equals another figure of it
        for m in re.finditer(w["pattern"], text):
            n = re.search(r"\d+(?:\.\d+)?\s*万", m.group(0))
            rows.append({"raw": n.group(0), "kind": "number", "context": text[max(0, m.start() - 6):m.end() + 6].replace("\n", " "),
                         "worked_out": w["worked_out"], "around": _around(text, m.start() + n.start(), m.start() + n.end())})
    obs = f"{len(figs)} 个数字，{len(rows)} 个清单里没有" + (
        "（" + "；".join(f"「{r['raw']}」{'（可能是' + r['worked_out'] + '）' if r['worked_out'] and r['worked_out'] != '清单里找不到来源' else '（清单里找不到来源）' if r['worked_out'] else ''}：…{r['context']}…" for r in rows[:8]) + "）" if rows else "")
    obs += f"；旧数字当成现在的 {len(stale)} 处" + ("（" + "；".join(f"{s['about']}「{s['old']}」：{s['where']}" for s in stale) + "）" if stale else "")
    return {"pass": not rows and not stale, "figures": len(figs), "extra": rows, "stale": stale, "observed": obs}


def _around(text: str, a: int, b: int, n: int = 3) -> tuple:
    """Up to n characters on each side of text[a:b] inside the piece the evidence page marks it in
    (textcheck.to_html: a heading's, list item's, quote's or paragraph's content, or a table cell), so
    the page marks this occurrence of a figure and not every 15 or 2.4 万; a side cut short by the
    piece's edge is anchored to it (textcheck.START, END); in a table, the row's first cell as well.
    For the evidence page only."""
    ls = text.rfind("\n", 0, a) + 1
    le = text.find("\n", b)
    le = len(text) if le < 0 else le
    line = text[ls:le]
    lo, hi = ls, le
    if line.strip().startswith("|"):
        lo = text.rfind("|", ls, a) + 1
        hi = text.find("|", b, le)
        hi = le if hi < 0 else hi
    elif h := tc.HEADING.match(line):
        lo, hi = ls + h.start(2), ls + h.end(2)
    elif (m := tc.LIST.match(line)) and m.group(2).strip():
        lo = ls + m.start(2)
    elif line.lstrip().startswith(">"):
        lo = ls + line.index(">") + 1
    while lo < a and text[lo].isspace():
        lo += 1
    while hi > b and text[hi - 1].isspace():
        hi -= 1
    before, after = text[max(lo, a - n):a], text[b:min(hi, b + n)]
    row = line.strip().strip("|").split("|")[0].strip() if line.strip().startswith("|") else ""   # a table row's first cell
    return (tc.START if a - n <= lo else "") + before, after + (tc.END if b + n >= hi else ""), row


def _line_numbers(line: str) -> list:
    """The numbers and percentages on one line of the list as (value, kind, as written), months and
    years left out (9 月, 2026 年)."""
    return sorted({(f["value"], f.get("unit") or f["kind"], f["raw"]) for f in tc.figures(line) if f["kind"] in ("number", "percent")
                   and f["value"] and not re.match(r"\s*[月年]", line[f["end"]:f["end"] + 2])})


SOURCE_LINES = [(line, _line_numbers(line)) for line in SOURCE.splitlines() if line.strip()]


def worked_out(f: dict, context: str = "") -> str:
    """How a figure not in the list could have been worked out from two numbers of one kind on one line
    of the list: a difference, a share, a change in percent or a sum, to the precision written; lines
    sharing words with the figure's context are tried first. Else "清单里找不到来源". For the evidence,
    not the verdict: a worked-out figure fails the check all the same."""
    if f["kind"] not in ("number", "percent"):
        return ""
    v = f["value"]
    dec = len(f["raw"].split(".")[1].rstrip("%％ 万千")) if "." in f["raw"] else 0
    close = lambda x: round(x, dec) == round(v, dec) or (dec == 0 and abs(x - v) < 0.5)   # noqa: E731
    small = lambda a, b: a == int(a) and b == int(b) and max(a, b) < 10   # noqa: E731  (1 名 and 2 人: no percentages)
    ways = [(lambda a, b: abs(a - b), "{ra} 和 {rb} 之差"),
            (lambda a, b: a / b * 100 if a < b and not small(a, b) else None, "{ra} 占 {rb} 的比例"),
            (lambda a, b: None if small(a, b) else abs(a - b) / b * 100, "从 {rb} 到 {ra} 的变化幅度"),
            (lambda a, b: a + b if a < b else None, "{ra} 加 {rb}")]
    near = _bigrams(context)
    fk = f.get("unit") or f["kind"]
    for line, nums in sorted(SOURCE_LINES, key=lambda ln: -len(_bigrams(ln[0]) & near)):
        for op, say in ways:
            for a, ka, ra in nums:
                for b, kb, rb in nums:
                    if a != b and ka == kb and (ka == "sec") == (fk == "sec") and (x := op(a, b)) is not None and close(x):   # like with like; durations only from durations
                        return say.format(ra=ra, rb=rb)
    return "清单里找不到来源"


def _clauses(s: str) -> list:
    return [c for c in CLAUSE.split(s) if c.strip()]


def tone_hits(text: str) -> list:
    """Stock phrases and empty elevation (truth tone): every match of the stock and elevation lists,
    and the vague verbs (持续优化, 进一步提升 ...) only in a clause with no figure in it."""
    t = tc.plain(text)
    hits = []
    for kind, pats in (("stock", STOCK), ("elevation", ELEVATION)):
        for p in pats:
            hits += [{"kind": kind, "text": m.group(0), "at": m.start()} for m in p.finditer(t)]
    pos = 0
    for c in re.split(r"(?<=[，,；;。！？!?\n])", t):
        if not re.search(r"\d", c):
            hits += [{"kind": "vague", "text": m.group(0), "at": pos + m.start()} for m in VAGUE.finditer(c)]
        pos += len(c)
    hits.sort(key=lambda h: h["at"])
    out, end = [], -1
    for h in hits:                                 # overlapping matches count once
        if h["at"] >= end:
            out.append(h)
            end = h["at"] + len(h["text"])
    return out


def check_tone(text: str, units: list) -> dict:
    """Pass: stock phrases and empty elevation together (tone_hits) come to at most tone_per_1000 per
    1,000 字 of the report."""
    hits = tone_hits(text)
    n, z = len(hits), max(tc.zi(text), 1)
    rate = round(n * 1000 / z, 1)
    from collections import Counter
    top = Counter(h["text"] for h in hits).most_common(12)
    return {"pass": rate <= TRUTH["tone_per_1000"], "count": n, "per_1000": rate, "hits": hits,
            "observed": f"套话和空泛拔高 {n} 处，每千字 {rate} 处（上限 {TRUTH['tone_per_1000']}）" +
            ("：" + "、".join(f"「{w}」×{k}" if k > 1 else f"「{w}」" for w, k in top) if top else "")}


def parallel_hits(text: str, units: list) -> list:
    """排比 (truth parallel): a contrast frame (不是…而是, 不仅…更/还/也, 不只…更); three or more
    four-character phrases in a row, at least two of them stock ones (齐心协力、攻坚克难、勇于担当);
    three or more clauses in a row opening with the same two characters (我们……，我们……，我们……),
    within a paragraph, not across list items."""
    out = []
    t = tc.plain(text)
    for p in CONTRAST:
        out += [{"kind": "contrast", "text": m.group(0)} for m in p.finditer(t)]
    for m in re.finditer(rf"(?<![{tc.CJK}])(?:[{tc.CJK}]{{4}}[、，,；;]){{2,}}[{tc.CJK}]{{4}}(?![{tc.CJK}])", t):
        chunks = re.split(r"[、，,；;]", m.group(0))
        if sum(c in FOUR for c in chunks) >= 2:
            out.append({"kind": "four_char", "text": m.group(0)})
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip() and not tc.LIST.match(p.strip().splitlines()[0])
             and not p.strip().startswith(("|", "#"))]
    for p in paras:
        cl = [re.sub(rf"^[^{tc.CJK}]*", "", c) for c in _clauses(tc.plain(p))]
        run = 1
        for i in range(1, len(cl) + 1):
            same = i < len(cl) and len(cl[i]) >= 2 and len(cl[i - 1]) >= 2 and cl[i][:2] == cl[i - 1][:2] and re.fullmatch(f"[{tc.CJK}]{{2}}", cl[i][:2])
            if same:
                run += 1
            else:
                if run >= 3:
                    out.append({"kind": "same_opening", "text": "，".join(cl[i - run:i])})
                run = 1
    return out


def check_parallel(text: str, units: list) -> dict:
    """Pass: at most parallel_max 排比 in the report (parallel_hits)."""
    hits = parallel_hits(text, units)
    return {"pass": len(hits) <= TRUTH["parallel_max"], "count": len(hits), "hits": hits,
            "observed": f"排比 {len(hits)} 处（上限 {TRUTH['parallel_max']}）" + ("：" + "；".join(f"{h['text'][:40]}" for h in hits[:6]) if hits else "")}


def _bigrams(s: str) -> set:
    t = re.sub(f"[^{tc.CJK}A-Za-z0-9]", "", s)
    return {t[i:i + 2] for i in range(len(t) - 1)}


SOURCE_BIGRAMS = _bigrams(SOURCE)


def fact_candidates(text: str, units: list) -> list:
    """Lines for the tester to look at in check 6: praise, credit or reactions the list does not give
    (truth praise: 好评, 认可, 领导, 行业领先 ...), and sentences with little wording from the list (under
    35 % of their two-character pieces), which is where something new is most often said."""
    out = []
    for u in units:
        if u["kind"] in ("heading", "header"):
            continue
        m = PRAISE.search(u["text"])
        if m:
            out.append({"why": f"评价或归功（「{m.group(0)}」）", "text": _cut(u["text"])})
            continue
        b = _bigrams(u["text"])
        if len(b) >= 8 and len(b & SOURCE_BIGRAMS) / len(b) < 0.35:
            out.append({"why": "用词和清单重合不到三成半", "text": _cut(u["text"])})
    return out


def info(text: str) -> dict:
    """AI-writing marks that are recorded, not scored: em dashes, bold runs, emoji, inline-header bullets
    (- **标题**：), 进行 + verb."""
    return {"em_dash": len(re.findall("—+", text)),
            "bold": len(re.findall(r"\*\*[^*]+\*\*", text)),
            "emoji": len(re.findall("[\U0001F300-\U0001FAFF☀-➿]", text)),
            "inline_header_bullets": len(re.findall(r"(?m)^\s*[-*+]\s+\*\*[^*]{1,20}\*\*\s*[:：]", text)),
            "jinxing": len(re.findall(r"进行(了)?[一-鿿]{2}", text))}


def check(text: str) -> dict:
    """Every scripted check on one report: {"checks": {id: {...}}, "zi", "fact_candidates", "info",
    "key_numbers", "marks"}."""
    units, paras = tc.units(text), tc.units(text, coarse=True)
    checks = {"length": check_length(text), "structure": check_structure(text, units), "coverage": check_coverage(text, paras),
              "problems": check_problems(text, paras), "numbers": check_numbers(text, units), "tone": check_tone(text, units),
              "parallel": check_parallel(text, units)}
    kept = [k["say"] for k in TRUTH["key_numbers"] if re.search(k["pattern"], text)]
    marks = [(r["raw"], "bad", "清单里没有这个数" + (f"（可能是{r['worked_out']}）" if r["worked_out"] and r["worked_out"] != "清单里找不到来源" else ""),
              *r.get("around", ("", "", ""))) for r in checks["numbers"]["extra"]]
    marks += [(s["old"], "bad", f"旧数字：{s['about']}") for s in checks["numbers"]["stale"]]
    marks += [(h["text"], "warn", {"stock": "套话", "elevation": "空泛拔高", "vague": "空话（没数字）"}[h["kind"]]) for h in checks["tone"]["hits"]]
    marks += [(h["text"], "line", "排比") for h in checks["parallel"]["hits"]]
    for r in checks["problems"]["rows"]:
        if r["spin"]:
            marks.append((r["spin"], "bad", f"{r['id']} 往好里说"))
    cands = fact_candidates(text, units)
    return {"checks": checks, "zi": checks["length"]["zi"], "fact_candidates": cands, "info": info(text),
            "key_numbers": kept, "marks": marks}


def explain(r: dict) -> str:
    lines = []
    for cid in SCRIPTED:
        c = r["checks"][cid]
        lines.append(f"[{'PASS' if c['pass'] else 'FAIL'}] {cid}: {c['observed']}")
        for row in c.get("rows", []):
            lines.append("    " + json.dumps(row, ensure_ascii=False))
    lines.append(f"check 6 (facts), lines to look at: {len(r['fact_candidates'])}")
    lines += [f"    {c['why']}: {c['text']}" for c in r["fact_candidates"]]
    lines.append(f"recorded, not scored: {json.dumps(r['info'], ensure_ascii=False)}; key numbers kept: {len(r['key_numbers'])}/{len(TRUTH['key_numbers'])}")
    return "\n".join(lines)


def save(r: dict, path) -> None:
    tc.save_json(r, path)


def card(r: dict, verdicts: dict, label: str) -> str:
    """The summary card on top of the evidence picture: every check's verdict, then counts."""
    import html
    names = {"length": f"{TRUTH['zi_min']}–{TRUTH['zi_max']} 字", "structure": "三块、顺序对", "coverage": "项目和计划都在",
             "problems": "问题写实", "numbers": "数字都出自清单", "facts": "没编事实", "tone": "套话少",
             "parallel": "不用排比"}
    marks = "".join(f'<span class="{"ok" if verdicts.get(c) else "no"}">{"✓" if verdicts.get(c) else "✗"} {names[c]}</span>　'
                    for c in CHECKS if c in verdicts)
    c = r["checks"]
    facts = (f'{r["zi"]} 字 · 清单里没有的数字 {len(c["numbers"]["extra"])} · 旧数字 {len(c["numbers"]["stale"])} · '
             f'套话和拔高 {c["tone"]["count"]}（每千字 {c["tone"]["per_1000"]}）· 排比 {c["parallel"]["count"]}')
    return (f'<div class="card"><b>{html.escape(label)}</b><br>{marks}<br><span class="mute">{facts}</span><br>'
            f'<span class="legend mute"><span><mark class="bad">红</mark> 清单里没有的数、旧数字、往好里说</span>'
            f'<span><mark class="warn">黄</mark> 套话、空泛拔高</span><span><mark class="line">橙线</mark> 排比</span></span></div>')

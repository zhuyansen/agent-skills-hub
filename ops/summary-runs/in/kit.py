"""The scripted part of the meeting-summary checklist (ops/summary-runs, in/test.md).

The tester session imports this in the sandbox; score.py and render.py import the same file on
the Mac, so a [script] verdict is the same wherever it is computed.

    import sys; sys.path.insert(0, "/in")
    import kit
    path = kit.deliverable()          # the file in ~/work/output a person would open, or None
    text = kit.read(path)             # its text (Markdown, text, Word, HTML or PDF)
    r = kit.check(text)               # the scripted checks: r["checks"][id] = {"pass", "observed", ...}
    print(kit.explain(r))             # the same, as lines to read, with the units each verdict rests on
    kit.save(r, "~/tester/kit.json")
    kit.SOURCE                        # the meeting record (in/fixtures/会议记录.txt)
    kit.TRUTH                         # the answer key (in/truth.json), written before any run
    r["invented_candidates"]          # lines worth a look for check 7 (invented), which is the tester's

Scripted checks: length, conclusion, decisions, todos, numbers, undecided. How each is decided is
in its function's docstring and, in plain words, in in/test.md. The figure rules (what counts as
the same number) are textcheck.figure_in's.
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
CHECKS = ["length", "conclusion", "decisions", "todos", "numbers", "undecided", "invented"]
SCRIPTED = CHECKS[:6]
NAMES = {n: [n, *alias] for n, alias in TRUTH["people"].items()}
ANY_NAME = "|".join(sorted({a for v in NAMES.values() for a in v}, key=len, reverse=True))
OPEN = re.compile(TRUTH["open_marks"])
DECIDED = re.compile(TRUTH["decided_marks"])
OLD = re.compile(TRUTH["old_marks"])
NEAR = 20                      # an old-figure word (原定, 改为, 上季度 ...) counts within this many characters of the figure
DECISION_HEAD = re.compile(r"决定|决议|结论|已定|共识|拍板|决策|定下|[Dd]ecision")
TODO_HEAD = re.compile(r"待办|行动|[Aa]ction|[Tt]o-?[Dd]o|TODO|下一步|跟进|任务|分工|责任|谁来|后续|[Nn]ext")
OWNER_HEAD = re.compile(r"负责|[Oo]wner|执行人|责任人")
META = re.compile(r"^[\s>*\-#|]*(\*\*)?\s*(会议|下次|下一次|开始|结束)?(周会|例会|会议|时间|日期|地点|参会|出席|与会|记录|主持|缺席|名称|主题|议题|类型|形式|时长|来源|"
                  r"整理|撰写|作者|版本|状态|发送|抄送|分发|收件|阅读对象|读者)(人|员|人员|人数|方式)?\s*(（[^）]{0,20}）|\([^)]{0,20}\))?\s*(\*\*)?\s*[:：|]")


def _check_truth() -> None:
    """Every pattern of the answer key must be found in the record, or every verdict is off."""
    miss = []
    for d in TRUTH["decisions"]:
        for part in d["parts"]:
            miss += [f"{d['id']} {g}" for g in part if not re.search(g, SOURCE)]
    for t in TRUTH["todos"] + TRUTH["soft"]:
        if not re.search(t["keys"], SOURCE):
            miss.append(t["id"])
    for t in TRUTH["todos"]:
        if not any(f["kind"] == "date" and f["value"] == t["due"] for f in tc.figures(SOURCE)):
            miss.append(f"{t['id']} due {t['due']}")
    for u in TRUTH["undecided"]:
        if not re.search(u["keys"], SOURCE):
            miss.append(u["id"])
    for x in TRUTH["stale"]:
        if not re.search(x["old"], SOURCE) or not re.search(x["now"], SOURCE):
            miss.append(x["id"])
    for k in TRUTH["key_numbers"]:
        if not re.search(k["pattern"], SOURCE):
            miss.append(k["say"])
    if miss:
        raise RuntimeError(f"truth.json and the record disagree: {miss}")


_check_truth()


def deliverable(folder=None):
    """The summary a person would open in ~/work/output (textcheck.deliverable), or None."""
    return tc.deliverable(Path(folder) if folder else WORK / "output")


def read(path) -> str:
    return tc.read(path) if path else ""


def _cut(s: str, n: int = 160) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def _own(u: dict) -> str:
    """A unit's own words: its text with its sub-items."""
    return u.get("whole") or u["text"]


# ---- the checks --------------------------------------------------------------------------------

def check_length(text: str) -> dict:
    """Pass: the whole summary, title and all, is at most limit_zi 字 (textcheck.zi, as Word counts)."""
    n = tc.zi(text)
    return {"pass": n <= TRUTH["limit_zi"], "zi": n, "observed": f"{n} 字（上限 {TRUTH['limit_zi']}）"}


SOURCE_NOTE = re.compile(r"^\s*>\s*(\*\*)?\s*(依据|来源|出处|说明|注|备注|原文|本纪要|本文|本总结|整理|声明)")   # "> 依据：会议记录.txt …"


def _skippable(line: str, first: bool) -> bool:
    """A line before the summary proper: a title (the first line, at most 30 字, no full stop), a
    heading, a line or table row that only gives the meeting's (or the next meeting's) date, place,
    people or author, or a quoted note on the source ("> 依据：…"). A line that states a decision is
    never skipped, heading or not."""
    if not line.strip():
        return True
    if _decisions_in(tc.plain(line)):
        return False
    if first and tc.zi(line) <= 30 and not re.search(r"[。；！？]", line) and not tc.LIST.match(line) and not line.strip().startswith("|"):
        return True
    return bool(tc.HEADING.match(line) or tc.BOLD_LINE.match(line) or tc.COLON_HEADING.match(line) or META.match(line)
                or tc.TABLE_SEP.match(line) or (tc.CN_HEADING.match(line) and tc.zi(line) <= 12)
                or (line.strip().startswith("|") and _meta_row(line)) or SOURCE_NOTE.match(line))


def opening(text: str, n: int) -> str:
    """The summary's first block, at most n 字: after the lines _skippable() passes over, the first
    paragraph, or the first list (all its items) or table (all its rows). A first paragraph that is only
    a short note of who met when (at most 40 字, naming a date, a time or the people, stating no
    decision) is passed over too."""
    lines = text.splitlines()
    i, first = 0, True
    while i < len(lines) and _skippable(lines[i], first):
        first = first and not lines[i].strip()
        i += 1
    block, kind, used = _first_block(lines[i:])
    note = tc.plain("\n".join(block))
    if kind == "text" and tc.zi(note) <= 40 and not _decisions_in(note) \
            and re.search(r"主持|参会|参加|出席|与会|列席|记录人|\d+\s*人|\d+\s*月\s*\d+\s*[日号]|\d+[:：]\d\d|周[一二三四五六日]", note):
        i += used
        while i < len(lines) and _skippable(lines[i], False):
            i += 1
        block, kind, _ = _first_block(lines[i:])
    out, count = [], 0
    for ch in tc.plain("\n".join(block)).replace("\n", " "):
        if count >= n:
            break
        out.append(ch)
        if re.match(f"[{tc.CJK}{tc.CJK_PUNCT}]", ch) or (ch.isalnum() and (len(out) < 2 or not out[-2].isalnum())):
            count += 1
    return "".join(out).strip()


def _first_block(lines: list) -> tuple:
    """The first paragraph, list or table in lines, blank lines before it skipped: (its lines, its kind,
    how many lines it took up). A list runs on over blank lines while the next line is still an item."""
    block, kind, used = [], None, 0
    for line in lines:
        k = "table" if line.strip().startswith("|") else "list" if tc.LIST.match(line) else "blank" if not line.strip() else "text"
        if kind is None:
            used += 1
            if k == "blank":
                continue
            kind = k
        elif k == "blank":
            if kind != "list":
                break
            used += 1
            continue
        elif tc.HEADING.match(line) or tc.BOLD_LINE.match(line) or (k != kind and not (kind == "list" and line.startswith((" ", "\t")))):
            break
        else:
            used += 1
        block.append(line)
    return block, kind, used


META_CELL = re.compile(r"^(会议|下次|下一次|开始|结束)?(日期|时间|地点|参会|出席|与会|主持|记录|缺席|列席|抄送|分发|名称|主题|形式|时长|周会|会议)")


def _meta_row(line: str) -> bool:
    """A table row that only gives meeting information: its first cell is a short label such as 日期和时间,
    参会人, 记录人 (or the header 项目 | 内容)."""
    first = re.sub(r"[*\s]", "", line.strip().strip("|").split("|")[0])
    return (len(first) <= 10 and bool(META_CELL.match(first))) or first in ("项目", "内容", "字段")


def _decisions_in(text: str) -> list:
    return [d["id"] for d in TRUTH["decisions"] if any(tc.has_all(text, part) for part in d["parts"])]


def check_conclusion(text: str) -> dict:
    """Pass: the opening (the first block of the body, at most opening_zi 字, see opening()) states at
    least opening_min of the meeting's decisions (each by all the groups of one of its parts)."""
    head = opening(text, TRUTH["opening_zi"])
    found = _decisions_in(head)
    return {"pass": len(found) >= TRUTH["opening_min"], "found": found, "opening": head,
            "observed": f"开头 {TRUTH['opening_zi']} 字里写到 {len(found)} 条决定（{'、'.join(found) or '无'}）；开头：{_cut(head, 120)}"}


def check_decisions(text: str, units: list) -> dict:
    """Pass: every decision is there: each of its parts matched by one unit (a paragraph, list item or
    table row, with its sub-items, parent item and heading, so "3 步" under a heading 新手引导 counts)."""
    rows = []
    for d in TRUTH["decisions"]:
        where = []
        for part in d["parts"]:
            hit = next((u for u in units if tc.has_all(tc.scope(u), part)), None)
            where.append(_cut(hit["text"]) if hit else "")
        rows.append({"id": d["id"], "say": d["say"], "found": all(where), "where": where})
    n = sum(r["found"] for r in rows)
    return {"pass": n == len(rows), "rows": rows, "observed": f"{n}/{len(rows)} 条决定写到了" +
            ("" if n == len(rows) else "；没写到：" + "；".join(f"{r['id']} {r['say']}" for r in rows if not r["found"]))}


def _due_ok(text: str, t: dict) -> bool:
    for f in tc.figures(text):
        if (f["kind"] == "date" and f["value"] == t["due"]) or (f["kind"] == "day" and f["value"] == [t["due"][1]]) \
                or tc.as_date(f) == tuple(t["due"]):
            return True
    return any(w in text for w in t["due_words"])


def _owner_ok(text: str, owner: str) -> bool:
    return any(a in text for a in NAMES.get(owner, [owner]))


def _carried(units: list) -> dict:
    """For each sentence of a paragraph that names nobody: the last person named in an earlier sentence
    of the same paragraph (the subject carries over: 「赵敏……。达人名单和排期 11 月 12 日前发群里。」)."""
    out, last, para = {}, None, None
    for i, u in enumerate(units):
        if u["kind"] != "sentence":
            last, para = None, None
            continue
        if u["line"] != para:
            para, last = u["line"], None
        names = re.findall(ANY_NAME, u["text"])
        if not names and last:
            out[i] = last
        if names:
            last = names[-1]
    return out


def check_todos(text: str, units: list) -> dict:
    """Pass: every task is there (a unit whose own words match its keys) with its owner and its due date
    in the same unit (with sub-items, parent item and heading): the date written as a date (11 月 13 日,
    11/13, 13 号) or as the record said it (下周五). In a paragraph, a sentence that names nobody keeps
    the person named last before it in that paragraph (_carried). Of several units naming a task, the
    one with the owner and the date counts."""
    rows, carried = [], _carried(units)
    for t in TRUTH["todos"]:
        best = None
        for i, u in enumerate(units):
            if u["kind"] in ("heading", "header") or not re.search(t["keys"], _own(u)):
                continue
            s = tc.scope(u) + (" " + carried[i] if i in carried else "")
            score = (2 if _owner_ok(s, t["owner"]) else 0) + (2 if _due_ok(s, t) else 0) + (1 if u["kind"] in ("item", "row") else 0)
            if best is None or score > best[0]:
                best = (score, u, s)
        if best is None:
            rows.append({"id": t["id"], "say": t["say"], "found": False, "owner": False, "due": False, "where": ""})
            continue
        _, u, s = best
        rows.append({"id": t["id"], "say": t["say"], "found": True, "owner": _owner_ok(s, t["owner"]), "due": _due_ok(s, t),
                     "where": _cut(u["text"]), "want": f"{t['owner']}，{t['due'][0]} 月 {t['due'][1]} 日"})
    ok = [r for r in rows if r["found"] and r["owner"] and r["due"]]
    bad = [r for r in rows if r not in ok]
    def why(r):
        if not r["found"]:
            return f"{r['id']} 没写到（{r['say']}）"
        miss = [x for x, k in (("负责人", "owner"), ("截止日期", "due")) if not r[k]]
        return f"{r['id']} {'、'.join(miss)}不对或没写（应为 {r['want']}；写的是：{r['where']}）"
    return {"pass": not bad, "rows": rows,
            "observed": f"{len(ok)}/{len(rows)} 条待办负责人和截止日期都对" + ("" if not bad else "；" + "；".join(why(r) for r in bad))}


def check_numbers(text: str, units: list) -> dict:
    """Pass: every figure in the summary is one the record says (textcheck.figure_in: the same date,
    time or value; 41% and 41, 3.8 万 and 38,000 are the same; a figure worked out from the record's,
    such as 一周 written as 7 天 or a percentage of its own, is not), and no old figure the meeting
    replaced (truth stale: 日活 2.6 万, 上线 11 月 20 日, 预算 5 万, 月卡 15 元, 年卡 128 元, 早上 9 点,
    引导终稿 11 月 9 日) is given as the current one: a paragraph, list item or table row holding an old
    figure passes only when it also holds the new one, or a word saying the old one is old (truth
    old_marks: 原定, 从, 改为, 算错 ...) stands within NEAR characters of it."""
    figs = [f for f in tc.figures(text) if f["kind"] != "self"]
    extra = [f for f in figs if not tc.figure_in(f, SOURCE_FIGURES)]
    stale = []
    for x in TRUTH["stale"]:
        for u in tc.units(text, coarse=True):            # a paragraph, list item or table row: the context a reader has
            m = re.search(x["old"], u["text"]) if u["kind"] != "header" else None
            near = u["text"][max(0, m.start() - NEAR):m.end() + NEAR] if m else ""
            if m and not re.search(x["now"], u["text"]) and not OLD.search(near):
                stale.append({"id": x["id"], "about": x["about"], "old": m.group(0), "where": _cut(u["text"])})
    seen, extra_rows = set(), []
    for f in extra:
        ctx = text[max(0, f["start"] - 14):f["end"] + 14].replace("\n", " ")
        if (f["raw"], ctx) not in seen:
            seen.add((f["raw"], ctx))
            extra_rows.append({"raw": f["raw"], "kind": f["kind"], "context": ctx, "around": _around(text, f["start"], f["end"])})
    obs = f"{len(figs)} 个数字，{len(extra_rows)} 个原文里没有" + (
        "（" + "；".join(f"「{r['raw']}」：…{r['context']}…" for r in extra_rows[:8]) + "）" if extra_rows else "")
    obs += f"；旧数字当成现在的 {len(stale)} 处" + ("（" + "；".join(f"{s['about']}「{s['old']}」：{s['where']}" for s in stale) + "）" if stale else "")
    return {"pass": not extra_rows and not stale, "figures": len(figs), "extra": extra_rows, "stale": stale,
            "self_counts": [f["raw"] for f in tc.figures(text) if f["kind"] == "self"], "observed": obs}


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


def check_undecided(text: str, units: list) -> dict:
    """Pass: each open point (truth undecided) is in the summary, and marked open wherever it appears:
    the unit or its heading carries an open mark (truth open_marks: 待定, 没定, 下次再, 以后再说 ...).
    A mention without one fails, and so does one written as decided (a decided mark, or a heading such
    as 决定 / 结论, with no open mark)."""
    rows = []
    for o in TRUTH["undecided"]:
        hits = [u for u in units if u["kind"] != "header" and re.search(o["keys"], _own(u))]
        unmarked = [u for u in hits if not OPEN.search(tc.scope(u))]
        decided = [u for u in unmarked if DECIDED.search(u["text"]) or DECISION_HEAD.search(u.get("section", ""))]
        rows.append({"id": o["id"], "say": o["say"], "found": bool(hits), "marked": bool(hits) and not unmarked,
                     "as_decided": [_cut(u["text"]) for u in decided], "unmarked": [_cut(u["text"]) for u in unmarked],
                     "where": [_cut(u["text"]) for u in hits][:3]})
    bad = [r for r in rows if not (r["found"] and r["marked"])]
    def why(r):
        if not r["found"]:
            return f"{r['id']} 没写到（{r['say']}）"
        if r["as_decided"]:
            return f"{r['id']} 写成了定了：{r['as_decided'][0]}"
        return f"{r['id']} 没标没定：{r['unmarked'][0]}"
    return {"pass": not bad, "rows": rows, "observed": f"{len(rows) - len(bad)}/{len(rows)} 件没定的事写到并标了没定" +
            ("" if not bad else "；" + "；".join(why(r) for r in bad))}


def _bigrams(s: str) -> set:
    t = re.sub(f"[^{tc.CJK}A-Za-z0-9]", "", s)
    return {t[i:i + 2] for i in range(len(t) - 1)}


SOURCE_BIGRAMS = _bigrams(SOURCE)


def invented_candidates(text: str, units: list) -> list:
    """Lines for the tester to look at in check 7: an action item (under a 待办 / 行动 heading, in a table
    with an owner column, or any unit pairing a person with a date) that matches none of the record's
    tasks, its loose asks (truth soft) or its decisions; a loose ask given a date the record does not
    give it; an open point listed as a task; and sentences with little wording from the record (under
    40 % of their two-character pieces), which is where something new is most often said."""
    heads = {u["line"]: u["text"] for u in units if u["kind"] == "header"}
    out = []
    for u in units:
        if u["kind"] in ("heading", "header"):
            continue
        own, s = _own(u), tc.scope(u)
        in_todo = bool(TODO_HEAD.search(u.get("section", ""))) or (u["kind"] == "row" and any(
            OWNER_HEAD.search(h) for ln, h in heads.items() if ln < u["line"]))
        figs = tc.figures(own)
        dated = any(f["kind"] == "date" or (f["kind"] == "day" and not re.match(r"\s*(留存|活)", own[f["end"]:f["end"] + 3]))
                    for f in figs)                                 # 7 日留存 is not a date
        named = bool(re.search(ANY_NAME, s))
        todo = next((t for t in TRUTH["todos"] if re.search(t["keys"], own)), None)
        soft = next((t for t in TRUTH["soft"] if re.search(t["keys"], own)), None)
        open_pt = next((o for o in TRUTH["undecided"] if re.search(o["keys"], own)), None)
        decision = _decisions_in(s)
        if re.search(r"主持|参会|参加|出席|与会|列席|记录人|会议时间|散会|下次(周会|会议|例会)|下周(周会|例会)", own) or META.match(u["text"]):
            continue
        if (in_todo or (named and dated)) and not todo:
            if open_pt and in_todo and not OPEN.search(s):
                out.append({"why": f"没定的事（{open_pt['id']}）写成了待办", "text": _cut(u["text"])})
            elif soft and dated:
                out.append({"why": f"原文没给这件事截止日期（{soft['id']} {soft['say']}）", "text": _cut(u["text"])})
            elif not soft and not open_pt and not decision and (named or dated or in_todo):
                out.append({"why": "原文里没有这条待办", "text": _cut(u["text"])})
        if u["kind"] == "sentence" or u["kind"] == "item":
            b = _bigrams(u["text"])
            if len(b) >= 8 and len(b & SOURCE_BIGRAMS) / len(b) < 0.4:
                out.append({"why": "用词和原文重合不到四成", "text": _cut(u["text"])})
    return out


def check(text: str) -> dict:
    """Every scripted check on one summary: {"checks": {id: {...}}, "zi", "invented_candidates",
    "noise", "key_numbers", "marks"}."""
    units, paras = tc.units(text), tc.units(text, coarse=True)
    checks = {"length": check_length(text), "conclusion": check_conclusion(text), "decisions": check_decisions(text, paras),
              "todos": check_todos(text, units), "numbers": check_numbers(text, units), "undecided": check_undecided(text, units)}
    noise = sorted(set(re.findall(TRUTH["noise"], text)))
    kept = [k["say"] for k in TRUTH["key_numbers"] if re.search(k["pattern"], text)]
    marks = [(r["raw"], "bad", "原文没有这个数", *r.get("around", ("", "", ""))) for r in checks["numbers"]["extra"]]
    marks += [(s["old"], "bad", f"旧数字：{s['about']}") for s in checks["numbers"]["stale"]]
    cands = invented_candidates(text, units)
    marks += [(c["text"].rstrip("…"), "warn", c["why"]) for c in cands if c["why"] != "用词和原文重合不到四成"]
    for r in checks["todos"]["rows"]:
        if r["found"] and not (r["owner"] and r["due"]):
            marks.append((r["where"].rstrip("…"), "bad", f"{r['id']} 应为 {r['want']}"))
    for r in checks["undecided"]["rows"]:
        for w in r["as_decided"] + r["unmarked"]:
            marks.append((w.rstrip("…"), "bad", f"{r['id']} 没定的事没标没定"))
    marks += [(w, "info", "闲聊") for w in noise]
    return {"checks": checks, "zi": checks["length"]["zi"], "invented_candidates": cands, "noise": noise,
            "key_numbers": kept, "marks": marks}


def explain(r: dict) -> str:
    lines = []
    for cid in SCRIPTED:
        c = r["checks"][cid]
        lines.append(f"[{'PASS' if c['pass'] else 'FAIL'}] {cid}: {c['observed']}")
        for row in c.get("rows", []):
            lines.append("    " + json.dumps(row, ensure_ascii=False))
    lines.append(f"check 7 (invented), lines to look at: {len(r['invented_candidates'])}")
    lines += [f"    {c['why']}: {c['text']}" for c in r["invented_candidates"]]
    lines.append(f"small talk kept: {'、'.join(r['noise']) or 'none'}; key numbers kept: {len(r['key_numbers'])}/{len(TRUTH['key_numbers'])}")
    return "\n".join(lines)


def save(r: dict, path) -> None:
    tc.save_json(r, path)


def card(r: dict, verdicts: dict, label: str) -> str:
    """The summary card on top of the evidence picture: every check's verdict, then counts."""
    names = {"length": f"{TRUTH['limit_zi']} 字以内", "conclusion": "先写结论", "decisions": "决定都在", "todos": "待办：谁、哪天",
             "numbers": "数字照原文", "undecided": "没定的标没定", "invented": "没编"}
    import html
    marks = "".join(f'<span class="{"ok" if verdicts.get(c) else "no"}">{"✓" if verdicts.get(c) else "✗"} {names[c]}</span>　'
                    for c in CHECKS if c in verdicts)
    c = r["checks"]
    facts = (f'{r["zi"]} 字 · 决定 {sum(x["found"] for x in c["decisions"]["rows"])}/{len(c["decisions"]["rows"])} · '
             f'待办全对 {sum(x["found"] and x["owner"] and x["due"] for x in c["todos"]["rows"])}/{len(c["todos"]["rows"])} · '
             f'原文没有的数字 {len(c["numbers"]["extra"])} · 旧数字 {len(c["numbers"]["stale"])}')
    return (f'<div class="card"><b>{html.escape(label)}</b><br>{marks}<br><span class="mute">{facts}</span><br>'
            f'<span class="legend mute"><span><mark class="bad">红</mark> 错的数字、待办、没标没定</span>'
            f'<span><mark class="warn">黄</mark> 可能是编的</span><span><mark class="info">蓝</mark> 闲聊</span></span></div>')

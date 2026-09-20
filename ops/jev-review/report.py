"""Score every adjudicator against the hand labels.

AUC uses averaged ranks for ties — the naive version assigns tied scores the last rank,
which inflates every score and can exceed 1.0 (a bug this project already shipped once).
Discrete rules (the scanner's own citation heuristic, a keyword list) have no ranking, so
they are reported as precision/recall at their single operating point.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
CITE_WORDS = re.compile(
    r"\b(block(s|ed|ing)?|den(y|ies|ied)|detect(s|ed|ion)?|prevent(s|ed)?|warn(s|ing)?|forbid|"
    r"refus|reject(s|ed)?|scan(s|ner|ning)?|flag(s|ged)?|escalat|attack|malicious|exploit|"
    r"severity|critical|risk)\b|拦截|禁止|检测|危险|阻止|扫描")


def auc(scores: list[float], labels: list[int]) -> float:
    """Mann-Whitney U with averaged ranks for ties."""
    pos = sum(labels)
    neg = len(labels) - pos
    if not pos or not neg:
        return float("nan")
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return (sum(r for r, y in zip(ranks, labels) if y) - pos * (pos + 1) / 2) / (pos * neg)


def prf(pred: list[int], labels: list[int]) -> tuple[float, float, float]:
    tp = sum(p and y for p, y in zip(pred, labels))
    fp = sum(p and not y for p, y in zip(pred, labels))
    fn = sum((not p) and y for p, y in zip(pred, labels))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return prec, rec, (tp + sum((not p) and (not y) for p, y in zip(pred, labels))) / len(labels)


def keyword_issued(item: dict) -> int:
    line = item["line"]
    table_row = line.count("|") >= 2
    return int(not (table_row or bool(CITE_WORDS.search(line))))


def main() -> None:
    items = [it for it in json.load(open(OUT / "adjudicated-handlabels.json")) if it["y_human"] >= 0]
    y = [it["y_human"] for it in items]
    judge = {}
    path = OUT / "judge_haiku.json"
    if path.exists():
        judge = {r["i"]: r for r in json.loads(path.read_text())}

    print(f"items: {len(items)} · issued: {sum(y)} ({sum(y)/len(y):.1%}) · cited: {len(y)-sum(y)}\n")
    print(f"{'adjudicator':34s} {'AUC':>6s}  {'prec':>6s} {'recall':>6s} {'acc':>6s}")

    def row(name, scores, pred=None):
        a = auc(scores, y) if scores else float("nan")
        p, r, acc = prf(pred if pred is not None else [int(s > 0) for s in scores], y)
        print(f"{name:34s} {a:6.3f}  {p:6.3f} {r:6.3f} {acc:6.3f}")

    row("scanner today (flag = issued)", [], [1] * len(items))
    row("scanner citation heuristic", [], [int(not it["heuristic_cited"]) for it in items])
    row("in a code fence", [], [int(it["in_fence"]) for it in items])
    row("keyword/table baseline", [], [keyword_issued(it) for it in items])
    if judge:
        row("independent judge (Haiku)", [judge[i]["confidence"] / 100 * (1 if judge[i]["label"] == "ISSUED" else -1)
                                          for i, _ in enumerate(items)],
            [int(judge[i]["label"] == "ISSUED") for i, _ in enumerate(items)])
    row("Jev: issues_it alone", [it["jev"]["issues_it"] for it in items],
        [int(it["jev"]["issues_it"] > 0.5) for it in items])
    row("Jev: 4-question combo", [it["jev_score"] for it in items],
        [int(it["jev_score"] > 0.5) for it in items])

    print("\nper-question AUC (Jev):")
    for q in ("issues_it", "is_documentation", "is_negated", "word_coincidence"):
        print(f"  {q:20s} {auc([it['jev'][q] for it in items], y):6.3f}")

    print("\nJev errors at threshold 0.5 on issues_it:")
    for it in items:
        pred = int(it["jev"]["issues_it"] > 0.5)
        if pred != it["y_human"]:
            kind = "said ISSUED, is cited" if pred else "said CITED, is issued"
            print(f"  [{kind}] p={it['jev']['issues_it']:.2f} {it['flag']} · {it['repo']}")
            print(f"      {it['line'][:130]}")


if __name__ == "__main__":
    main()


def suppression_table(items: list[dict], y: list[int]) -> None:
    """The real decision: suppress a flag when the second pass calls it a citation.
    What matters is how many citations we clear per real flag we wrongly hide."""
    print(f"\n{'threshold':>9s}  {'flags suppressed':>16s}  {'citations cleared':>17s}  {'real flags lost':>15s}")
    scores = [it["jev_score"] for it in items]
    for t in (-0.2, 0.0, 0.2, 0.3, 0.4, 0.5, 0.6):
        sup = [s <= t for s in scores]
        cleared = sum(s and not yy for s, yy in zip(sup, y))
        lost = sum(s and yy for s, yy in zip(sup, y))
        total_cited = len(y) - sum(y)
        print(f"{t:9.2f}  {sum(sup):6d} / {len(y):<7d}  {cleared:5d} / {total_cited:<9d}"
              f"  {lost:5d} / {sum(y):<7d} ({lost/max(1,sum(y)):.1%})")


def bootstrap_ci(scores: list[float], y: list[int], n: int = 2000) -> tuple[float, float]:
    import random
    rng = random.Random(7)
    vals = []
    for _ in range(n):
        idx = [rng.randrange(len(y)) for _ in range(len(y))]
        s = [scores[i] for i in idx]
        lab = [y[i] for i in idx]
        if 0 < sum(lab) < len(lab):
            vals.append(auc(s, lab))
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals))]


def precision_at_recall(scores: list[float], y: list[int], target: float) -> tuple[float, float]:
    order = sorted(range(len(y)), key=lambda i: -scores[i])
    tp = fp = 0
    for n, i in enumerate(order, 1):
        tp += y[i]
        fp += 1 - y[i]
        if tp / sum(y) >= target:
            return tp / n, scores[i]
    return 0.0, 0.0


def extra() -> None:
    items = [it for it in json.load(open(OUT / "adjudicated-handlabels.json")) if it["y_human"] >= 0]
    y = [it["y_human"] for it in items]
    combo = [it["jev_score"] for it in items]
    lo, hi = bootstrap_ci(combo, y)
    print(f"\nJev combo AUC 95% CI (bootstrap, n={len(y)}): [{lo:.3f}, {hi:.3f}]")
    kw = [keyword_issued(it) for it in items]
    kp, kr, _ = prf(kw, y)
    p_at, thr = precision_at_recall(combo, y, kr)
    print(f"at the keyword baseline's recall ({kr:.3f}): keyword precision {kp:.3f} · Jev precision {p_at:.3f} (thr {thr:.2f})")
    both = [int(k and c > 0.0) for k, c in zip(kw, combo)]
    bp, br, ba = prf(both, y)
    print(f"keyword AND Jev>0:  precision {bp:.3f} recall {br:.3f} accuracy {ba:.3f}")
    suppression_table(items, y)


if __name__ == "__main__":
    extra()

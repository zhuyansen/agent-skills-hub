"""Shared by the three radar signals: split text into terms, score a surge.

A surge is a term that shows up in many more places in the recent window than its
baseline rate predicts. Counted per distinct source (an owner on GitHub, a URL on a
sitemap, a query in GSC) so one prolific account cannot fake a wave.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

_SPLIT = re.compile(r"[^a-z0-9.+#]+")
_CAMEL = re.compile(r"(?<=[a-z])(?=[A-Z])")
MIN_LEN = 3
# Words that are everywhere in this space; a surge in them is never a new term.
STOP = set("""
a an and are as at be by can for from has have in into is it its of on or that the this to with your you
using use used via based built make makes made new open source opensource simple fast free first best
ai agent agents agentic llm llms mcp server servers skill skills tool tools toolkit plugin plugins claude code
codex cursor gpt openai anthropic model models app apps api cli sdk framework library project repo repository
github python typescript javascript node rust go web based local self hosted hosted powered support supports
your all any more most one two three get set run runs build builder generate generator help helper helps
assistant assistants chat bot bots automation automate automated workflow workflows system systems data
md readme docs example examples demo test tests template templates collection awesome list curated
""".split())


def terms(text: str) -> set[str]:
    """Unigrams and bigrams, lowercased, stop words dropped. A camelCase name is kept whole
    ("hyperframes") and its parts are added; bigrams come from the text as written."""
    words = _words(text or "")
    parts = _words(_CAMEL.sub(" ", text or ""))
    keep = {w for w in words + parts if w not in STOP and not w.isdigit()}
    pairs = {f"{a} {b}" for a, b in zip(words, words[1:])
             if a != b and a not in STOP and b not in STOP and not a.isdigit() and not b.isdigit()}
    return keep | pairs


_URL = re.compile(r"https?://\S+|@\w+")
_TOKEN = re.compile(r"[A-Za-z0-9][\w.+\-]*[\w+]|[A-Za-z0-9]")


def names(text: str, strong: bool = False) -> set[str]:
    """Name-like phrases in prose (posts, model cards): capitalised words, words with a
    digit (Qwen3.8, 27B) or inner capitals (HyperFrames); a number right after a name
    joins it (Opus 5.5). Neighbouring name words join, up to three ("Qwen3.8 Flash
    Next"); anything but spaces between two words (punctuation, a bracket, Chinese text)
    ends the phrase. A phrase made only of stop words ("claude", "claude code") is
    dropped; a stop word inside a name ("claude opus 5.5") is kept.

    A capitalised word is often just the start of a sentence ("Lots", "Trained"). With
    `strong`, only phrases holding a word that is unmistakably a name (a digit, inner
    capitals, three or more capitals) are returned. Without it the caller must filter
    by novelty: those ordinary words are seen every day. `terms()` is for names and
    slugs; on prose it yields mostly ordinary bigrams."""
    text = _URL.sub(" ", text or "")
    out: set[str] = set()
    run: list[tuple[str, bool]] = []

    def flush() -> None:
        for i in range(len(run)):
            for j in range(i + 1, min(i + 3, len(run)) + 1):
                part = run[i:j]
                words = [w.lower().strip(".-") for w, _ in part]
                if words[0].replace(".", "").isdigit() or all(w in STOP for w in words):
                    continue
                if strong and not any(sure for _, sure in part):
                    continue
                phrase = " ".join(words)
                if len(phrase) >= MIN_LEN:
                    out.add(phrase)
        run.clear()

    prev_end = 0
    for m in _TOKEN.finditer(text):
        if text[prev_end:m.start()].strip():
            flush()
        prev_end = m.end()
        w = m.group().rstrip(".")
        number = w.replace(".", "").isdigit()
        sure = (any(c.isupper() for c in w[1:]) or (any(c.isdigit() for c in w) and not number)
                or (w.isupper() and len(w) >= 3))
        if sure or w[0].isupper() or (number and run):
            run.append((w, sure))
        else:
            flush()
    flush()
    return out


def _words(text: str) -> list[str]:
    words = [w.strip(".") for w in _SPLIT.split(text.lower())]
    return [w for w in words if len(w) >= MIN_LEN or any(c.isdigit() for c in w)]


def by_source(items: list[tuple[str, str]]) -> dict[str, set[str]]:
    """term -> the distinct sources (owner, URL, query) it appears in."""
    out: dict[str, set[str]] = defaultdict(set)
    for source, text in items:
        for t in terms(text):
            out[t].add(source)
    return out


def surges(recent: dict[str, set[str]], baseline: dict[str, set[str]], ratio: float,
           min_sources: int, top: int) -> list[dict]:
    """Terms whose recent count beats the baseline's expected count by the most.
    `ratio` scales the baseline to the recent window (3 days against 30 -> 0.1)."""
    rows = []
    for term, sources in recent.items():
        n = len(sources)
        if n < min_sources:
            continue
        expected = len(baseline.get(term, ())) * ratio
        rows.append({"term": term, "recent": n, "baseline": len(baseline.get(term, ())),
                     "lift": round(n / (expected + 1), 1)})
    rows.sort(key=lambda r: (-r["lift"], -r["recent"]))
    return _drop_nested(rows)[:top]


def _drop_nested(rows: list[dict]) -> list[dict]:
    """Keep "opus 5.5" and drop "5.5" when both surge on the same sources."""
    kept: list[dict] = []
    for r in rows:
        if any(r["term"] in k["term"].split() and r["recent"] <= k["recent"] for k in kept):
            continue
        kept.append(r)
    return kept


def top_counts(items: list[str], n: int) -> list[tuple[str, int]]:
    return Counter(items).most_common(n)

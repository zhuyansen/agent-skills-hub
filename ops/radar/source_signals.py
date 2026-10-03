"""Radar signal ①, the sources: where a new name is said first.

x_new    names in the last day's posts of the labs and bloggers in sources.json (via
         AIsa) that none of those accounts has used in the last VOCAB_DAYS. The
         vocabulary is kept in the snapshot dir; the first run only builds it.
hf_new   models that entered Hugging Face's trending top HF_TOP since yesterday (the
         public API, no key; AIsa has no Hugging Face tool). Quantised and fine-tuned
         copies of one model are grouped under its base name.
"""
from __future__ import annotations

import gzip
import json
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import aisa
from terms import STOP, _drop_nested, names

HERE = Path(__file__).resolve().parent
LOOKBACK_HOURS = 30          # the run is daily; 6 hours of overlap covers a late run
VOCAB_DAYS = 60
X_MIN_LIKES = 100            # a name only one account used needs this much attention,
PER_POST = 3                 # and must look like a name; one post yields at most this many
HF_TOP, HF_FETCH = 50, 100   # entering the top 50 against yesterday's top 100
TOP = 25
UA = "Mozilla/5.0 (compatible; agentskillshub-radar/1.0; +https://agentskillshub.top)"


def _load(path: Path):
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else None


def _save(path: Path, data) -> None:
    path.write_bytes(gzip.compress(json.dumps(data, ensure_ascii=False).encode()))


def accounts() -> list[tuple[str, str]]:
    cfg = json.loads((HERE / "sources.json").read_text())
    return [(h, "lab") for h in cfg["labs"]] + [(h, "blogger") for h in cfg["bloggers"]]


def _posted(post: dict) -> datetime | None:
    try:
        return datetime.strptime(post["createdAt"], "%a %b %d %H:%M:%S %z %Y")
    except (KeyError, ValueError):
        return None


def novel_names(posts: list[dict], vocab: dict[str, str], now: datetime) -> list[dict]:
    """Names in recent posts that are not in the vocabulary, with who said them.
    `posts` items: {"account", "text", "likes", "url", "created"}."""
    since = now - timedelta(hours=LOOKBACK_HOURS)
    found: dict[str, dict] = {}
    for p in posts:
        if p["created"] is None or p["created"] < since or p["text"].startswith("RT @"):
            continue
        strong = names(p["text"], strong=True)
        for term in names(p["text"]):
            if term in vocab:
                continue
            row = found.setdefault(term, {"term": term, "sources": set(), "likes": 0, "examples": [], "strong": False})
            if p["account"] not in row["sources"]:
                row["likes"] += p["likes"]
                row["examples"].append(f"@{p['account']}: {' '.join(p['text'].split())[:80]}")
            row["sources"].add(p["account"])
            row["strong"] |= term in strong
    rows = [r for r in found.values()
            if len(r["sources"]) >= 2 or (r["strong"] and r["likes"] >= X_MIN_LIKES)]
    # One viral post must not fill the report: keep its PER_POST longest single-account names.
    per_post: dict[str, int] = {}
    kept = []
    for r in sorted(rows, key=lambda r: (-len(r["sources"]), -len(r["term"]))):
        if len(r["sources"]) == 1:
            post = r["examples"][0]
            if per_post.get(post, 0) >= PER_POST:
                continue
            per_post[post] = per_post.get(post, 0) + 1
        kept.append(r)
    rows = kept
    for r in rows:
        r.pop("strong")
        r["recent"] = len(r["sources"])
        r["note"] = f"X {r['recent']} 个账号 ♥{r['likes']}"
        r["sources"] = sorted(r["sources"])
    rows.sort(key=lambda r: (-r["recent"], -r["likes"]))
    return _drop_nested(rows)[:TOP]


def x_new(snapshot_dir: Path) -> dict:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    handles = accounts()
    data, cost = aisa.call_all([{"call_id": h, "tool": "get_twitter_user_last_tweets", "arguments": {"userName": h}}
                            for h, _ in handles])
    posts = []
    for h, _ in handles:
        for t in ((data.get(h) or {}).get("data") or {}).get("tweets") or []:
            posts.append({"account": h, "text": t.get("text") or "", "likes": int(t.get("likeCount") or 0),
                          "url": t.get("url", ""), "created": _posted(t)})
    path = snapshot_dir / "x_vocab.json.gz"
    vocab: dict[str, str] | None = _load(path)
    first_run = vocab is None
    now = datetime.now(timezone.utc)
    rows = [] if first_run else novel_names(posts, vocab, now)
    # Every name in every fetched post joins the vocabulary, old posts included, so
    # tomorrow only what is new tomorrow is reported.
    vocab = vocab or {}
    today, cutoff = date.today().isoformat(), (date.today() - timedelta(days=VOCAB_DAYS)).isoformat()
    for p in posts:
        for term in names(p["text"]):
            vocab[term] = today
    if posts:   # a failed fetch keeps yesterday's vocabulary
        _save(path, {t: d for t, d in vocab.items() if d >= cutoff})
    return {"accounts": len(handles), "answered": len(data), "posts": len(posts), "cost_micros": cost,
            "first_run": first_run, "terms": rows}


_HF_NOISE = re.compile(r"[-_.](gguf|ggml|awq|gptq|fp8|fp16|bf16|int[48]|mlx|exl2|onnx|uncensored|abliterated|"
                       r"instruct|chat|it|base|preview|turbo|lora|q\d\w*|\d+(\.\d+)?b|a\d+(\.\d+)?b)(?=[-_.]|$)", re.I)


def base_name(model_id: str) -> str:
    """'abenzerps/Qwen-Image-2.1-Uncensored-GGUF' -> 'qwen image 2.1'."""
    name = model_id.split("/")[-1]
    for _ in range(4):   # suffixes stack: -27B-Instruct-GGUF
        name = _HF_NOISE.sub("", name)
    return re.sub(r"[-_]+", " ", name).strip().lower()


def hf_new(snapshot_dir: Path) -> dict:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(f"https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit={HF_FETCH}",
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as res:
        models = json.load(res)
    path = snapshot_dir / "hf_top.json.gz"
    before = _load(path)
    if models:
        _save(path, [m["id"] for m in models])
    if before is None:
        return {"models": len(models), "first_run": True, "terms": []}
    seen = set(before)
    grouped: dict[str, dict] = {}
    for rank, m in enumerate(models[:HF_TOP], 1):
        if m["id"] in seen:
            continue
        term = base_name(m["id"])
        if not term or term in STOP:
            continue
        g = grouped.setdefault(term, {"term": term, "rank": rank, "copies": 0, "examples": []})
        g["copies"] += 1
        g["examples"].append(f"{m['id']} ({m.get('pipeline_tag') or '?'}, ♥{m.get('likes', 0)})")
    rows = sorted(grouped.values(), key=lambda g: g["rank"])
    for g in rows:
        g["recent"] = g["copies"]
        g["note"] = f"HF 新进榜第 {g['rank']} 名" + (f",{g['copies']} 个版本" if g["copies"] > 1 else "")
    return {"models": len(models), "first_run": False, "terms": rows[:TOP]}

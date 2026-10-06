"""English descriptions for scenario-page cards whose GitHub description is not in English.

  python ops/jev-review/describe_en.py [--limit N]

The English pages showed some repos' own descriptions in Japanese, Chinese or Korean:
250 cards on 31 live pages (ppt-presentation 44, claude-video-skills 36, anti-slop 36;
10-06). Those words entered the page's word-frequency list ("生 成", "编 辑" on the PPT
page, 哥飞's On Page audit) and told Google the English page is partly not English.

Same pipeline as the Chinese descriptions (daily_video_pass.describe_zh): FlatRouter GPT
writes, Jev checks it says what the original says and adds nothing; below FAITHFUL_MIN
the card keeps its original text. Candidates are read from the live pages (the cards the
site shows now); written ones go to frontend/scripts/scenario-desc-en.json, which the
generator reads (scenario-kinds.mjs descEn). Runs in CI (describe-en.yml): the keys live
in GitHub secrets.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "ops/awesome")]
import daily_video_pass as dvp  # noqa: E402

DESC_EN = ROOT / "frontend/scripts/scenario-desc-en.json"
SITE = "https://agentskillshub.top"
WORKERS, SAVE_EVERY = 10, 10
# English runs longer than Chinese for the same meaning: the 80-character cap of the
# Chinese descriptions cut 152 of the first 177 English ones mid-sentence (10-06).
EN_MAX = 160
NON_LATIN = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
NON_LATIN_SHARE = 0.3
CARD = re.compile(r'<a class="bp-card-title" href="/skill/([^"/]+/[^"/]+)/".*?<p class="bp-card-desc"[^>]*data-en="([^"]*)"', re.S)
PROMPT = ("Translate this GitHub repository description into plain English. Say only what it says; drop "
          "marketing words (world's first, ultimate, 100M views). Keep product, model and technique names "
          "as written (Claude Code, Codex, Remotion, HyperFrames, MCP, skill, agent). At most 150 characters, "
          "no pipes or line breaks. Output only the translation.")
FAITHFUL_EN = {
    "same_meaning": {"type": "noul", "instructions": {
        "question": "Does `en` say what `original` says, in English?",
        "focus": "The main claim and what the tool does must match; a shorter wording is fine."}},
    "adds_nothing": {"type": "noul", "instructions": {
        "question": "Does `en` avoid claims, numbers or features that are not in `original`?"}},
}
UA = "Mozilla/5.0 (compatible; agentskillshub-describe/1.0; +https://agentskillshub.top)"


def not_english(text: str) -> bool:
    letters = re.sub(r"\s", "", text)
    return bool(letters) and len(NON_LATIN.findall(letters)) >= NON_LATIN_SHARE * len(letters)


def live_slugs() -> list[str]:
    pages = json.loads((ROOT / "frontend/scripts/scenario-keywords.json").read_text())
    return [p["slug"] for p in pages if not p.get("retired")]


def candidates(have: dict[str, str]) -> dict[str, str]:
    """repo -> its original description, for cards on live pages not in English and not done yet."""
    found: dict[str, str] = {}
    for slug in live_slugs():
        req = urllib.request.Request(f"{SITE}/best/{slug}/", headers={"User-Agent": UA})
        page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        for repo, desc in CARD.findall(page):
            desc = html.unescape(desc)
            if repo not in have and not_english(desc):
                found.setdefault(repo, desc)
    return found


def faithful(jev, original: str, en: str) -> float:
    state = json.dumps({"original": original[:600], "en": en}, ensure_ascii=False)
    answers = jev.decisions(state, FAITHFUL_EN).answers
    return min(float(answers.get(k, {}).get("noul", 0.0)) for k in FAITHFUL_EN)


def describe_en(jev, original: str) -> str:
    """An English description Jev accepts, or "" (the card keeps its original)."""
    for _ in range(2):
        en = dvp.translate(original, PROMPT, EN_MAX)
        if en and not not_english(en) and faithful(jev, original, en) >= dvp.FAITHFUL_MIN:
            return en
    return ""


def save(done: dict[str, str]) -> None:
    have = json.loads(DESC_EN.read_text()) if DESC_EN.exists() else {}
    have.update({k: v for k, v in done.items() if v})
    DESC_EN.write_text(json.dumps(have, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def main() -> int:
    from jev_client import OpenRouter
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    have = json.loads(DESC_EN.read_text()) if DESC_EN.exists() else {}
    have = {k: v for k, v in have.items() if not v.endswith("…")}   # cut short: write again
    todo = list(candidates(have).items())[:limit]
    print(f"{len(todo)} descriptions to translate ({len(have)} already done)", flush=True)
    jev, done = OpenRouter(), {}
    with ThreadPoolExecutor(WORKERS) as pool:
        for start in range(0, len(todo), SAVE_EVERY):
            chunk = todo[start:start + SAVE_EVERY]
            done.update(zip((r for r, _ in chunk), pool.map(lambda item: describe_en(jev, item[1]), chunk)))
            save(done)
            print(f"  {min(start + SAVE_EVERY, len(todo))}/{len(todo)}", flush=True)
    kept = sum(bool(v) for v in done.values())
    print(f"written {kept}, kept the original {len(done) - kept}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

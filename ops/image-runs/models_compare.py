"""The model line-up for the image page (owner, 2026-11-07): the test's poster, drawn once by each
image model on APIMart, then judged line by line like the skills' posters.

  python3 ops/image-runs/models_compare.py      # -> ops/image-runs/models/{<model>.<ext>, results.json}

Same prompt for every model: the brief's six poster lines, 3:4. One image each, no retries of a
paid submit. A model whose request format is not documented and is refused is recorded as such.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "models"
sys.path.insert(0, str(HERE))
from score_image import POSTER_Q, ask, env  # noqa: E402 (the same judge and question as the skills')

PROMPT = ("A portrait poster for Morning Loaf, a small neighbourhood bakery opening this Saturday: a loaf of bread in warm "
          "morning light. The poster shows exactly these six lines of text, spelled exactly like this (punctuation and "
          "currency signs included), and no other text: \"Morning Loaf\" / \"Grand opening · Saturday 9 am\" / "
          "\"晨光面包 · 周六上午九点开业\" / \"Sourdough £4.50 · Croissant £2.20\" / \"12 Elm Street, Bristol\" / \"前一百位顾客送一个可颂\".")
# (label, model id, request extras). Ratio sizes everywhere; gpt-image-1 takes only 1:1, 3:2 and 2:3.
MODELS = [
    ("GPT Image 1", "gpt-image-1", {"size": "2:3"}), ("GPT Image 2", "gpt-image-2", {"size": "3:4", "resolution": "1k"}),
    ("GPT Image 2.6", "gpt-image-2.6-ext", {"size": "3:4", "resolution": "1k"}),
    ("Nano Banana", "gemini-2.5-flash-image-preview", {"size": "3:4", "resolution": "1K"}),
    ("Nano Banana 2", "gemini-3.1-flash-image-preview", {"size": "3:4", "resolution": "1K"}),
    ("Nano Banana Pro", "gemini-3-pro-image-preview", {"size": "3:4", "resolution": "1K"}),
    ("Nano Banana 2.1", "gemini-nano-banana-2.1-ext", {"size": "3:4", "resolution": "1K"}),
    ("Imagen 4", "imagen-4.0-apimart", {"size": "3:4"}),
    ("FLUX 2 Pro", "flux-2-pro", {"size": "3:4", "resolution": "1MP"}), ("FLUX 3", "flux-3-image", {"size": "3:4"}),
    ("Muse", "muse-image-ext", {"size": "3:4"}), ("Seedream 5 Pro", "seedream-5-0-pro", {"size": "3:4"}),
    ("Qwen-Image 3 Pro", "qwen-image-3.0-pro", {"size": "3:4"}), ("Grok Imagine 2", "grok-imagine-image-2.0", {"size": "3:4"}),
    ("Midjourney", "midjourney", {"size": "3:4"}), ("MAI Image 2.6", "mai-image-2.6", {"size": "3:4"}),
    ("Hunyuan Image 3.5", "hy-image-v3.5-preview", {"size": "3:4"}), ("Wan 2.7 Image Pro", "wan2.7-image-pro", {"size": "3:4"}),
    ("Z-Image Turbo", "z-image-turbo", {"size": "3:4"}),
]
BASE = "https://api.apimart.ai/v1"


def get(url: str, headers: dict) -> requests.Response:
    """A GET with retries: the local network drops TLS reads now and then."""
    for i in range(6):
        try:
            return requests.get(url, headers=headers, timeout=60)
        except requests.exceptions.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"GET failed: {url}")


def wait(task_id: str, headers: dict) -> dict:
    for _ in range(240):
        task = get(f"{BASE}/tasks/{task_id}", headers).json()["data"]
        if task.get("status") in ("completed", "failed", "cancelled"):
            return task
        time.sleep(3)
    return {"status": "timeout"}


def draw(label: str, model: str, extra: dict, headers: dict) -> dict:
    row, t0 = {"label": label, "model": model}, time.time()
    try:
        r = requests.post(f"{BASE}/images/generations", headers=headers, timeout=60, json={"model": model, "prompt": PROMPT, "n": 1, **extra})
    except requests.exceptions.RequestException as e:
        return {**row, "status": "submit dropped (not resent)", "error": str(e)[:160]}
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or not body.get("data"):
        return {**row, "status": f"refused {r.status_code}", "error": json.dumps(body, ensure_ascii=False)[:200]}
    task = wait(body["data"][0]["task_id"], headers)
    urls = [u for im in (task.get("result") or {}).get("images", []) for u in im.get("url", [])]
    row.update(status=task.get("status"), cost=task.get("cost"), seconds=round(time.time() - t0),
               error=(task.get("error") or {}).get("message", "")[:160])
    if urls:
        raw = get(urls[0], headers).content
        ext = "jpg" if raw[:2] == b"\xff\xd8" else "webp" if raw[:4] == b"RIFF" else "png"
        (OUT / f"{model}.{ext}").write_bytes(raw)
        row["file"] = f"{model}.{ext}"
    return row


def main() -> None:
    e = env()
    OUT.mkdir(exist_ok=True)
    headers = {"Authorization": f"Bearer {e['APIMART_MULTI_KEY']}", "User-Agent": "Mozilla/5.0"}
    rows = []
    for label, model, extra in MODELS:
        row = draw(label, model, extra, headers)
        if row.get("file"):
            try:
                row["judge"] = ask(e, POSTER_Q, [OUT / row["file"]])
            except Exception as err:  # noqa: BLE001 (a judge failure leaves the picture for a later look)
                row["judge_error"] = str(err)[:160]
        exact = sum(1 for l in (row.get("judge") or {}).get("lines", []) if l.get("exact"))
        print(f"{label:20} {row.get('status')} ${row.get('cost')} {row.get('seconds')}s lines exact {exact}/6 {row.get('error', '')[:80]}", flush=True)
        rows.append(row)
        (OUT / "results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

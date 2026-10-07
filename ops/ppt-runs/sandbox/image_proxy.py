"""OpenAI-compatible image endpoint for the sandbox, backed by an async provider.

Skills call the OpenAI SDK (POST /v1/images/generations and returns the image).
The provider (IMAGE_API_BASE_URL, e.g. apimart) instead returns a task id; this
proxy submits, polls /tasks/{id}, downloads the result and answers in OpenAI's
shape. Any requested image model maps to IMAGE_MODEL. The real key stays here;
skills see OPENAI_BASE_URL=http://127.0.0.1:8787/v1 and a placeholder key.
Every call is appended to /out/images.jsonl (model, size, quality, cost, seconds).
"""
import base64
import json
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.environ["IMAGE_API_BASE_URL"].rstrip("/")
KEY = os.environ["IMAGE_API_KEY"]
MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-2.5-flare")
POLL_SECONDS, TIMEOUT_SECONDS = 2, 300
LOG = "/out/images.jsonl"


def call(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def wait(task_id: str) -> dict:
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        task = call("GET", f"/tasks/{task_id}")["data"]
        if task.get("status") in ("completed", "failed", "cancelled"):
            return task
        time.sleep(POLL_SECONDS)
    raise TimeoutError(task_id)


def generate(req: dict) -> dict:
    body = {k: v for k, v in req.items() if k in ("prompt", "size", "quality", "n", "background")}
    body["model"] = MODEL
    t0 = time.time()
    task = wait(call("POST", "/images/generations", body)["data"][0]["task_id"])
    urls = [u for img in (task.get("result") or {}).get("images", []) for u in img.get("url", [])]
    with open(LOG, "a") as f:
        f.write(json.dumps({"model": MODEL, "size": body.get("size"), "quality": body.get("quality"),
                            "status": task.get("status"), "cost": task.get("cost"), "seconds": round(time.time() - t0)}) + "\n")
    if task.get("status") != "completed" or not urls:
        raise RuntimeError(f"image task {task.get('status')}")
    images = [base64.b64encode(urllib.request.urlopen(u, timeout=120).read()).decode() for u in urls]
    return {"created": int(time.time()), "data": [{"b64_json": b} for b in images]}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 (http.server naming)
        if not self.path.rstrip("/").endswith("/images/generations"):
            return self.reply(404, {"error": {"message": f"only images/generations is proxied, not {self.path}"}})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            self.reply(200, generate(req))
        except Exception as e:  # noqa: BLE001 (report any upstream failure to the caller)
            self.reply(502, {"error": {"message": str(e)[:300], "type": "upstream_error"}})

    def reply(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def log_message(self, *args):  # quiet
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()

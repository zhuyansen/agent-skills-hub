"""OpenAI-compatible image endpoints for the sandbox, backed by an async provider.

Skills call the OpenAI SDK (POST /v1/images/generations and returns the image).
The provider (IMAGE_API_BASE_URL, e.g. apimart) instead returns a task id; this
proxy submits, polls /tasks/{id}, downloads the result and answers in OpenAI's
shape. Any requested image model maps to IMAGE_MODEL. The real key stays here;
skills see OPENAI_BASE_URL=http://127.0.0.1:8787/v1 and a placeholder key.
POST /images/edits (multipart, as the OpenAI SDK sends it) becomes a generation with
the uploaded images as reference images (`image_urls`); masks are not supported
upstream and are ignored (logged). Every call is appended to /out/images.jsonl (model, size, quality, cost, seconds).
POST /chat/completions is passed through to TEXT_API_BASE_URL (when TEXT_API_KEY is set), with any model
mapped to TEXT_MODEL: tools that need their own text LLM key get one, as a user would plug in theirs.
Each text call is appended to /out/text.jsonl.

IMAGE_ROUTES=1 (the image test, ops/image-runs): each image call goes to the model family the skill asked
for instead of IMAGE_MODEL (image_routes.py), and two more formats are answered: Google's Gemini API
(/v1beta/models/<m>:generateContent, image and text; text goes to the provider's Gemini endpoint) and
OpenAI's Responses API with the image_generation tool. With TLS_CERT/TLS_KEY set, the same handler also
listens on 127.0.0.1:443, so skills that call generativelanguage.googleapis.com or api.openai.com by name
reach it too (run_one.sh points those names at 127.0.0.1 and trusts a throwaway CA).
"""
import base64
import email
import email.policy
import json
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.environ["IMAGE_API_BASE_URL"].rstrip("/")
KEY = os.environ["IMAGE_API_KEY"]
MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-2.5-flare")
POLL_SECONDS, TIMEOUT_SECONDS = 2, 300
OUT_DIR = os.environ.get("PROXY_LOG_DIR", "/out")   # /out in the container; a temp folder for a local try
LOG = f"{OUT_DIR}/images.jsonl"
TEXT_BASE = os.environ.get("TEXT_API_BASE_URL", "").rstrip("/")
TEXT_KEY = os.environ.get("TEXT_API_KEY", "")
TEXT_MODEL = os.environ.get("TEXT_MODEL", "gpt-6-astra")
TEXT_LOG = f"{OUT_DIR}/text.jsonl"
ROUTES = bool(os.environ.get("IMAGE_ROUTES"))
FORCE = bool(os.environ.get("IMAGE_FORCE_NEWEST"))   # every call to the newest model of its family
if ROUTES:
    import image_routes as routes  # noqa: E402 (same folder; only the image test needs it)
# The provider's CDN turns away urllib's default User-Agent (APIMart, 2026-10-29: 403 before submit).
UA = "Mozilla/5.0 (sandbox image proxy)"
GEMINI_PATH = re.compile(r"/v1(?:beta|alpha)?/models/([^/:]+):(generateContent|streamGenerateContent)$")
GEMINI_TEXT_FALLBACK = "gemini-3-flash-preview"


def _open(req: urllib.request.Request, timeout: int, tries: int):
    """urlopen with retries for dropped connections (the local network drops a TLS read now and
    then). A paid submit is retried once at most: a second image costs cents, not dollars."""
    for attempt in range(tries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ssl.SSLError, ConnectionError, TimeoutError):
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def call(method: str, path: str, body: dict | None = None, base: str = BASE) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": UA})
    with _open(req, 120, 2 if method == "POST" else 3) as r:
        return json.load(r)


def fetch(url: str) -> bytes:
    with _open(urllib.request.Request(url, headers={"User-Agent": UA}), 120, 3) as r:
        return r.read()


def wait(task_id: str) -> dict:
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        task = call("GET", f"/tasks/{task_id}")["data"]
        if task.get("status") in ("completed", "failed", "cancelled"):
            return task
        time.sleep(POLL_SECONDS)
    raise TimeoutError(task_id)


def provider_request(req: dict, images: list[str] | None) -> dict:
    """The provider's body: one model for everything, or (IMAGE_ROUTES) the family asked for."""
    if not ROUTES:
        body = {k: v for k, v in req.items() if k in ("prompt", "size", "quality", "n", "background")}
        body["model"] = MODEL
        if images:   # edits: the provider takes reference images on the generation endpoint
            body["image_urls"] = images
        return body
    model = req.get("_model") or routes.openai_model(req.get("model"), FORCE)
    return routes.provider_body(model, req.get("prompt", ""), req.get("size"), images or [], req.get("_resolution"))


def log_image(kind: str, req: dict, body: dict, task: dict, seconds: int) -> None:
    with open(LOG, "a") as f:
        f.write(json.dumps({"kind": kind, "asked": req.get("model"), "model": body["model"], "size": body.get("size"),
                            "quality": body.get("quality") or body.get("resolution"), "status": task.get("status"),
                            "cost": task.get("cost"), "seconds": seconds}) + "\n")


def generate(req: dict, images: list[str] | None = None, kind: str = "generate") -> dict:
    body = provider_request(req, images)
    t0 = time.time()
    task = wait(call("POST", "/images/generations", body)["data"][0]["task_id"])
    urls = [u for img in (task.get("result") or {}).get("images", []) for u in img.get("url", [])]
    log_image(kind, req, body, task, round(time.time() - t0))
    if task.get("status") != "completed" or not urls:
        raise RuntimeError(f"image task {task.get('status')}: {(task.get('error') or {}).get('message', '')}"[:300])
    images_b64 = [base64.b64encode(fetch(u)).decode() for u in urls]
    return {"created": int(time.time()), "data": [{"b64_json": b} for b in images_b64]}


def multipart(raw: bytes, ctype: str) -> tuple[dict, list[str], bool]:
    """Fields, images as data URIs, and whether a mask was sent (not supported upstream)."""
    msg = email.message_from_bytes(b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + raw, policy=email.policy.default)
    fields, images, mask = {}, [], False
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition") or ""
        data = part.get_payload(decode=True) or b""
        if name.startswith("image"):
            mime = part.get_content_type() if part.get_content_type() != "application/octet-stream" else "image/png"
            images.append(f"data:{mime};base64,{base64.b64encode(data).decode()}")
        elif name == "mask":
            mask = True
        else:
            fields[name] = data.decode(errors="ignore")
    return fields, images, mask


def edit(raw: bytes, ctype: str) -> dict:
    if ctype.startswith("multipart/"):
        fields, images, mask = multipart(raw, ctype)
    else:   # JSON with base64 or URLs
        req = json.loads(raw or b"{}"); fields = req
        images = [x if str(x).startswith(("http", "data:")) else f"data:image/png;base64,{x}" for x in (req.get("image") if isinstance(req.get("image"), list) else [req.get("image")]) if x]
        mask = bool(req.get("mask"))
    if mask:
        with open(LOG, "a") as f: f.write(json.dumps({"kind": "edit", "note": "mask ignored: not supported upstream"}) + "\n")
    return generate(fields, images, kind="edit")


def chat(raw: bytes) -> tuple[bytes, str]:
    """Forward a chat completion to the text provider; returns the body and its content type."""
    req = json.loads(raw or b"{}")
    asked, req["model"] = req.get("model"), TEXT_MODEL
    t0 = time.time()
    up = urllib.request.Request(TEXT_BASE + "/chat/completions", data=json.dumps(req).encode(), method="POST",
                                headers={"Authorization": f"Bearer {TEXT_KEY}", "Content-Type": "application/json",
                                         "User-Agent": UA})
    with urllib.request.urlopen(up, timeout=300) as r:
        body, ctype = r.read(), r.headers.get("Content-Type", "application/json")
    with open(TEXT_LOG, "a") as f:
        f.write(json.dumps({"asked": asked, "model": TEXT_MODEL, "stream": bool(req.get("stream")),
                            "seconds": round(time.time() - t0)}) + "\n")
    return body, ctype


def gemini_image(model: str, body: dict) -> dict:
    prompt, images, ratio, size = routes.gemini_request(body)
    used = routes.gemini_image_model(model, FORCE)
    out = generate({"model": model, "prompt": prompt, "size": ratio, "_model": used, "_resolution": size},
                   images, kind="gemini")
    return routes.gemini_response([d["b64_json"] for d in out["data"]], used)


def gemini_text(model: str, body: dict) -> dict:
    """A text generateContent call, through the provider's Gemini endpoint (it wraps replies in
    {"code", "data"}). When the asked model fails there (missing, or 503), GEMINI_TEXT_FALLBACK answers."""
    root = re.sub(r"/v1$", "", BASE)
    names = list(dict.fromkeys((model, GEMINI_TEXT_FALLBACK)))
    for name in names:
        try:
            reply = call("POST", f"/v1beta/models/{name}:generateContent", body, base=root)
        except urllib.error.HTTPError:
            if name == names[-1]:
                raise
            continue
        with open(TEXT_LOG, "a") as f:
            f.write(json.dumps({"asked": model, "model": name, "format": "gemini"}) + "\n")
        return reply.get("data", reply)
    raise RuntimeError("no Gemini text model answered")


def responses_image(body: dict) -> dict | None:
    asked = routes.responses_image_request(body)
    if asked is None:
        return None
    out = generate({"model": "gpt-image-2", "prompt": asked[0], "size": asked[1]}, kind="responses")
    return routes.responses_image([d["b64_json"] for d in out["data"]], routes.openai_model("gpt-image-2", FORCE))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 (http.server naming)
        path = self.path.split("?")[0].rstrip("/")
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            if ROUTES and self.routed(path, raw):
                return
            if path.endswith("/chat/completions") and TEXT_KEY:
                return self.raw(200, *chat(raw))
            if not path.endswith(("/images/generations", "/images/edits")):
                return self.reply(404, {"error": {"message": f"only images/generations, images/edits and chat/completions are proxied, not {self.path}"}})
            if path.endswith("/images/edits"):
                return self.reply(200, edit(raw, self.headers.get("Content-Type", "")))
            self.reply(200, generate(json.loads(raw or b"{}")))
        except Exception as e:  # noqa: BLE001 (report any upstream failure to the caller)
            self.reply(502, {"error": {"message": str(e)[:300], "type": "upstream_error"}})

    def do_GET(self):  # noqa: N802 (http.server naming)
        listing = routes.model_list(self.path.split("?")[0].rstrip("/")) if ROUTES else None
        if listing is None:
            return self.reply(404, {"error": {"message": f"not proxied: GET {self.path}"}})
        self.reply(200, listing)

    def routed(self, path: str, raw: bytes) -> bool:
        """The image test's extra formats; True when this request was one of them and is answered."""
        m = GEMINI_PATH.search(path)
        if m:
            model, method, body = m.group(1), m.group(2), json.loads(raw or b"{}")
            reply = gemini_image(model, body) if routes.is_gemini_image_call(model, body) else gemini_text(model, body)
            self.gemini_reply(reply, stream=method == "streamGenerateContent")
            return True
        if path.endswith("/responses"):
            reply = responses_image(json.loads(raw or b"{}"))
            if reply is not None:
                self.reply(200, reply)
                return True
        return False

    def gemini_reply(self, reply: dict, stream: bool) -> None:
        """streamGenerateContent gets the whole answer as one chunk: one SSE event (alt=sse), else a JSON array."""
        if not stream:
            return self.reply(200, reply)
        if "alt=sse" in self.path:
            return self.raw(200, f"data: {json.dumps(reply)}\n\n".encode(), "text/event-stream")
        self.raw(200, json.dumps([reply]).encode(), "application/json")

    def reply(self, code: int, body: dict) -> None:
        self.raw(code, json.dumps(body).encode(), "application/json")

    def raw(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *args):  # quiet
        pass


def serve_tls(cert: str, key: str) -> None:
    """The same handler on 127.0.0.1:443 for skills that call the providers' hostnames directly."""
    server = ThreadingHTTPServer(("127.0.0.1", 443), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()


if __name__ == "__main__":
    if os.environ.get("TLS_CERT"):
        serve_tls(os.environ["TLS_CERT"], os.environ["TLS_KEY"])
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()

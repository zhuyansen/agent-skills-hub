"""Bluesky posts with links, for the social-sites signal (social_sites.py). Free, no login.

What answered without an account on 2026-10-21:
  - app.bsky.feed.searchPosts on api.bsky.app: 200, a page of up to 100 posts. The same
    call on public.api.bsky.app, the host meant for calls without login, answers 403:
    its cache refuses search, so this may close one day too;
  - getAuthorFeed and getFeed on public.api.bsky.app: 200, but a list of accounts has to
    be kept, and the Discover feed is news (300 posts over a day, 66 with links, nearly
    all to news sites);
  - Jetstream, the firehose as JSON over a websocket (it closes a client that does not
    answer its pings): 60 s gave 1,635 posts, 22% with links, and every domain two
    people linked was a platform or a news site.
So the step searches: the most-liked posts of the window for each of QUERIES, one page
each, PAUSE seconds apart, len(QUERIES) requests a run. Four of those queries on 10-21
found a site registered two months earlier that two people had linked. When the search
is refused (401 or 403) the step samples Jetstream for SAMPLE_SECONDS instead (stdlib
only), so the signal keeps a Bluesky source, a thinner one; the status line says which
ran.

A post's links are its link facets (app.bsky.richtext.facet#link) and its external embed,
alone or beside a quoted post (recordWithMedia).
"""
from __future__ import annotations

import base64
import http.client
import json
import os
import socket
import ssl
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SEARCH = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
QUERIES = ("this site", "this website", "made a website", "just launched", "free tool", "ai tool")
LIMIT = 100                 # posts a page, the API's maximum
PAUSE = 1.0                 # seconds between two searches
TIMEOUT = 30
REFUSED = {401, 403}        # search wants a login: sample the firehose instead
JETSTREAM_HOSTS = ("jetstream2.us-east.bsky.network", "jetstream1.us-east.bsky.network")
JETSTREAM_PATH = "/subscribe?wantedCollections=app.bsky.feed.post"
SAMPLE_SECONDS = 90
SAMPLE_MAX = 4000           # posts read at most; about 30 a second come through
CONNECT_TIMEOUT = 20
READ_TIMEOUT = 10           # a stream silent this long has stalled: keep what it gave
HEAD_MAX = 16384            # bytes of an HTTP answer's head
RECV = 65536
PONG, CLOSE, PING = 0xA, 0x8, 0x9
UA = "agentskillshub-radar/1.0 (+https://agentskillshub.top)"
LINK = "app.bsky.richtext.facet#link"
POST = "app.bsky.feed.post"


def posts(since: datetime) -> dict:
    """Bluesky posts with links since `since`: searched, or sampled from Jetstream when the
    search is refused. Never raises: a failure is in `errors` and `posts` holds what came."""
    found, requests, refused, errors = search(since)
    if refused:
        try:
            found += sample(SAMPLE_SECONDS, SAMPLE_MAX)
        except OSError as exc:
            errors.append(f"Jetstream {' '.join(str(exc).split())[:100]}")
    unique = list({p["url"] or f"{p['author']}|{p['text']}": p for p in found}.values())
    return {"source": "jetstream" if refused else "search", "requests": requests, "refused": refused,
            "read": len(unique), "posts": [p for p in unique if p["links"]], "errors": errors}


def search(since: datetime) -> tuple[list[dict], int, str, list[str]]:
    """(posts, requests made, "HTTP 403" when the search was refused, errors) for the most-liked
    posts since `since` of each query in QUERIES."""
    out, errors = [], []
    for i, q in enumerate(QUERIES):
        if i:
            time.sleep(PAUSE)
        try:
            out += [from_view(v) for v in _search_page(q, since)]
        except urllib.error.HTTPError as exc:
            if exc.code in REFUSED:
                return out, i + 1, f"HTTP {exc.code}", errors
            errors.append(f"“{q}” HTTP {exc.code}")
        except (OSError, ValueError, http.client.HTTPException) as exc:
            errors.append(f"“{q}” {type(exc).__name__}")
    return out, len(QUERIES), "", errors


def _search_page(q: str, since: datetime) -> list[dict]:
    query = urllib.parse.urlencode({"q": q, "sort": "top", "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": LIMIT})
    req = urllib.request.Request(f"{SEARCH}?{query}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
        return json.load(res).get("posts") or []


def from_view(view: dict) -> dict:
    """A searchPosts PostView as the radar's post. `at` is when Bluesky indexed it: a post's
    own createdAt is set by the client and can be anything."""
    author = view.get("author") or {}
    rec = view.get("record") or {}
    return make_post(author.get("handle") or author.get("did") or "", view.get("uri", ""), rec,
                     int(view.get("likeCount") or 0), str(view.get("indexedAt") or rec.get("createdAt") or ""))


def make_post(author: str, uri: str, rec: dict, likes: int, at: str) -> dict:
    """{"platform", "author", "url", "text", "likes", "at", "links"}; `at` is ISO 8601."""
    return {"platform": "bluesky", "author": author, "url": post_url(author, uri),
            "text": " ".join(str(rec.get("text") or "").split()), "likes": likes, "at": at, "links": links(rec)}


def post_url(author: str, uri: str) -> str:
    """'at://did:plc:x/app.bsky.feed.post/3mabc' -> 'https://bsky.app/profile/<author>/post/3mabc'."""
    rkey = uri.rsplit("/", 1)[-1] if uri.startswith("at://") else ""
    return f"https://bsky.app/profile/{author}/post/{rkey}" if author and rkey else ""


def links(rec: dict) -> list[str]:
    """A post record's external links: its link facets, then its external embed."""
    found = [f.get("uri") for facet in rec.get("facets") or [] for f in facet.get("features") or []
             if f.get("$type") == LINK]
    embed = rec.get("embed") or {}
    found.append((embed.get("external") or (embed.get("media") or {}).get("external") or {}).get("uri"))
    return list(dict.fromkeys(u for u in found if isinstance(u, str) and u.startswith(("http://", "https://"))))


# --- Jetstream, when search is refused -----------------------------------------------------

def sample(seconds: float, most: int) -> list[dict]:
    """New posts from Jetstream for `seconds` or `most` posts, from the first host that
    answers. Raises OSError when none does."""
    error = ""
    for host in JETSTREAM_HOSTS:
        try:
            return read_stream(host, seconds, most)
        except OSError as exc:
            error = f"{host}: {exc}"
    raise OSError(error)


def read_stream(host: str, seconds: float, most: int) -> list[dict]:
    """Posts read off one Jetstream host. A stream that drops or stalls keeps what it gave."""
    sock, rest = ws_open(host)
    frames, out, read = Frames(sock, rest), [], 0
    end = time.monotonic() + seconds
    try:
        while time.monotonic() < end and read < most:
            post = event_post(frames.next_text())
            read += post is not None
            out += [post] if post else []
    except (OSError, ValueError):
        pass
    finally:
        sock.close()
    return out


def event_post(msg: bytes) -> dict | None:
    """The new post in one Jetstream event; None for anything else (deletes, likes, identity)."""
    ev = json.loads(msg)
    commit = ev.get("commit") or {}
    if ev.get("kind") != "commit" or commit.get("operation") != "create" or commit.get("collection") != POST:
        return None
    did = str(ev.get("did") or "")
    at = datetime.fromtimestamp(int(ev.get("time_us") or 0) / 1e6, timezone.utc).isoformat()
    return make_post(did, f"at://{did}/{POST}/{commit.get('rkey', '')}", commit.get("record") or {}, 0, at)


def ws_open(host: str) -> tuple[socket.socket, bytes]:
    """A websocket to `host` over TLS (RFC 6455 handshake), and the bytes read past its head."""
    sock = ssl.create_default_context().wrap_socket(_tcp(host), server_hostname=host)
    sock.settimeout(READ_TIMEOUT)
    key = base64.b64encode(os.urandom(16)).decode()
    sock.sendall((f"GET {JETSTREAM_PATH} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                  f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\nUser-Agent: {UA}\r\n\r\n").encode())
    status, rest = _head(sock)
    if b" 101 " not in status + b" ":
        sock.close()
        raise OSError(f"answered {status[:60].decode('latin-1')}")
    return sock, rest


def _tcp(host: str) -> socket.socket:
    """A TCP connection to host:443, through HTTPS_PROXY (CONNECT) when one is set: local runs."""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not proxy:
        return socket.create_connection((host, 443), timeout=CONNECT_TIMEOUT)
    p = urllib.parse.urlsplit(proxy)
    raw = socket.create_connection((p.hostname, p.port or 80), timeout=CONNECT_TIMEOUT)
    raw.sendall(f"CONNECT {host}:443 HTTP/1.1\r\nHost: {host}:443\r\n\r\n".encode())
    status, _ = _head(raw)
    if b" 200 " not in status + b" ":
        raw.close()
        raise OSError(f"proxy answered {status[:60].decode('latin-1')}")
    return raw


def _head(sock: socket.socket) -> tuple[bytes, bytes]:
    """(the status line of an HTTP answer, the bytes after its head)."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(RECV)
        if not chunk or len(buf) > HEAD_MAX:
            raise OSError("no HTTP answer")
        buf += chunk
    head, rest = buf.split(b"\r\n\r\n", 1)
    return head.split(b"\r\n", 1)[0], rest


class Frames:
    """Text messages off a websocket, answering pings (Jetstream closes a client that does
    not). Frames from a server are never masked (RFC 6455 5.1); a client's pong must be."""

    def __init__(self, sock: socket.socket, buf: bytes = b""):
        self.sock, self.buf = sock, buf

    def next_text(self) -> bytes:
        """The next whole text message. Raises OSError when the server closes."""
        parts: list[bytes] = []
        while True:
            op, fin, payload = self._frame()
            if op == CLOSE:
                raise OSError("closed by the server")
            if op == PING:
                self._pong(payload)
            elif op in (0, 1):          # a text frame, or the next part of one (binary and pongs are skipped)
                parts.append(payload)
            if fin and op in (0, 1):
                return b"".join(parts)

    def _frame(self) -> tuple[int, bool, bytes]:
        self._need(2)
        size, off = self.buf[1] & 0x7F, 2
        if size == 126:
            self._need(4)
            size, off = struct.unpack(">H", self.buf[2:4])[0], 4
        elif size == 127:
            self._need(10)
            size, off = struct.unpack(">Q", self.buf[2:10])[0], 10
        self._need(off + size)
        head, payload, self.buf = self.buf[0], self.buf[off:off + size], self.buf[off + size:]
        return head & 0x0F, bool(head & 0x80), payload

    def _need(self, n: int) -> None:
        while len(self.buf) < n:
            chunk = self.sock.recv(RECV)
            if not chunk:
                raise OSError("stream ended")
            self.buf += chunk

    def _pong(self, payload: bytes) -> None:
        mask = os.urandom(4)
        body = bytes(b ^ mask[i % 4] for i, b in enumerate(payload[:125]))
        self.sock.sendall(bytes([0x80 | PONG, 0x80 | len(body)]) + mask + body)

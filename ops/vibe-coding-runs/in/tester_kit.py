"""Browser helpers for the tester session of the vibe coding test (ops/vibe-coding-runs).

The tester imports this from its own test script; nothing here touches the app under test.

    import sys; sys.path.insert(0, "/in")
    from tester_kit import Browser, app_url, file_url
    first = file_url() or app_url()        # the "open" check: what double-clicking opens (file://)
    url = app_url()                        # every other check: index.html from a local address, or START.txt's command
    b = Browser(); page = b.open(first)    # ... then page.goto(url) for the other checks
    ...
    page = b.restart(url)                  # close the app and open it again (see Browser.restart)
    b.shot(page, "2-add")                  # -> ~/tester/shots/2-add.png
    b.close()

The browser is Chromium with a persistent profile, Chinese locale, Beijing time, and
downloads saved to ~/tester/downloads. Console errors and requests to hosts other than this machine are
written to ~/tester/browser.json when the browser closes.
"""
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

CHROMIUM = "/usr/bin/chromium"
HOME = Path.home()
WORK = HOME / "work"
OUT = HOME / "tester"
SHOTS = OUT / "shots"
DOWNLOADS = OUT / "downloads"
LOCAL = re.compile(r"^(https?|wss?)://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])(:\d+)?/")
URL_IN_LOG = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?[^\s'\"]*")
START_SECONDS = 180
STATIC_PORT = 8700


def _answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url.replace("0.0.0.0", "127.0.0.1"), timeout=5) as r:
            return r.status < 500
    except Exception:  # noqa: BLE001 (not up yet)
        return False


def start_command(cmd: str) -> str:
    """Run the one command from START.txt in ~/work, in the background, and return the
    local address it serves once that address answers (it is read from the command's output)."""
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / "server.log"
    with log.open("w") as f:
        subprocess.Popen(cmd, shell=True, cwd=WORK, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.time() + START_SECONDS
    while time.time() < deadline:
        for url in URL_IN_LOG.findall(log.read_text(errors="ignore")):
            if _answers(url):
                return url.replace("0.0.0.0", "127.0.0.1")
        time.sleep(2)
    raise RuntimeError(f"nothing answered within {START_SECONDS} s; see {log}")


def file_url() -> str | None:
    """The address double-clicking ~/work/output/index.html opens, or None when there is no index.html."""
    index = WORK / "output" / "index.html"
    return index.as_uri() if index.exists() else None


def _serve_output() -> str:
    """index.html from a local address instead of file://: the test browser's localStorage for
    file:// pages loses writes when the app is closed and opened again (1 in 10 for a correct app
    here), which would fail apps for the browser's sake. Use file_url() for the "open" check."""
    log = (OUT / "static.log").open("w")
    subprocess.Popen(["python3", __file__, "--serve", str(WORK / "output"), str(STATIC_PORT)],
                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    url = f"http://127.0.0.1:{STATIC_PORT}/index.html"
    deadline = time.time() + 20
    while time.time() < deadline and not _answers(url):
        time.sleep(0.5)
    return url


def app_url() -> str:
    """Where to use the app: index.html from a local address (see _serve_output), else the address
    the command in START.txt serves (started once: a later call reuses it while it still answers)."""
    OUT.mkdir(parents=True, exist_ok=True)
    saved = OUT / "url.txt"
    if saved.exists() and _answers(saved.read_text().strip()):
        return saved.read_text().strip()
    if (WORK / "output" / "index.html").exists():
        url = _serve_output()
    else:
        start = WORK / "output" / "START.txt"
        lines = [x.strip() for x in start.read_text().splitlines() if x.strip() and not x.strip().startswith("#")] if start.exists() else []
        if not lines:
            raise FileNotFoundError("neither ~/work/output/index.html nor a command in ~/work/output/START.txt")
        url = start_command(lines[0])
    saved.write_text(url)
    return url


class Browser:
    def __init__(self, profile: Path = OUT / "profile"):
        self.pw = sync_playwright().start()
        self.profile = profile
        self.ctx = None
        self.errors: list[str] = []
        self.outside: list[str] = []

    def _watch(self, page) -> None:
        page.on("console", lambda m: self.errors.append(m.text[:300]) if m.type == "error" else None)
        page.on("pageerror", lambda e: self.errors.append(str(e)[:300]))
        page.on("request", lambda r: self.outside.append(r.url[:200])
                if r.url.startswith(("http", "ws")) and not LOCAL.match(r.url) else None)

    def open(self, url: str):
        """Open the app in a tab: the first call starts the browser, a later one adds a tab."""
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        if self.ctx is None:
            self.ctx = self.pw.chromium.launch_persistent_context(
                str(self.profile), executable_path=CHROMIUM, args=["--no-sandbox"], viewport={"width": 1280, "height": 900},
                accept_downloads=True, downloads_path=str(DOWNLOADS), locale="zh-CN", timezone_id="Asia/Shanghai")
            page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        else:
            page = self.ctx.new_page()
        self._watch(page)
        page.goto(url, wait_until="load")
        page.wait_for_timeout(1000)
        return page

    def restart(self, url: str):
        """Close the app (every tab) and open it again in a new tab. Quitting Chromium itself is not
        used: stopped by a script, it loses localStorage writes still on their way to disk."""
        for p in list(self.ctx.pages):
            p.close()
        time.sleep(1)
        return self.open(url)

    def shot(self, page, name: str) -> str:
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / f"{name}.png"), full_page=True)
        return f"shots/{name}.png"

    def close(self) -> None:
        (OUT / "browser.json").write_text(json.dumps({"console_errors": self.errors, "outside_requests": sorted(set(self.outside))},
                                                     indent=1, ensure_ascii=False))
        if self.ctx:
            self.ctx.close()
        self.pw.stop()


def serve(folder: str, port: int) -> None:
    """A plain static server for _serve_output, with an empty answer for /favicon.ico, so the
    browser's request for an icon the app never asked for is not logged as an error of the app."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] == "/favicon.ico" and not (Path(folder) / "favicon.ico").exists():
                self.send_response(204); self.end_headers(); return
            super().do_GET()

    ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=folder)).serve_forever()


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["--serve"]:
        serve(sys.argv[2], int(sys.argv[3]))

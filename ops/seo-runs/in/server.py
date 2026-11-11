"""The SEO test site's server (sandbox/start_seo.sh runs it on port 80 as http://lumentea.test/).
Static files from ./site, plus the planted 301 chain /shop/ -> /store/ -> /teas/ (defect D11), an X-Robots-Tag: noindex
header on /teas/bai-mudan/ (D13) and a real 404."""
import http.server
import sys
from pathlib import Path

SITE = Path(__file__).parent / "site"
REDIRECTS = {"/shop/": "/store/", "/shop": "/store/", "/store/": "/teas/", "/store": "/teas/"}
NOINDEX_HEADER = ("/teas/bai-mudan/", "/teas/bai-mudan/index.html")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".html": "text/html; charset=utf-8", ".xml": "application/xml; charset=utf-8", ".txt": "text/plain; charset=utf-8"}

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(SITE), **k)

    def end_headers(self):
        if self.path.split("?", 1)[0] in NOINDEX_HEADER:
            self.send_header("X-Robots-Tag", "noindex")
        super().end_headers()

    def log_message(self, fmt, *args):   # one line per request, for the run's evidence (who fetched what)
        sys.stderr.write(f"{self.log_date_time_string()} {self.headers.get('User-Agent', '-')[:80]} {fmt % args}\n")

    def send_head(self):
        path = self.path.split("?", 1)[0]
        if path in REDIRECTS:
            self.send_response(301)
            self.send_header("Location", REDIRECTS[path])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        f = SITE / path.lstrip("/")
        missing = not f.exists() or (f.is_dir() and not (f / "index.html").exists())
        if missing or path.startswith("/404"):
            body = (SITE / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return None
        return super().send_head()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()

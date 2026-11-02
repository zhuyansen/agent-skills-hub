"""Pin the home page's layout shifts on the elements that move.

CrUX put the home page at CLS 0.17 (phone) and 0.13 (desktop) at p75 on 2026-11-02,
while PageSpeed's lab run, which loads once and never scrolls, saw 0. This drives
headless Chromium through what visitors do after the first paint: wait for the data,
scroll to the bottom, use the Explore tab. It does so as new visitors and as returning
visitors whose cached data is out of date, and records every layout-shift entry with
the elements that moved.

Read-only. GA, Clarity and the site-search log are blocked, so the runs leave nothing
in the site's own numbers. Pages load one at a time, about 23 loads in all.

    ~/.local/pipx/venvs/playwright/bin/python ops/perf/home_cls.py [--only SUBSTR] [--base URL]
"""
import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://agentskillshub.top"
OUT_DIR = Path(__file__).parent / "out"
BLOCKED = re.compile(
    r"googletagmanager\.com|google-analytics\.com|analytics\.google\.com"
    r"|clarity\.ms|/rpc/log_site_search"
)
CACHE_PREFIX = "ash_v6_"  # frontend/src/hooks/useCache.ts
# Lighthouse's "slow 4G" plus its 4x CPU slowdown for phones.
SLOW_NET = {"offline": False, "latency": 150,
            "downloadThroughput": 1.6e6 / 8, "uploadThroughput": 750e3 / 8}
SLOW_CPU = 4
PHONE_UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36")
SESSION_GAP_MS, SESSION_MAX_MS = 1000, 5000  # how CLS groups shifts into windows
SETTLE_S = {"fast": 4, "slow": 9}
# skim: most of a screen every 0.35 s (a fling, PageDown); read: 240 px every 0.45 s.
SCROLL = {"skim": (None, 0.35), "read": (240, 0.45)}
MAX_SCROLL_STEPS = 200
PHONES = [(360, 780), (390, 844), (412, 915)]
DESKTOPS = [(1280, 720), (1440, 900), (1920, 1080)]

# Records every layout shift from the start of the page, with the moved elements.
OBSERVER_JS = r"""
(() => {
  const shifts = (window.__shifts = []);
  const describe = (node) => {
    if (!node) return null;
    const el = node.nodeType === 1 ? node : node.parentElement;
    if (!el) return null;
    const cls = (el.getAttribute("class") || "").split(/\s+/).filter(Boolean).slice(0, 3).join(".");
    const sec = el.closest("[id]");
    const text = (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 50);
    return { tag: el.tagName.toLowerCase(), cls, section: sec ? sec.id : null, text };
  };
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      shifts.push({
        t: Math.round(e.startTime), value: e.value, input: e.hadRecentInput,
        scrollY: Math.round(window.scrollY),
        sources: (e.sources || []).map((s) => ({
          node: describe(s.node),
          dy: Math.round(s.currentRect.y - s.previousRect.y),
          dh: Math.round(s.currentRect.height - s.previousRect.height),
        })),
      });
    }
  }).observe({ type: "layout-shift", buffered: true });
})();
"""

# Layout-shift sources name what moved; this names what grew. Logs every home-page
# block whose height changes by 20 px or more, and where it sat on screen then.
RESIZE_JS = r"""
() => {
  const box = document.querySelector("main > div");
  if (!box) return 0;
  const log = (window.__resizes = []);
  const last = new Map();
  const label = (el, i) => `${i}:` + (el.id || el.querySelector("h2, h3")?.textContent.trim().slice(0, 40) || el.tagName.toLowerCase());
  const blocks = [...box.children];
  const ro = new ResizeObserver((entries) => {
    for (const e of entries) {
      const r = e.target.getBoundingClientRect();
      const prev = last.get(e.target);
      last.set(e.target, Math.round(r.height));
      if (prev === undefined || Math.abs(r.height - prev) < 20) continue;
      log.push({ t: Math.round(performance.now()), block: label(e.target, blocks.indexOf(e.target)),
                 from: prev, to: Math.round(r.height), top: Math.round(r.top), vh: innerHeight });
    }
  });
  blocks.forEach((c) => ro.observe(c));
  return blocks.length;
}
"""

# A returning visitor after a sync: cache marked stale, and the lists in it put in a
# different order, so the background refresh swaps what every slot shows (an upper
# bound on how much a sync changes them).
STALE_CACHE_JS = r"""
(prefix) => {
  let n = 0;
  for (const key of Object.keys(localStorage)) {
    if (!key.startsWith(prefix)) continue;
    const entry = JSON.parse(localStorage.getItem(key));
    entry.lastSyncAt = "1970-01-01T00:00:00Z";
    for (const v of Object.values(entry.data || {})) if (Array.isArray(v)) v.reverse();
    localStorage.setItem(key, JSON.stringify(entry));
    n++;
  }
  return n;
}
"""


def scenarios():
    runs = []
    for (w, h) in PHONES:
        for visitor in ("new", "returning"):
            runs.append(dict(name=f"phone{w}-{visitor}-slow", size=(w, h), phone=True,
                             net="slow", visitor=visitor, flow="scroll"))
    for (w, h) in DESKTOPS:
        for visitor in ("new", "returning"):
            runs.append(dict(name=f"desk{w}-{visitor}-fast", size=(w, h), phone=False,
                             net="fast", visitor=visitor, flow="scroll"))
    for sc in [r for r in runs if r["size"][0] in (390, 1440)]:
        runs.append({**sc, "name": sc["name"] + "-read", "speed": "read"})
    return runs + [
        dict(name="phone390-new-fast", size=(390, 844), phone=True, net="fast",
             visitor="new", flow="scroll"),
        dict(name="desk1440-new-slow", size=(1440, 900), phone=False, net="slow",
             visitor="new", flow="scroll"),
        dict(name="desk1440-new-fast-zh", size=(1440, 900), phone=False, net="fast",
             visitor="new", flow="scroll", locale="zh-CN"),
        dict(name="phone390-explore-slow", size=(390, 844), phone=True, net="slow",
             visitor="new", flow="explore"),
        dict(name="desk1440-explore-fast", size=(1440, 900), phone=False, net="fast",
             visitor="new", flow="explore"),
    ]


def new_context(browser, sc):
    w, h = sc["size"]
    opts = dict(viewport={"width": w, "height": h}, locale=sc.get("locale", "en-US"),
                device_scale_factor=2 if sc["phone"] else 1)
    if sc["phone"]:
        opts.update(is_mobile=True, has_touch=True, user_agent=PHONE_UA)
    context = browser.new_context(**opts)
    context.route(BLOCKED, lambda route: route.abort())
    context.add_init_script(OBSERVER_JS)
    return context


def throttle(context, page, net):
    if net != "slow":
        return
    cdp = context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", SLOW_NET)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": SLOW_CPU})


def load(page, url, net):
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    time.sleep(SETTLE_S[net])


def scroll_to_bottom(page, speed="skim"):
    step, pause = SCROLL[speed]
    step = step or int(page.viewport_size["height"] * 0.8)
    for _ in range(MAX_SCROLL_STEPS):
        at_bottom = page.evaluate(
            "() => scrollY + innerHeight >= document.documentElement.scrollHeight - 2")
        if at_bottom:
            break
        page.evaluate(f"() => window.scrollBy(0, {step})")
        time.sleep(pause)
    time.sleep(2)


def click_if_visible(page, selector, net):
    target = page.locator(selector).first
    if target.count() == 0 or not target.is_visible():
        return False
    target.click()
    time.sleep(SETTLE_S[net])
    return True


def explore(page, net):
    clicked = [click_if_visible(page, "main button:has-text('mcp-server')", net),
               click_if_visible(page, "main button:text-is('2')", net)]
    scroll_to_bottom(page)
    return clicked


def run_scenario(browser, sc, base):
    context = new_context(browser, sc)
    page = context.new_page()
    throttle(context, page, sc["net"])
    url = base + ("/?tab=explore" if sc["flow"] == "explore" else "/")
    if sc["visitor"] == "returning":
        load(page, url, sc["net"])
        page.evaluate(STALE_CACHE_JS, CACHE_PREFIX)
    load(page, url, sc["net"])
    page.evaluate(RESIZE_JS)
    speed = sc.get("speed", "skim")
    extra = explore(page, sc["net"]) if sc["flow"] == "explore" else scroll_to_bottom(page, speed)
    shifts = page.evaluate("() => window.__shifts")
    resizes = page.evaluate("() => window.__resizes || []")
    height = page.evaluate("() => document.documentElement.scrollHeight")
    context.close()
    return {**sc, "shifts": shifts, "resizes": resizes, "page_height": height, "clicked": extra}


def session_windows(shifts):
    windows, current = [], None
    for s in (x for x in shifts if not x["input"]):
        fresh = (current is None or s["t"] - current["last"] > SESSION_GAP_MS
                 or s["t"] - current["start"] > SESSION_MAX_MS)
        if fresh:
            current = {"start": s["t"], "last": s["t"], "value": 0.0, "entries": []}
            windows.append(current)
        current["last"] = s["t"]
        current["value"] += s["value"]
        current["entries"].append(s)
    return windows


def source_key(entry):
    node = (entry["sources"] or [{}])[0].get("node") or {}
    return f"#{node.get('section')} {node.get('tag')}.{node.get('cls')} \"{node.get('text', '')[:40]}\""


def top_sources(shifts, n=4):
    totals = {}
    for s in (x for x in shifts if not x["input"]):
        key = source_key(s)
        totals[key] = totals.get(key, 0.0) + s["value"]
    return sorted(totals.items(), key=lambda kv: -kv[1])[:n]


def grew_on_screen(resizes):
    """Blocks that grew while some of them was inside the viewport."""
    seen = {}
    for r in resizes:
        if r["to"] > r["from"] and r["top"] < r["vh"] and r["top"] + r["to"] > 0:
            seen[r["block"]] = seen.get(r["block"], 0) + (r["to"] - r["from"])
    return sorted(seen.items(), key=lambda kv: -kv[1])[:5]


HEIGHT_WIDTHS = [360, 390, 412, 640, 768, 900, 1024, 1280, 1440, 1920]
HEIGHTS_JS = r"""
() => {
  const blocks = [...document.querySelector("main > div").children];
  return blocks.map((el, i) => {
    const box = el.getBoundingClientRect();
    const end = blocks[i + 1] ? blocks[i + 1].getBoundingClientRect().top : box.bottom;
    return [i, el.id || el.querySelector("h2, h3")?.textContent.trim().slice(0, 24) ||
      el.tagName.toLowerCase(), Math.round(end - box.top)];
  });
}
"""


def measure_heights(browser, base):
    """Final space every home block takes once all of them have rendered, per width:
    its height plus the margin below it, which arrives with the content, so a
    placeholder has to hold it too. These set the space the lazy blocks hold."""
    table = {}
    for w in HEIGHT_WIDTHS:
        sc = dict(name=f"h{w}", size=(w, 900), phone=w < 768, net="fast")
        context = new_context(browser, sc)
        page = context.new_page()
        load(page, base + "/", "fast")
        scroll_to_bottom(page, "read")
        for i, label, h in page.evaluate(HEIGHTS_JS):
            table.setdefault((i, label), {})[w] = h
        context.close()
    print(f"{'block':<32}" + "".join(f"{w:>6}" for w in HEIGHT_WIDTHS))
    for (i, label), row in sorted(table.items()):
        print(f"{i:>2} {label[:28]:<29}" + "".join(f"{row.get(w, ''):>6}" for w in HEIGHT_WIDTHS))


def summarize(result):
    windows = session_windows(result["shifts"])
    worst = max(windows, key=lambda w: w["value"], default=None)
    before_scroll = [s for s in result["shifts"] if s["scrollY"] == 0]
    return {
        "name": result["name"],
        "cls": round(worst["value"], 4) if worst else 0.0,
        "cls_before_scroll": round(max((w["value"] for w in session_windows(before_scroll)), default=0.0), 4),
        "entries": len(result["shifts"]),
        "top_moved": [(k, round(v, 4)) for k, v in top_sources(result["shifts"])],
        "grew_on_screen_px": grew_on_screen(result.get("resizes", [])),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", help="run only scenarios whose name contains this")
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--heights", action="store_true",
                    help="print each block's rendered height per width instead")
    args = ap.parse_args()
    if args.heights:
        with sync_playwright() as p:
            measure_heights(p.chromium.launch(), args.base)
        return
    runs = [s for s in scenarios() if not args.only or args.only in s["name"]]
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for sc in runs:
            result = run_scenario(browser, sc, args.base)
            results.append(result)
            print(json.dumps(summarize(result), ensure_ascii=False), flush=True)
        browser.close()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"home-cls-{stamp}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1))
    print(f"saved {out}")


if __name__ == "__main__":
    main()

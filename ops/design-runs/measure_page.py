"""Measure one built landing page in a headless browser. Runs inside the sandbox image:

  docker run --rm --entrypoint python3 -v <run dir>:/run -v <this dir>:/tool:ro pptrun:1 /tool/measure_page.py /run

Reads /run/deliverables/index.html (the page we had built; its web fonts load). Writes desktop.png (1440 wide, full page), fold.png (the first
screen), mobile.png (375 wide) and measure.json: the text on the page, the fonts and
colours it uses weighted by area, and counts of the stock choices score_design.py checks.
"""
import json
import sys
from pathlib import Path

RUN = Path(sys.argv[1])
PAGE = RUN / "deliverables" / "index.html"
SETTLE_MS = 1500

PROBE = r"""
() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && Number(s.opacity) > 0; };
  // Any CSS colour (oklch, color-mix, named) as "rgb(r, g, b)", by painting one pixel.
  const cv = document.createElement('canvas'); cv.width = cv.height = 1; const cx = cv.getContext('2d', { willReadFrequently: true });
  const rgb = (c) => { cx.clearRect(0, 0, 1, 1); cx.fillStyle = '#000'; cx.fillStyle = c; cx.fillRect(0, 0, 1, 1);
    const [r, g, b, al] = cx.getImageData(0, 0, 1, 1).data; return al < 8 ? 'rgba(0, 0, 0, 0)' : `rgb(${r}, ${g}, ${b})`; };
  const all = [...document.querySelectorAll('body *')].filter(vis);
  const fonts = {}, textColors = {}, bgColors = {};
  let gradientEls = 0, gradientText = 0, blurEls = 0, shadowEls = 0, roundCards = 0, purpleGradient = 0;
  const hue = (rgb) => { const m = rgb.match(/\d+(\.\d+)?/g); if (!m) return null; const [r, g, b] = m.map(Number).map(v => v / 255);
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn; if (d < 0.08) return null;
    let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; return (h * 60 + 360) % 360; };
  for (const el of all) {
    const s = getComputedStyle(el), r = el.getBoundingClientRect(), area = r.width * r.height;
    const own = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()).join(' ');
    if (own) { const f = s.fontFamily.split(',')[0].replace(/["']/g, '').trim(); fonts[f] = (fonts[f] || 0) + own.length;
      textColors[s.color] = (textColors[s.color] || 0) + own.length; }
    if (s.backgroundColor !== 'rgba(0, 0, 0, 0)') bgColors[s.backgroundColor] = (bgColors[s.backgroundColor] || 0) + area;
    const bg = s.backgroundImage;
    if (bg.includes('gradient')) { gradientEls++;
      const hs = (bg.match(/(?:rgba?|oklch|oklab|hsla?|lab|lch|color)\([^()]*(?:\([^()]*\)[^()]*)*\)|#[0-9a-f]{3,8}\b/gi) || []).map(rgb).map(hue).filter(h => h !== null);
      if (hs.some(h => h >= 235 && h <= 320)) purpleGradient++;
      if ((s.webkitBackgroundClip || s.backgroundClip) === 'text') gradientText++; }
    if ((s.backdropFilter || s.webkitBackdropFilter || 'none') !== 'none') blurEls++;
    if (s.boxShadow !== 'none' && area > 20000) shadowEls++;
    if (parseFloat(s.borderTopLeftRadius) >= 12 && area > 20000 && area < 600000) roundCards++;
  }
  const text = document.body.innerText;
  const emoji = (text.match(/\p{Extended_Pictographic}/gu) || []).length;
  const hero = document.querySelector('h1');
  const heroAlign = hero ? getComputedStyle(hero).textAlign : null;
  const heroBox = hero ? hero.getBoundingClientRect() : null;
  const heroCentered = hero ? (heroAlign === 'center' || Math.abs((heroBox.left + heroBox.right) / 2 - innerWidth / 2) < 40 && heroBox.width < innerWidth * 0.8) : false;
  const buttons = [...document.querySelectorAll('a,button')].filter(vis).map(b => ({ text: b.innerText.trim(), top: b.getBoundingClientRect().top + scrollY }));
  // The accent is the fill of the primary button: the first "Check my beach" that has one (a nav copy is often an outline).
  const accent = (() => { const bs = [...document.querySelectorAll('a,button')].filter(vis).filter(x => /check my beach/i.test(x.innerText));
    const filled = bs.map(b => rgb(getComputedStyle(b).backgroundColor)).find(c => c !== 'rgba(0, 0, 0, 0)');
    return filled || (bs[0] ? rgb(getComputedStyle(bs[0]).color) : null); })();
  const pageBg = (() => { for (const el of [document.body, document.documentElement, document.querySelector('main'), document.querySelector('header'), document.querySelector('section')]) {
    if (!el) continue; const c = rgb(getComputedStyle(el).backgroundColor); if (c !== 'rgba(0, 0, 0, 0)') return c; } return 'rgb(255, 255, 255)'; })();
  const h1Font = hero ? getComputedStyle(hero).fontFamily.split(',')[0].replace(/["']/g, '').trim() : null;
  return { text, fonts, textColors, bgColors, gradientEls, gradientText, purpleGradient, blurEls, shadowEls, roundCards, emoji,
    h1: document.querySelectorAll('h1').length, heroCentered, buttons, accent, bodyBg: pageBg, h1Font,
    svg: document.querySelectorAll('svg').length, img: document.querySelectorAll('img').length,
    scrollWidth: document.documentElement.scrollWidth, innerWidth, height: document.documentElement.scrollHeight,
    sections: [...document.querySelectorAll('body > *, main > *')].filter(vis).map(e => e.tagName.toLowerCase()) };
}
"""


def main() -> None:
    from playwright.sync_api import sync_playwright
    out = {"errors": [], "requests": []}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: out["errors"].append(str(e)[:200]))
        page.on("request", lambda r: out["requests"].append(r.url[:160]) if r.url.startswith("http") else None)
        page.goto(f"file://{PAGE}", wait_until="load")
        page.wait_for_timeout(SETTLE_MS)
        page.screenshot(path=str(RUN / "fold.png"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(600)   # trigger scroll reveals
        page.evaluate("window.scrollTo(0, 0)"); page.wait_for_timeout(300)
        page.screenshot(path=str(RUN / "desktop.png"), full_page=True)
        out["desktop"] = page.evaluate(PROBE)
        page.set_viewport_size({"width": 375, "height": 812}); page.wait_for_timeout(600)
        page.screenshot(path=str(RUN / "mobile.png"), full_page=True)
        m = page.evaluate(PROBE)
        out["mobile"] = {"scrollWidth": m["scrollWidth"], "innerWidth": m["innerWidth"]}
        b.close()
    (RUN / "measure.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

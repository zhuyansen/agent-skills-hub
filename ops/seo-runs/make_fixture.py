"""Build the SEO test's fixture: a small tea shop site with 16 planted SEO defects.

  python ops/seo-runs/make_fixture.py

Writes in/site/ (the pages, robots.txt, sitemap.xml, images) and truth.json (the planted
defects, and the facts a report can get wrong). The sandbox serves the site at http://lumentea.test/
with in/server.py (sandbox/start_seo.sh), which adds what static files cannot do: the 301 chain
/shop/ -> /store/ -> /teas/ and an X-Robots-Tag: noindex header on /teas/bai-mudan/ (the HTML is clean). Everything not planted is meant to be correct: unique
titles and descriptions, one H1, a self canonical, lang, viewport, alt text, valid JSON-LD, links
that answer 200. So a report that calls one of those broken is wrong, and we can check it.
"""
import json
import struct
import zlib
from pathlib import Path

HERE = Path(__file__).parent
SITE = HERE / "in/site"
HOST = "http://lumentea.test"
IMG = {"hero": ((176, 196, 160), 1200, 630), "jasmine": ((226, 222, 196), 800, 800),
       "peony": ((214, 200, 170), 800, 800), "brew": ((150, 170, 120), 1200, 800),
       "team": ((190, 170, 150), 1200, 800), "icon": ((60, 90, 60), 64, 64)}

TRUTH = [
    {"id": "D1", "where": "/robots.txt", "defect": "robots.txt has `Disallow: /blog/`, so crawlers may not fetch the whole blog, although the blog pages are in the sitemap and linked from every page."},
    {"id": "D2", "where": "/teas/jasmine-silver-needle/", "defect": "The best-selling product page has <meta name=\"robots\" content=\"noindex, follow\">, so it is kept out of search results although it is in the sitemap and linked from the home page."},
    {"id": "D3", "where": "/teas/", "defect": "The tea category page's canonical points to the home page (http://lumentea.test/) instead of itself."},
    {"id": "D4", "where": "/blog/how-to-brew-green-tea/", "defect": "The blog article has no <title> element at all."},
    {"id": "D5", "where": "/teas/ and /blog/", "defect": "/teas/ and /blog/ have the same meta description (duplicate descriptions)."},
    {"id": "D6", "where": "/blog/how-to-brew-green-tea/", "defect": "The article links to /teas/dragon-well/, which answers 404 (broken internal link)."},
    {"id": "D7", "where": "/sitemap.xml", "defect": "The sitemap lists /teas/white-peony/, which answers 404."},
    {"id": "D8", "where": "/teas/jasmine-silver-needle/", "defect": "The product page's Product JSON-LD is not valid JSON (a trailing comma), so the structured data cannot be parsed."},
    {"id": "D9", "where": "/teas/jasmine-silver-needle/", "defect": "The product page's main product image has no alt attribute."},
    {"id": "D10", "where": "/contact/", "defect": "The contact page has no H1 heading."},
    {"id": "D11", "where": "site navigation", "defect": "The 'Shop' link in the navigation on every page goes to /shop/, which redirects 301 to /store/, which redirects 301 to /teas/ (a redirect chain on an internal link)."},
    {"id": "D12", "where": "/blog/", "defect": "The blog index page has no <meta name=\"viewport\"> tag (not mobile friendly)."},
    # Harder ones, added after the first control run found all twelve above in 90 seconds.
    {"id": "D13", "where": "/teas/bai-mudan/", "defect": "The Bai Mudan product page is sent with an HTTP header X-Robots-Tag: noindex, so it is kept out of search results; its HTML has no robots meta, so only the response header shows it."},
    {"id": "D14", "where": "/guides/storing-tea/", "defect": "/guides/storing-tea/ is an orphan page: it is in the sitemap and answers 200, but no page on the site links to it."},
    {"id": "D15", "where": "/ (home)", "defect": "The home page declares <link rel=\"alternate\" hreflang=\"zh-CN\" href=\"http://lumentea.test/zh/\">, and /zh/ answers 404 (a broken hreflang alternate; there is also no x-default or self reference)."},
    {"id": "D16", "where": "/ and /guides/storing-tea/", "defect": "/guides/storing-tea/ has the same <title> as the home page (duplicate titles)."},
]
# Facts that hold on the site, for marking a report's claim as false. A claim of a defect that one of
# these contradicts (e.g. "the home page has no canonical") counts as a false claim.
FACTS = [
    "Every page except the blog article has a <title> of 35-60 characters; titles are unique except / and /guides/storing-tea/.",
    "Every page has a meta description of 120-160 characters; only /teas/ and /blog/ share one.",
    "Every page except /teas/ has a canonical pointing to its own URL. Only the home page has hreflang (zh-CN -> /zh/, a 404).",
    "Every page except /contact/ has exactly one H1.",
    "Every page has <html lang=\"en\">, a UTF-8 charset, Open Graph tags (og:title, og:description, og:url, og:image) and twitter:card.",
    "Every page except /blog/ has a viewport meta tag.",
    "Every image has an alt attribute and width/height except the jasmine product image (no alt).",
    "Home has valid Organization + WebSite JSON-LD; /teas/bai-mudan/ has valid Product JSON-LD; the article has valid BlogPosting JSON-LD; /about/ has valid AboutPage JSON-LD.",
    "Internal links all answer 200 except /teas/dragon-well/ (404) and /shop/ (301 chain). /guides/storing-tea/ is linked from nowhere.",
    "robots.txt allows everything except /blog/ and names the sitemap. The sitemap lists the 9 real pages plus /teas/white-peony/ (404).",
    "No page has a noindex except /teas/jasmine-silver-needle/ (meta robots) and /teas/bai-mudan/ (X-Robots-Tag header only).",
    "The site is served over plain HTTP inside the sandbox (no certificate); the prompt says to ignore HTTPS.",
]

NAV = """<header><nav><a href="/">Lumen Tea</a> · <a href="/shop/">Shop</a> · <a href="/blog/">Journal</a> · <a href="/about/">About</a> · <a href="/contact/">Contact</a></nav></header>"""
FOOT = """<footer><p>Lumen Tea Co., 18 Harbour Lane, Bristol BS1 4RW, United Kingdom · <a href="/about/">About us</a> · <a href="/contact/">Contact</a> · <a href="/teas/">All teas</a></p><p>© 2026 Lumen Tea Co.</p></footer>"""
DESC_SHARED = "Browse every loose leaf tea we sell: white and jasmine teas from three family farms in Fujian, packed in small batches each month."


def png(rgb: tuple, w: int, h: int) -> bytes:
    row = b"\x00" + bytes(rgb) * w
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)   # noqa: E731
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * h, 9)) + chunk(b"IEND", b""))


def img(name: str, alt: str | None) -> str:
    _, w, h = IMG[name]
    a = f' alt="{alt}"' if alt is not None else ""
    return f'<img src="/img/{name}.png"{a} width="{w}" height="{h}">'


def page(path: str, title: str | None, desc: str, h1: str | None, body: str, *, canonical: str | None = None,
         robots: str | None = None, viewport: bool = True, ld: str = "", image: str = "hero", og_type: str = "website",
         extra_head: str = "") -> str:
    url = HOST + path
    head = ['<meta charset="utf-8">']
    if viewport:
        head.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    if title is not None:
        head.append(f"<title>{title}</title>")
    head.append(f'<meta name="description" content="{desc}">')
    if robots:
        head.append(f'<meta name="robots" content="{robots}">')
    head.append(f'<link rel="canonical" href="{canonical or url}">')
    og_title = title or h1 or "Lumen Tea"
    head += [f'<meta property="og:title" content="{og_title}">', f'<meta property="og:description" content="{desc}">',
             f'<meta property="og:url" content="{url}">', f'<meta property="og:image" content="{HOST}/img/{image}.png">',
             f'<meta property="og:type" content="{og_type}">', '<meta name="twitter:card" content="summary_large_image">',
             '<link rel="icon" href="/img/icon.png" type="image/png">']
    if extra_head:
        head.append(extra_head)
    if ld:
        head.append(f'<script type="application/ld+json">{ld}</script>')
    h1_html = f"<h1>{h1}</h1>\n" if h1 else ""
    return (f'<!doctype html>\n<html lang="en">\n<head>\n' + "\n".join(head) + f"\n</head>\n<body>\n{NAV}\n<main>\n{h1_html}"
            f"{body}\n</main>\n{FOOT}\n</body>\n</html>\n")


def ld(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False)


PRODUCT_BAD_LD = """{"@context": "https://schema.org", "@type": "Product", "name": "Jasmine Silver Needle", "image": "http://lumentea.test/img/jasmine.png",
 "description": "White tea buds scented seven times with fresh jasmine flowers.", "sku": "LT-JSN-50",
 "offers": {"@type": "Offer", "price": "18.00", "priceCurrency": "GBP", "availability": "https://schema.org/InStock",},
}"""


def pages() -> dict[str, str]:
    p = {}
    p["/"] = page("/", "Lumen Tea | Small-Batch Loose Leaf Tea from Fujian",
                  "Loose leaf white and jasmine teas from three family farms in Fujian, packed by hand in small batches in Bristol and shipped across the UK.",
                  "Small-batch loose leaf tea from Fujian",
                  f"""{img("hero", "Tea fields on a hillside in Fuding, Fujian, in early spring")}
<p>Lumen Tea buys from three family farms in Fuding and Fu'an, in the north of Fujian province, where white tea was first made. We visit every spring, taste each lot before we buy it, and pack it ourselves in Bristol in batches small enough to sell within a few months. The leaf you get was picked this year.</p>
<h2>Our teas</h2>
<p>We sell two teas for now, both white, and no blends. Our best seller is <a href="/teas/jasmine-silver-needle/">Jasmine Silver Needle</a>: downy white tea buds scented seven times with fresh jasmine flowers, sweet and clean rather than perfumed. <a href="/teas/bai-mudan/">Bai Mudan</a>, or White Peony, is a bud and two leaves, fuller and more forgiving to brew. You will find every tea, with tasting notes and brewing times, on <a href="/teas/">the tea page</a>.</p>
<h2>How we brew it</h2>
<p>Green and white teas burn in boiling water. Most of the bitterness people blame on green tea comes from water that is too hot or leaf left in too long. Our guide <a href="/blog/how-to-brew-green-tea/">How to brew green tea</a> gives temperatures, amounts and times for a mug, a teapot and a gaiwan, and what to change when a cup comes out bitter or thin.</p>
<h2>Shipping</h2>
<p>Orders placed before 2 pm ship the same working day from Bristol by Royal Mail. Delivery is free in the UK above £30. Every tea comes in a resealable foil pouch of 50 or 100 grams with the harvest date printed on the back.</p>""",
                  ld=ld([{"@context": "https://schema.org", "@type": "Organization", "name": "Lumen Tea Co.", "url": HOST + "/",
                          "logo": HOST + "/img/icon.png", "address": {"@type": "PostalAddress", "streetAddress": "18 Harbour Lane",
                                                                       "addressLocality": "Bristol", "postalCode": "BS1 4RW", "addressCountry": "GB"}},
                         {"@context": "https://schema.org", "@type": "WebSite", "name": "Lumen Tea", "url": HOST + "/"}]),
                  extra_head=f'<link rel="alternate" hreflang="zh-CN" href="{HOST}/zh/">')
    p["/about/"] = page("/about/", "About Lumen Tea | Who We Are and Where We Buy",
                        "Lumen Tea is two people in Bristol who buy white tea directly from three family farms in Fujian and pack it in small batches.",
                        "About Lumen Tea",
                        f"""{img("team", "Mei and Tom Harding tasting tea samples at a farm in Fu'an")}
<p>Lumen Tea is Mei and Tom Harding. Mei grew up in Fuzhou and spent ten years buying tea for a London importer; Tom ran a coffee roastery in Bristol. We started Lumen Tea in 2021 because the white tea we could buy in the UK was usually two or three years old by the time it reached a cup.</p>
<h2>Where our tea comes from</h2>
<p>We buy from three farms: the Lin family in Diantou, the Chen family near Fu'an and a cooperative of eleven growers in Panxi. None of them sells through a wholesaler. We pay before harvest, which lets them pick by hand and skip the machine-cut autumn crop. Each lot is tasted in Fujian and again in Bristol, and we turn down about one in three.</p>
<h2>What we do not do</h2>
<p>We do not add flavourings, sell blends or use tea bags. The only scented tea we sell is jasmine, and it is scented with real flowers over several nights, the traditional way. If a tea does not sell within six months of harvest, we give it to staff and friends instead of discounting it.</p>
<p>Questions about a tea or an order? <a href="/contact/">Write to us</a>; one of us answers every message within a working day.</p>""",
                        ld=ld({"@context": "https://schema.org", "@type": "AboutPage", "name": "About Lumen Tea", "url": HOST + "/about/"}))
    p["/teas/"] = page("/teas/", "All Teas | White, Green and Jasmine Tea | Lumen Tea", DESC_SHARED, "All our teas",
                       """<p>Every tea we sell comes from one of three family farms in northern Fujian and is packed in Bristol within weeks of arriving. We list the harvest date on each pouch. Prices are for 50 grams, about 25 cups.</p>
<h2>White tea</h2>
<ul><li><a href="/teas/jasmine-silver-needle/">Jasmine Silver Needle</a>: silver buds scented seven times with jasmine. £18.</li>
<li><a href="/teas/bai-mudan/">Bai Mudan (White Peony)</a>: a bud and two leaves, honeyed and full. £12.</li></ul>
<h2>Choosing a tea</h2>
<p>If you are new to white tea, start with Bai Mudan: it is hard to over-brew and tastes of hay, honey and dried apricot. Jasmine Silver Needle is lighter and sweeter, with the jasmine in the aroma more than the taste. Both can be brewed three or four times from the same leaf.</p>
<p>Not sure how much water or how hot? Read <a href="/blog/how-to-brew-green-tea/">our brewing guide</a>; the same temperatures work for white tea.</p>""",
                       canonical=HOST + "/")
    p["/teas/jasmine-silver-needle/"] = page(
        "/teas/jasmine-silver-needle/", "Jasmine Silver Needle White Tea, 50 g | Lumen Tea",
        "Jasmine Silver Needle: downy white tea buds from Fuding scented seven times with fresh jasmine flowers. Sweet, clean and floral. 50 g pouch, £18.",
        "Jasmine Silver Needle", f"""{img("jasmine", None)}
<p><strong>£18.00 for 50 g</strong> · In stock · Harvest: April 2026</p>
<p>Silver Needle is the first spring bud of the Fuding Da Bai tea bush, picked before the leaf opens. We buy ours from the Lin family in Diantou. In June the buds are layered with jasmine flowers picked the same afternoon; the flowers open overnight and the tea takes up their scent. The flowers are sifted out in the morning and the process is repeated with fresh flowers seven times.</p>
<h2>Tasting notes</h2>
<p>Sweet and clean, with jasmine in the aroma and a long, soft finish. There is no bitterness unless the water is too hot. The second and third infusions are often the best.</p>
<h2>How to brew</h2>
<p>Use 3 grams of leaf for 250 ml of water at 80 °C and steep for 3 minutes. In a gaiwan, use 5 grams for 100 ml and pour off after 40 seconds, adding 15 seconds for each infusion after that.</p>
<p>Compare it with our <a href="/teas/bai-mudan/">Bai Mudan</a>, or see <a href="/teas/">all our teas</a>.</p>""",
        robots="noindex, follow", ld=PRODUCT_BAD_LD, image="jasmine", og_type="product")
    p["/teas/bai-mudan/"] = page(
        "/teas/bai-mudan/", "Bai Mudan (White Peony) White Tea, 50 g | Lumen Tea",
        "Bai Mudan, or White Peony: a bud and two leaves from the Chen family farm near Fu'an. Honeyed, full and hard to over-brew. 50 g pouch, £12.",
        "Bai Mudan (White Peony)", f"""{img("peony", "Loose Bai Mudan white tea leaves and buds on a ceramic dish")}
<p><strong>£12.00 for 50 g</strong> · In stock · Harvest: April 2026</p>
<p>Bai Mudan is made from a bud and the two leaves below it, withered in the sun and shade and then dried at a low heat. Nothing else is done to it. Ours comes from the Chen family near Fu'an, who pick by hand on the first warm days of April.</p>
<h2>Tasting notes</h2>
<p>Hay, wildflower honey and dried apricot, with more body than Silver Needle. It stays sweet even when brewed a little too long, which makes it a good first white tea.</p>
<h2>How to brew</h2>
<p>Use 3 grams for 250 ml of water at 85 °C and steep for 3 to 4 minutes. The leaf gives three good infusions; add a minute each time.</p>
<p>Compare it with our <a href="/teas/jasmine-silver-needle/">Jasmine Silver Needle</a>, or see <a href="/teas/">all our teas</a>.</p>""",
        ld=ld({"@context": "https://schema.org", "@type": "Product", "name": "Bai Mudan (White Peony)", "image": HOST + "/img/peony.png",
               "description": "A bud and two leaves from the Chen family farm near Fu'an.", "sku": "LT-BMD-50",
               "offers": {"@type": "Offer", "price": "12.00", "priceCurrency": "GBP", "availability": "https://schema.org/InStock"}}),
        image="peony", og_type="product")
    p["/blog/"] = page("/blog/", "The Lumen Tea Journal | Brewing Guides and Farm Notes", DESC_SHARED, "The Lumen Tea Journal",
                       """<p>Notes from the farms we buy from, and plain answers to the questions we get most often about brewing white and green tea at home.</p>
<article><h2><a href="/blog/how-to-brew-green-tea/">How to brew green tea without the bitterness</a></h2>
<p>Water temperature, how much leaf, how long to steep, and what to change when a cup comes out bitter or thin. Temperatures and times for a mug, a teapot and a gaiwan.</p>
<p>Published 12 September 2026 · 6 minute read</p></article>
<p>We publish a new guide or farm note about once a month. The next one covers this year's jasmine scenting in Diantou.</p>""",
                       viewport=False)
    p["/blog/how-to-brew-green-tea/"] = page(
        "/blog/how-to-brew-green-tea/", None,
        "How to brew green tea without bitterness: the right water temperature, how much leaf, steeping times for a mug, teapot and gaiwan, and fixes for a bad cup.",
        "How to brew green tea without the bitterness", f"""<p>Published 12 September 2026 by Mei Harding</p>
{img("brew", "Green tea leaves unfurling in a glass teapot")}
<p>Most bitter green tea is brewed with water that is too hot or left on the leaf too long. Green tea is not roasted or oxidised the way black tea is, so boiling water pulls out tannins and caffeine fast and cooks the delicate flavours. Get the temperature and the time right and nearly any decent green tea tastes sweet.</p>
<h2>Water temperature</h2>
<p>Brew most green teas at 75 to 80 °C. Without a thermometer kettle, boil the water and let it stand with the lid open for about four minutes, or add one part cold water to four parts boiling. Delicate Chinese greens such as Dragon Well, which we hope to stock next spring (<a href="/teas/dragon-well/">see Dragon Well</a>), like the lower end of that range.</p>
<h2>How much leaf and how long</h2>
<p>For a 250 ml mug, use 2 to 3 grams of leaf, about a heaped teaspoon, and steep for 2 minutes. For a teapot, scale up: 5 grams for 500 ml. In a gaiwan, use 4 grams for 100 ml and pour off after 30 seconds, adding 10 seconds for each infusion after that.</p>
<h2>When the cup is wrong</h2>
<ul><li>Bitter: the water was too hot or the tea steeped too long. Cool the water or shorten the time, not both at once.</li>
<li>Thin or flat: too little leaf. Add more leaf before you lengthen the time.</li>
<li>Grassy and sharp: common with Japanese greens; try 70 °C.</li></ul>
<p>The same temperatures work for white tea. Try them with our <a href="/teas/bai-mudan/">Bai Mudan</a>, the most forgiving tea we sell.</p>""",
        ld=ld({"@context": "https://schema.org", "@type": "BlogPosting", "headline": "How to brew green tea without the bitterness",
               "datePublished": "2026-09-12", "author": {"@type": "Person", "name": "Mei Harding"},
               "image": HOST + "/img/brew.png", "url": HOST + "/blog/how-to-brew-green-tea/"}),
        image="brew", og_type="article")
    p["/contact/"] = page("/contact/", "Contact Lumen Tea | Orders, Wholesale and Questions",
                          "Contact Lumen Tea about an order, wholesale prices for cafés and shops, or a question about brewing. We answer every message within a working day.",
                          None, """<h2>Get in touch</h2>
<p>Email <a href="mailto:hello@lumentea.test">hello@lumentea.test</a> or call 0117 496 0123, Monday to Friday, 9 am to 5 pm. One of us answers every message within a working day.</p>
<h2>Orders and returns</h2>
<p>If a pouch arrives damaged or a tea is not what you expected, write within 30 days and we will refund or replace it. You do not need to send the tea back.</p>
<h2>Wholesale</h2>
<p>We supply cafés, restaurants and independent shops in 500 gram and 1 kilogram bags. Ask for our wholesale price list and we will post you samples of every tea.</p>
<h2>Visit</h2>
<p>Our packing room at 18 Harbour Lane, Bristol BS1 4RW, is open for collection on Saturdays from 10 am to 1 pm.</p>""")
    p["/guides/storing-tea/"] = page(
        "/guides/storing-tea/", "Lumen Tea | Small-Batch Loose Leaf Tea from Fujian",
        "How to store loose leaf white and green tea at home: airtight, dark and cool, away from strong smells, and how long each kind keeps its flavour.",
        "How to store loose leaf tea", """<p>Tea takes up moisture and smells from the air around it, and light and heat fade its flavour. Stored well, white tea keeps for years and even improves; green tea is best within six months of harvest.</p>
<h2>The four rules</h2>
<ul><li>Airtight: keep the leaf in its resealable pouch, pressed flat, or in a tin with a tight lid.</li>
<li>Dark: a cupboard, not a glass jar on the counter.</li>
<li>Cool and dry: away from the kettle, the oven and the dishwasher. Do not keep tea in the fridge; it picks up damp when you take it out.</li>
<li>Away from smells: not next to spices, coffee or soap.</li></ul>
<h2>How long it keeps</h2>
<p>Green tea is at its best for six months and drinkable for a year. White tea such as Bai Mudan changes slowly over several years, getting deeper and sweeter, which is why aged white tea is prized in Fujian. Jasmine tea keeps its scent for about a year; after that the jasmine fades before the tea does.</p>
<p>Every pouch we sell has the harvest date printed on the back, so you can tell how old your tea is.</p>""")
    return p


ROBOTS = f"User-agent: *\nDisallow: /blog/\n\nSitemap: {HOST}/sitemap.xml\n"


def sitemap() -> str:
    urls = ["/", "/about/", "/teas/", "/teas/jasmine-silver-needle/", "/teas/bai-mudan/", "/teas/white-peony/",
            "/blog/", "/blog/how-to-brew-green-tea/", "/contact/", "/guides/storing-tea/"]
    rows = "".join(f"<url><loc>{HOST}{u}</loc><lastmod>2026-10-01</lastmod></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}</urlset>\n'


def main() -> None:
    for path, html in pages().items():
        f = SITE / path.strip("/") / "index.html" if path != "/" else SITE / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html)
    (SITE / "img").mkdir(exist_ok=True)
    for name, (rgb, w, h) in IMG.items():
        (SITE / "img" / f"{name}.png").write_bytes(png(rgb, w, h))
    (SITE / "robots.txt").write_text(ROBOTS)
    (SITE / "sitemap.xml").write_text(sitemap())
    (SITE / "404.html").write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Not found | Lumen Tea</title>'
                                   '<meta name="robots" content="noindex"></head><body><h1>Page not found</h1><p><a href="/">Lumen Tea home</a></p></body></html>\n')
    (HERE / "truth.json").write_text(json.dumps({"host": HOST, "defects": TRUTH, "facts": FACTS}, indent=1) + "\n")
    print(f"{len(pages())} pages, {len(TRUTH)} planted defects -> {SITE}")


if __name__ == "__main__":
    main()

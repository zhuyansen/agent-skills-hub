# SEO tools test, 2026-11-11

One 9-page test shop (http://lumentea.test/, served in the sandbox) with 16 planted SEO problems; see make_fixture.py, truth.json and score_seo.py.

| Tool | Kind | ★ | Found | False claims | Problems raised | Min | Missed |
|---|---|---:|---:|---:|---:|---:|---|
| Control: Claude Code, no tool | control | - | 16/16 | 0 | 26 | 2 | - |
| aaron-he-zhu/aaron-marketing-skills | marketing | 3123 | 16/16 | 0 | 33 | 5 | - |
| Bhanunamikaze/Agentic-SEO-Skill | suite | 1046 | 16/16 | 2 | 44 | 18 | - |
| coreyhaines31/marketingskills | marketing | 59621 | 15/16 | 0 | 25 | 1 | D13 |
| squirrelscan/squirrelscan | audit | 311 | 15/16 | 0 | 33 | 2 | D15 |
| tigerless-labs/seo-ops | audit | 986 | 13/16 | 2 | 24 | 2 | D1, D11, D14 |
| iannuttall/seo | data_mcp | 616 | 12/16 | 0 | 16 | 1 | D4, D5, D6, D12 |
| zubair-trabzada/geo-seo-claude | geo | 11602 | 12/16 | 2 | 48 | 5 | D4, D5, D6, D12 |
| AgriciDaniel/claude-seo | suite | 27956 | 12/16 | 3 | 44 | 6 | D4, D5, D6, D12 |
| Auriti-Labs/geo-optimizer-skill | geo | 1278 | 9/16 | 3 | 37 | 6 | D1, D5, D6, D11, D14, D15, D16 |
| seo-skills/seo-audit-skill | audit | 667 | 9/16 | 6 | 64 | 1 | D1, D4, D6, D7, D14, D15, D16 |
| addyosmani/agentic-seo | geo | 333 | 0/16 | 0 | 5 | 1 | D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14, D15, D16 |

No audit:

- JeffLi1993/seo-audit-skill: It refuses private addresses, so it ran on the public copy, where its site audit stopped: it requires a Google PageSpeed Insights API key, which we did not give it.
- every-app/open-seo: Its audit runs on OpenSEO's servers and needs an OpenSEO account sign-in, so it cannot audit a site that is not on the public internet.

Notes:

- Bhanunamikaze/Agentic-SEO-Skill: It refuses private addresses, so it ran on 2026-11-12 on a public copy of the same site; Claude Code with no tool found all 16 there too. It took the /shop/ redirect for a duplicate of /teas/ and counted no product links on /teas/, which has two.
- Auriti-Labs/geo-optimizer-skill: It refuses private addresses, so it ran on 2026-11-12 on a public copy of the same site; Claude Code with no tool found all 16 there too. A GEO scorer page by page: it missed the robots.txt block and the redirect chain, reported 0 broken links on the article that has one, and said the contact page has no contact details.
- aaron-he-zhu/aaron-marketing-skills: A 120-skill marketing plugin; its site-audit route ran. Its fetch scripts refuse private addresses unless their built-in allow-private option is on, which the run turned on.
- squirrelscan/squirrelscan: A crawler CLI with 310+ rules, run in its offline mode: its cloud service cannot reach a private site.
- coreyhaines31/marketingskills: Its seo-audit skill is a written checklist: Claude Code followed it with curl. It missed the noindex sent in an HTTP header.
- AgriciDaniel/claude-seo: It obeys robots.txt, so it did not read the two blog pages the test blocks and missed the four problems on them; it did report the block. Its summary then said every page has a viewport tag and that titles and descriptions are unique, which the blog pages contradict. Ten specialist agents, a score of 61/100.
- zubair-trabzada/geo-seo-claude: It obeys robots.txt, so it did not read the two blog pages the test blocks and missed the four problems on them; it did report the block. It also said the guides have no author, byline or Article schema; the blog post has all three, but it had not read it.
- iannuttall/seo: It obeys robots.txt, so it did not read the two blog pages the test blocks and missed the four problems on them; it did report the block. Its MCP crawl failed with a parameter error (Unrecognized key: "saveReport"), so the run used its CLI, which needed no account.
- tigerless-labs/seo-ops: 30 fixed checks. It passed "robots.txt allows AI crawlers" and "redirect hops ≤1" although the blog is blocked for every crawler and the main menu link takes two hops.
- seo-skills/seo-audit-skill: SEOmator's CLI. It took the /shop/ redirect for a second page and reported a duplicate title, H1 and content with /teas/, and read the home page's JSON-LD array as having no @type. It missed the robots.txt block.
- addyosmani/agentic-seo: It checks files for AI agents at the site root (llms.txt, robots rules for AI crawlers); it does not crawl pages, so page problems are outside what it looks at.

## Public copy, 2026-11-12

The three tools that refuse private addresses ran again on https://lumentea-test.vercel.app/ (Vercel; public/site, public/run_all.sh): the same pages with that host in their URLs, and the same 301 chain, X-Robots-Tag header and 404s (vercel.json). Their rows above come from that run. The control ran there too: found 16/16, 1 false claim (a summary line calling the article's title fine; it had reported the missing title), 24 problems, 3 min. The copy has no noindex added: a site-wide noindex would have hidden the two planted ones (D2, D13), so it stays up only for the test and is then to be taken down.

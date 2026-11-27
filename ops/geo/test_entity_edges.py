"""Offline tests for entity_edges.py: python3 -m unittest ops/geo/test_entity_edges.py"""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entity_edges import (ASH_ORG, OPERATOR, PERSON, PERSON_SOURCE, SITE, SITEMAP,  # noqa: E402
                          audit_entity_edges, blog_pages, check_pages, hold_frozen, pick)

PROFILES = {"https://x.com/GoSailGlobal", "https://github.com/zhuyansen", "https://orcid.org/0009-0000-2894-6285"}
ADDRESS = {"@type": "PostalAddress", "addressLocality": "Sheridan", "addressRegion": "WY", "addressCountry": "US"}
PERSON_REF = {"@type": "Person", "@id": PERSON, "name": "Jason Zhu", "url": "https://jasonzhu.ai/en"}


def page(*docs):
    return "".join(f'<script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>' for d in docs)


# The graph after 77e2eb2: product, company and person apart, joined by @id.
NEW_HOME = page({"@context": "https://schema.org", "@graph": [
    {"@type": "Organization", "@id": ASH_ORG, "name": "Agent Skills Hub", "founder": PERSON_REF,
     "parentOrganization": {"@type": "Organization", "@id": OPERATOR, "name": "GoSailGlobal LLC"},
     "sameAs": ["https://x.com/agentskillshub", "https://github.com/zhuyansen/agent-skills-hub"]},
    {"@type": "Organization", "@id": OPERATOR, "name": "GoSailGlobal LLC", "legalName": "GoSailGlobal LLC",
     "alternateName": "BRICKAI", "founder": {"@id": PERSON}, "address": ADDRESS},
    {"@type": "Person", "@id": PERSON, "name": "Jason Zhu", "alternateName": ["祝彦森", "Yansen Zhu"],
     "sameAs": sorted(PROFILES)},
]})
NEW_BLOG = page({"@context": "https://schema.org", "@type": "BlogPosting", "headline": "x", "author": PERSON_REF,
                 "publisher": {"@type": "Organization", "@id": ASH_ORG, "name": "Agent Skills Hub"}})

# The graph before 77e2eb2 (shapes from the 11-24 pages).
OLD_HOME = page(
    {"@context": "https://schema.org", "@type": "Organization", "@id": ASH_ORG, "name": "Agent Skills Hub",
     "legalName": "BRICKAI (GoSailGlobal LLC)", "alternateName": ["AgentSkillsHub", "BRICKAI"],
     "sameAs": ["https://x.com/GoSailGlobal", "https://www.youtube.com/@JasonZhuGoSail"],
     "founder": {"@type": "Person", "name": "Jason Zhu", "sameAs": ["https://github.com/ZhuYansen", "https://jasonzhu.ai"]}},
    {"@context": "https://schema.org", "@type": "Person", "@id": PERSON, "name": "Jason Zhu",
     "sameAs": ["https://jasonzhu.ai", "https://agentskillshub.top/about/", "https://github.com/zhuyansen"],
     "worksFor": {"@id": ASH_ORG}},
)
OLD_BLOG = page({"@context": "https://schema.org", "@type": "BlogPosting", "headline": "x",
                 "author": {"@type": "Person", "name": "Jason Zhu", "url": "https://x.com/GoSailGlobal"}})


def rules(result):
    return sorted({i["rule"] for i in result["issues"]})


class RelationRuleTests(unittest.TestCase):
    def test_split_graph_passes(self):
        r = check_pages({"/": NEW_HOME, "/blog/a/": NEW_BLOG}, PROFILES, {"/blog/a/"})
        self.assertEqual(r["issues"], [])
        self.assertEqual((r["pages_checked"], r["blocks"]), (2, 2))

    def test_merged_graph_breaks_every_rule_it_should(self):
        r = check_pages({"/": OLD_HOME, "/blog/a/": OLD_BLOG}, PROFILES, {"/blog/a/"})
        self.assertEqual(rules(r), [1, 2, 3, 4, 5, 6, 7, 8, 10])

    def test_each_finding_names_page_node_and_fix(self):
        r = check_pages({"/": OLD_HOME}, PROFILES, set())
        org = [i for i in r["issues"] if i["rule"] == 1]
        self.assertEqual(len(org), 1)
        self.assertEqual((org[0]["page"], org[0]["node"]), ("/", ASH_ORG))
        self.assertIn("https://x.com/GoSailGlobal", org[0]["detail"])
        self.assertTrue(all(i["fix"] for i in r["issues"]))

    def test_anonymous_blog_author_is_one_finding(self):
        r = check_pages({"/blog/a/": OLD_BLOG}, PROFILES, {"/blog/a/"})
        self.assertEqual([i["rule"] for i in r["issues"]], [8])

    def test_author_outside_the_blog_needs_the_founders_name(self):
        guest = page({"@type": "Review", "author": {"@type": "Person", "name": "A Reader"}})
        self.assertEqual(check_pages({"/reviews/": guest}, PROFILES, set())["issues"], [])
        self.assertEqual(rules(check_pages({"/blog/b/": guest}, PROFILES, {"/blog/b/"})), [8])

    def test_profile_added_on_jasonzhu_ai_is_expected_here(self):
        r = check_pages({"/": NEW_HOME}, PROFILES | {"https://space.bilibili.com/1"}, set())
        self.assertEqual(rules(r), [2])
        self.assertIn("space.bilibili.com", r["issues"][0]["detail"])

    def test_unreadable_jasonzhu_ai_skips_rule_2_but_keeps_rule_1(self):
        r = check_pages({"/": NEW_HOME}, None, set())
        self.assertEqual(r["issues"], [])
        leak = page({"@type": "Organization", "@id": ASH_ORG, "parentOrganization": {"@id": OPERATOR},
                     "sameAs": ["https://www.youtube.com/@JasonZhuGoSail"]})
        self.assertEqual(rules(check_pages({"/contact/": leak}, None, set())), [1])

    def test_reference_to_ash_org_without_parent_is_fine_off_the_home_page(self):
        ref = page({"@type": "WebPage", "publisher": {"@type": "Organization", "@id": ASH_ORG, "name": "Agent Skills Hub"}})
        self.assertEqual(check_pages({"/about/": ref}, PROFILES, set())["issues"], [])

    def test_parent_pointing_elsewhere_is_flagged(self):
        wrong = page({"@type": "Organization", "@id": ASH_ORG, "parentOrganization": {"@id": "https://example.com/#org"}})
        self.assertEqual(rules(check_pages({"/ai-info/": wrong}, PROFILES, set())), [7])

    def test_company_alias_on_the_company_node_is_fine(self):
        r = check_pages({"/": NEW_HOME}, PROFILES, set())
        self.assertNotIn(4, rules(r))

    def test_unparsable_block_is_rule_9(self):
        r = check_pages({"/x/": '<script type="application/ld+json">{"@type": "Thing",}</script>'}, PROFILES, set())
        self.assertEqual((rules(r), r["blocks"]), ([9], 0))

    def test_home_without_the_operator_node(self):
        bare = page({"@type": "Organization", "@id": ASH_ORG, "name": "Agent Skills Hub"})
        self.assertEqual(rules(check_pages({"/": bare}, PROFILES, set())), [6, 7, 10])


def home_with(change):
    """NEW_HOME with `change` applied to the product node: the mutations rules 1-9 let through on 11-27."""
    doc = json.loads(NEW_HOME[NEW_HOME.index(">") + 1:NEW_HOME.rindex("</script>")])
    change(next(n for n in doc["@graph"] if n["@id"] == ASH_ORG))
    return page(doc)


class FounderEdgeTests(unittest.TestCase):
    def test_dropping_the_products_founder_is_found(self):
        r = check_pages({"/": home_with(lambda n: n.pop("founder"))}, PROFILES, set())
        self.assertEqual(rules(r), [10])

    def test_founder_pointed_at_the_company_is_found(self):
        r = check_pages({"/": home_with(lambda n: n.update(founder={"@id": OPERATOR}))}, PROFILES, set())
        self.assertEqual(rules(r), [10])
        self.assertIn(OPERATOR, r["issues"][0]["detail"])

    def test_company_founder_must_be_the_person(self):
        co = page({"@type": "Organization", "@id": OPERATOR, "name": "GoSailGlobal LLC", "founder": {"@id": ASH_ORG}})
        self.assertEqual(rules(check_pages({"/about/": co}, PROFILES, set())), [10])

    def test_off_the_home_page_a_reference_needs_no_founder(self):
        ref = page({"@type": "WebPage", "publisher": {"@type": "Organization", "@id": ASH_ORG, "name": "Agent Skills Hub"}})
        self.assertEqual(check_pages({"/best/x/": ref}, PROFILES, set())["issues"], [])


class BlogEdgeTests(unittest.TestCase):
    def test_blog_post_without_json_ld_is_found(self):
        r = check_pages({"/blog/probe/": "<html></html>"}, PROFILES, {"/blog/probe/"})
        self.assertEqual((rules(r), r["blocks"]), ([11], 0))

    def test_blog_post_without_an_author_is_found(self):
        bare = page({"@context": "https://schema.org", "@type": "BlogPosting", "headline": "x"})
        self.assertEqual(rules(check_pages({"/blog/b/": bare}, PROFILES, {"/blog/b/"})), [11])

    def test_wrong_author_is_rule_8_only(self):
        self.assertEqual(rules(check_pages({"/blog/a/": OLD_BLOG}, PROFILES, {"/blog/a/"})), [8])


class TwitterSiteTests(unittest.TestCase):
    def test_the_founders_handle_as_twitter_site_is_found(self):
        html = '<meta name="twitter:site" content="@GoSailGlobal" />' + NEW_BLOG
        r = check_pages({"/blog/a/": html}, PROFILES, {"/blog/a/"})
        self.assertEqual(rules(r), [12])

    def test_product_site_and_founder_creator_pass(self):
        html = ('<meta content="@agentskillshub" name="twitter:site">'
                '<meta name="twitter:creator" content="@GoSailGlobal" />' + NEW_BLOG)
        self.assertEqual(check_pages({"/blog/a/": html}, PROFILES, {"/blog/a/"})["issues"], [])

    def test_fallback_profiles_still_know_the_handle(self):
        html = '<meta name="twitter:site" content="@gosailglobal">'
        self.assertEqual(rules(check_pages({"/x/": html}, None, set())), [12])


class AliasTests(unittest.TestCase):
    def test_aliases_must_match_jasonzhu_ai(self):
        r = check_pages({"/": NEW_HOME}, PROFILES, set(), aliases={"祝彦森", "Yansen Zhu", "JasonZhu.AI"})
        self.assertEqual(rules(r), [2])
        self.assertIn("JasonZhu.AI", r["issues"][0]["detail"])

    def test_same_aliases_or_unreadable_pass(self):
        self.assertEqual(check_pages({"/": NEW_HOME}, PROFILES, set(), aliases={"祝彦森", "Yansen Zhu"})["issues"], [])
        self.assertEqual(check_pages({"/": NEW_HOME}, PROFILES, set(), aliases=None)["issues"], [])


class CoverageTests(unittest.TestCase):
    def test_pick_is_even_and_stable(self):
        paths = [f"/top/{i:03d}/" for i in range(100)]
        chosen = pick(list(reversed(paths)), 20)
        self.assertEqual(len(chosen), 20)
        self.assertEqual(chosen, pick(paths, 20))
        self.assertEqual((chosen[0], chosen[1]), ("/top/000/", "/top/005/"))
        self.assertEqual(pick(paths[:3], 20), paths[:3])

    def fake(self, sitemap_up=True):
        top = "".join(f"<url><loc>{SITE}/top/{i}/</loc></url>" for i in range(50))
        bodies = {
            SITEMAP: f"<sitemapindex><sitemap><loc>{SITE}/sitemap-static.xml</loc></sitemap>"
                     f"<sitemap><loc>{SITE}/sitemap-top.xml</loc></sitemap></sitemapindex>",
            f"{SITE}/sitemap-static.xml": f"<urlset><url><loc>{SITE}/</loc></url><url><loc>{SITE}/how-we-grade/</loc></url></urlset>",
            f"{SITE}/sitemap-top.xml": f"<urlset>{top}</urlset>",
            f"{SITE}/": NEW_HOME,
            PERSON_SOURCE: page({"@type": "Person", "@id": PERSON, "sameAs": sorted(PROFILES),
                                 "alternateName": ["祝彦森", "Yansen Zhu"]}),
        }
        fetched = []

        def get(url, headers=None, timeout=12.0):
            fetched.append(url)
            if url == SITEMAP and not sitemap_up:
                return 503, {}, ""
            if url in bodies:
                return 200, {}, bodies[url]
            return 200, {}, NEW_BLOG if "/blog/" in url else "<html></html>"
        return get, fetched

    def test_audit_reads_every_template_and_says_how_much(self):
        get, fetched = self.fake()
        r = audit_entity_edges(get)
        self.assertEqual(r["status"], "VERIFIED", r["issues"] or r["fetch_errors"])
        self.assertEqual(r["coverage"], {"static": {"in_sitemap": 2, "checked": 2}, "top": {"in_sitemap": 50, "checked": 20}})
        self.assertIn(f"{SITE}/how-we-grade/", fetched)
        self.assertEqual(sum(1 for u in fetched if "/top/" in u), 20)

    def test_no_sitemap_is_partial_not_verified(self):
        get, fetched = self.fake(sitemap_up=False)
        r = audit_entity_edges(get)
        self.assertEqual(r["status"], "PARTIAL_FETCH")
        self.assertIn("sitemap", r["fetch_errors"])
        self.assertEqual(r["coverage"], {})


DURING, AFTER = date(2026, 11, 27), date(2027, 1, 2)
SHELL_PERSON = page({"@context": "https://schema.org", "@type": "Person", "@id": PERSON, "name": "Jason Zhu",
                     "alternateName": ["祝彦森", "Yansen Zhu", "Zhu Yansen"], "sameAs": sorted(PROFILES)})
FOUNDER_SITE = '<meta name="twitter:site" content="@GoSailGlobal" />'
ANON = page({"@type": "WebPage", "author": {"@type": "Person", "name": "Jason Zhu", "url": f"{SITE}/about/"}})


def held(pages, today, aliases=frozenset({"祝彦森", "Yansen Zhu"})):
    return hold_frozen(check_pages(pages, PROFILES, set(), set(aliases)), pages, today)


class FreezeTests(unittest.TestCase):
    def test_a_frozen_page_is_held_until_the_last_readout(self):
        pages = {"/best/ai-design/": ANON}
        r = held(pages, DURING)
        self.assertEqual((r["issues"], rules({"issues": r["frozen"]})), ([], [8]))
        self.assertEqual((rules(held(pages, AFTER)), held(pages, AFTER)["frozen"]), ([8], []))

    def test_a_shell_copy_keeps_the_shells_part_frozen(self):
        home = FOUNDER_SITE + NEW_HOME + SHELL_PERSON
        book = FOUNDER_SITE + SHELL_PERSON + page({"@type": "Article", "author": {"@id": PERSON}})
        r = held({"/": home, "/book/ch01/": book}, DURING)
        self.assertEqual(r["issues"], [])
        self.assertEqual(sorted({(i["page"], i["rule"]) for i in r["frozen"]}),
                         [("/", 2), ("/", 12), ("/book/ch01/", 2), ("/book/ch01/", 12)])

    def test_a_shell_page_with_its_own_json_ld_keeps_the_shells_twitter_site_frozen(self):
        category = FOUNDER_SITE + '<div id="root"></div>' + page({"@type": "CollectionPage", "name": "MCP servers"})
        r = held({"/": NEW_HOME + SHELL_PERSON, "/category/mcp-server/": category}, DURING)
        self.assertEqual(([i["page"] for i in r["issues"]], [(i["page"], i["rule"]) for i in r["frozen"]]),
                         ([], [("/", 2), ("/category/mcp-server/", 12)]))

    def test_a_page_not_copied_from_the_shell_is_not_held(self):
        r = held({"/": NEW_HOME + SHELL_PERSON, "/skill/a/b/": FOUNDER_SITE}, DURING)
        self.assertEqual([(i["page"], i["rule"]) for i in r["issues"]], [("/skill/a/b/", 12)])

    def test_a_wrong_profile_on_a_shell_copy_is_still_an_issue(self):
        wrong = SHELL_PERSON.replace("https://github.com/zhuyansen", "https://github.com/someone")
        r = held({"/": NEW_HOME + SHELL_PERSON, "/submit/": wrong}, DURING)
        self.assertIn(("/submit/", 2), [(i["page"], i["rule"]) for i in r["issues"]])

    def test_after_the_readout_nothing_is_held(self):
        home = FOUNDER_SITE + NEW_HOME + SHELL_PERSON
        r = held({"/": home, "/book/ch01/": FOUNDER_SITE + SHELL_PERSON}, AFTER)
        self.assertEqual(r["frozen"], [])
        self.assertEqual(sorted({i["rule"] for i in r["issues"]}), [2, 12])


class BlogPageTests(unittest.TestCase):
    def test_blog_posts_with_json_ld_are_found_as_site_paths(self):
        paths = blog_pages()
        self.assertTrue(paths)
        self.assertTrue(all(p.startswith("/blog/") and p.endswith("/") for p in paths))
        self.assertNotIn("/blog/", paths)  # the index carries no JSON-LD


if __name__ == "__main__":
    unittest.main()

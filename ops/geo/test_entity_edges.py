"""Offline tests for entity_edges.py: python3 -m unittest ops/geo/test_entity_edges.py"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entity_edges import ASH_ORG, OPERATOR, PERSON, blog_pages, check_pages  # noqa: E402

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
        self.assertEqual(rules(r), [1, 2, 3, 4, 5, 6, 7, 8])

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
        self.assertEqual(rules(check_pages({"/": bare}, PROFILES, set())), [6, 7])


class BlogPageTests(unittest.TestCase):
    def test_blog_posts_with_json_ld_are_found_as_site_paths(self):
        paths = blog_pages()
        self.assertTrue(paths)
        self.assertTrue(all(p.startswith("/blog/") and p.endswith("/") for p in paths))
        self.assertNotIn("/blog/", paths)  # the index carries no JSON-LD


if __name__ == "__main__":
    unittest.main()

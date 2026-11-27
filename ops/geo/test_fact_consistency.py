"""Offline tests for fact_consistency.py: python3 -m unittest ops/geo/test_fact_consistency.py"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fact_consistency import body_to_text, check_texts, parse_count  # noqa: E402

LEDGER = json.loads((Path(__file__).resolve().parent / "brand-facts.json").read_text(encoding="utf-8"))
HOME = ("https://agentskillshub.top/", "Claude Skills Marketplace: 280,000+ AI Agent Tools, every popular one security-graded.")
AI_INFO = ("https://agentskillshub.top/ai-info/", "Security-Graded Count 140,000+ repositories graded")


def run(**extra):
    texts = {"site_home": HOME, "site_ai_info": AI_INFO}
    texts.update({k: ("https://example.test/" + k, v) for k, v in extra.items()})
    return check_texts(texts, LEDGER)


def facts(result):
    return [(c["fact"], c["source"]) for c in result["conflicts"]]


class ParseTests(unittest.TestCase):
    def test_parse_count(self):
        self.assertEqual(parse_count("280,000"), 280000)
        self.assertEqual(parse_count("130K"), 130000)
        self.assertEqual(parse_count("1.2M"), 1200000)

    def test_wikidata_inception_keeps_precision(self):
        body = json.dumps({"entities": {"Q1": {"labels": {}, "descriptions": {}, "claims": {"P571": [
            {"mainsnak": {"datavalue": {"value": {"time": "+2026-03-00T00:00:00Z", "precision": 10}}}}]}}}})
        self.assertIn("inception 2026-03", body_to_text("wikidata", body))


class CheckTests(unittest.TestCase):
    def test_live_pages_agree(self):
        r = run()
        self.assertEqual(r["live_directory_size"], 280000)
        self.assertEqual(r["live_graded_count"], 140000)
        self.assertEqual(r["conflicts"], [])

    def test_unread_live_count_skips_counts_only(self):
        r = check_texts({"site_ai_info": AI_INFO, "npm_mcp": ("u", "281,000+ skills; checked against 40 security rules")}, LEDGER)
        self.assertIn("directory_size", r["counts_skipped"])
        self.assertEqual(facts(r), [("security_rules", "npm_mcp")])

    def test_stale_count_is_flagged(self):
        self.assertIn(("skill_count", "npm_mcp"), facts(run(npm_mcp="a directory of 100K+ skills")))

    def test_rounded_copy_within_tolerance_passes(self):
        self.assertEqual(run(github_readme="indexes 267,000+ projects")["conflicts"], [])

    def test_snapshot_needs_its_anchor(self):
        anchored = run(site_llms_txt="dataset (DOI: 10.5281/zenodo.24387073): June 2026 snapshot of 105,000+ indexed skills")
        self.assertEqual(anchored["conflicts"], [])
        old_doi = run(site_llms_txt="dataset (DOI: 10.5281/zenodo.24387074): 105,000+ indexed skills audit")
        self.assertEqual(old_doi["conflicts"], [])
        bare = run(site_mcp_server_card="Deep search across 130K+ skills with filters")
        self.assertIn("equals snapshot", bare["conflicts"][0]["why"])

    def test_snapshot_source_describes_itself(self):
        self.assertEqual(run(zenodo_24387073="covering 105,000+ open-source AI agent skills")["conflicts"], [])

    def test_small_numbers_and_units_are_not_counts(self):
        self.assertEqual(run(site_llms_txt="10 mcp tools for google services; 10 multi-agent tools")["conflicts"], [])

    def test_known_other_counts_skip(self):
        self.assertEqual(run(site_home_extra="As Liu et al. (2026) report in their study of 31,132 agent skills")["conflicts"], [])

    def test_launch_date(self):
        self.assertEqual(run(a="launched 2026-03-08", b="inception 2026-03", c="Launched March 8, 2026")["conflicts"], [])
        self.assertIn(("launch_date", "d"), facts(run(d="founded in 2024-05-01")))

    def test_rule_count(self):
        self.assertEqual(run(a="against 44 published rules; a 44-rule scan")["conflicts"], [])
        self.assertIn(("security_rules", "b"), facts(run(b="checked against 40 security rules")))

    def test_founder(self):
        self.assertEqual(run(a="founded by Jason Zhu", b="founder and maintainer Jason Zhu")["conflicts"], [])
        self.assertIn(("founder", "c"), facts(run(c="founded by Someone Else")))

    def test_foreign_domain_needs_disclaimer(self):
        ok = run(a="not affiliated with agentskillshub.dev", b="与 agentskillshub.dev （及 support@agentskillshub.dev ）无任何关联")
        self.assertEqual(ok["conflicts"], [])
        self.assertIn(("foreign_domain", "c"), facts(run(c="Contact support@agentskillshub.dev for help")))



class SummaryAndFieldTests(unittest.TestCase):
    """2026-11-27: /ai-info/ called the index total "graded" in its three summary tags and nothing noticed."""

    def test_summary_tags_are_read(self):
        body = ('<meta property="og:description" content="X: 280,000+ skills graded on 44 public rules." />'
                '<meta name="description" content="X: 280,000+ skills graded on 44 public rules.">'
                "<p>visible</p>")
        text = body_to_text("html", body)
        self.assertIn("graded on 44 public rules", text)
        self.assertEqual(text.count("graded on 44"), 1)        # the same text in two tags is read once

    def test_index_total_called_graded_is_a_conflict(self):
        r = run(jasonzhu_about="operated by X LLC, 280,000+ skills & MCP servers graded on 44 public rules.")
        self.assertEqual(facts(r), [("skill_count", "jasonzhu_about")])
        self.assertIn("calls it graded", r["conflicts"][0]["why"])

    def test_graded_count_called_indexed_is_a_conflict(self):
        r = run(a="the hub has 140,000+ skills indexed so far")
        self.assertEqual(facts(r), [("skill_count", "a")])
        self.assertIn("calls it indexed", r["conflicts"][0]["why"])

    def test_the_fixed_wording_passes(self):
        fixed = "operated by X LLC; 280,000+ skills & MCP servers indexed; grades follow 44 public rules."
        self.assertEqual(run(a=fixed)["conflicts"], [])

    def test_a_clause_that_names_neither_may_match_either(self):
        self.assertEqual(run(a="280,000+ skills, MCP servers & tools, every popular one security-graded",
                             b="140,000+ repositories")["conflicts"], [])

    def test_an_anchored_snapshot_wins_over_a_nearby_live_count(self):
        # 138,000 is within 5% of the graded 140,000, and the clause says indexed: still the dev.to snapshot.
        self.assertEqual(run(a="our dev.to audit of 138,000 skills indexed in July")["conflicts"], [])

    def test_a_tagline_dot_ends_the_clause(self):
        self.assertEqual(run(a="267,000+ projects · **security-graded** + quality-scored on 10 dimensions")["conflicts"], [])

    def test_the_company_founding_date_is_its_own(self):
        self.assertEqual(run(company_home='"foundingDate": "2026-10-21"')["conflicts"], [])
        self.assertIn(("launch_date", "a"), facts(run(a='"foundingDate": "2026-10-21"')))

    def test_the_company_site_is_held_to_the_rule_count(self):
        self.assertIn(("security_rules", "company_home"), facts(run(company_home="security-graded against 42 published rules")))


if __name__ == "__main__":
    unittest.main()

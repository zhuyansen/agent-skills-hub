"""Offline tests for fact_todos.py: python3 -m unittest ops/geo/test_fact_todos.py"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fact_todos import build_todos, floor_text, token_of  # noqa: E402

LIVE = {"live_directory_size": 281000, "live_graded_count": 140000}


def conflict(source, found, fact="skill_count", expected="~281,000+"):
    return {"source": source, "fact": fact, "found": found, "expected": expected, "url": "https://x.test/"}


class TodoTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        (self.repo / "frontend/scripts").mkdir(parents=True)
        (self.repo / "frontend/public/.well-known/mcp").mkdir(parents=True)
        (self.repo / "frontend/scripts/generate-static-pages.mjs").write_text(
            "<p>grades <span data-count='graded'>132,000+</span> repos</p>\n<p>indexes 267,000+ skills</p>\n")
        (self.repo / "frontend/public/.well-known/mcp/server-card.json").write_text('{"d": "search 130K+ skills"}\n')

    def todos(self, *conflicts, github_has=None):
        return build_todos({**LIVE, "conflicts": list(conflicts)}, self.repo, github_has)

    def test_helpers(self):
        self.assertEqual(token_of("132,000+ repositories"), "132,000")
        self.assertEqual(token_of("130K+ skills"), "130K")
        self.assertEqual(floor_text(281000, 50000), "250K+")
        self.assertEqual(floor_text(147000, 5000), "145K+")

    def test_built_page_gets_a_marker_and_its_line(self):
        [t] = self.todos(conflict("site_ai_info", "267,000+ skills"))
        self.assertEqual(t["where"], [{"file": "frontend/scripts/generate-static-pages.mjs", "line": 2, "marked": False}])
        self.assertIn('data-count="total"', t["replace_with"])

    def test_already_marked_waits_for_deploy(self):
        [t] = self.todos(conflict("site_ai_info", "132,000+ repositories"))
        self.assertEqual(t["where"], [])
        self.assertIn("部署", t["note"])

    def test_static_file_gets_a_floor(self):
        [t] = self.todos(conflict("site_mcp_server_card", "130K+ skills"))
        self.assertEqual(t["where"][0]["line"], 1)
        self.assertEqual(t["replace_with"], "140K+")  # closer to the graded count than to the indexed one

    def test_package_fixed_on_github_only_needs_publish(self):
        [t] = self.todos(conflict("npm_mcp", "100K+ skills"), github_has=lambda repo, f, tok: False)
        self.assertEqual(t["where"], [])
        self.assertIn("npm publish", t["note"])
        [t] = self.todos(conflict("npm_mcp", "100K+ skills"), github_has=lambda repo, f, tok: f == "README.md")
        self.assertTrue(t["where"])

    def test_small_number_is_probably_a_subset(self):
        [t] = self.todos(conflict("github_readme", "20K quality skills"))
        self.assertIn("核对", t["replace_with"])

    def test_other_fact_takes_ledger_value_and_dedupes(self):
        c = conflict("wikidata_org", 40, fact="security_rules", expected=44)
        todos = self.todos(c, c)
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["replace_with"], "44")
        self.assertIn("wikidata.org", todos[0]["then"])


if __name__ == "__main__":
    unittest.main()

"""Offline tests for academic_index.py: python3 -m unittest ops/geo/test_academic_index.py"""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from academic_index import ORCID, audit_academic_index, check_work, is_ours, summarize  # noqa: E402

TODAY = date(2026, 11, 22)
OURS = f"https://orcid.org/{ORCID}"


def work(**kw):
    base = {"doi": "10.5281/zenodo.1", "title": "t", "published": "2026-11-01", "handle": True,
            "datacite_creators": [{"name": "Zhu, Jason", "ids": [ORCID]}], "openalex": None,
            "semantic_scholar": False, "wikidata": ""}
    return base | kw


def kinds(row):
    return [i["kind"] for i in row["issues"]]


class NameTests(unittest.TestCase):
    def test_our_names(self):
        for n in ("Zhu, Jason", "J ZHU", "zhu, yansen", "Yansen Zhu", "祝彦森", "Jason Zhu"):
            self.assertTrue(is_ours(n), n)
        for n in ("竹彦 森", "Zhu, Wei", "Jason Chu", "", None):
            self.assertFalse(is_ours(n), n)


class CheckTests(unittest.TestCase):
    def test_clean_work(self):
        self.assertEqual(kinds(check_work(work(), TODAY)), [])

    def test_unresolved_doi_waits_two_days_then_is_an_issue(self):
        young = check_work(work(handle=False, published="2026-11-21"), TODAY)
        self.assertEqual(kinds(young), [])
        self.assertIn("等登记", young["notes"][0])
        old = check_work(work(handle=False, published="2026-11-19"), TODAY)
        self.assertEqual(kinds(old), ["doi_unresolved"])
        self.assertIn("zenodo.org/records/1", old["issues"][0]["fix"])

    def test_duplicate_and_orcid_less_creators(self):
        dup = check_work(work(datacite_creators=[{"name": "zhu, yansen", "ids": [ORCID]},
                                                 {"name": "Jason Zhu", "ids": [ORCID]}]), TODAY)
        self.assertEqual(kinds(dup), ["creator_duplicate"])
        bare = check_work(work(datacite_creators=[{"name": "Zhu, Jason", "ids": []}]), TODAY)
        self.assertEqual(kinds(bare), ["creator_no_orcid"])

    def test_openalex_misattribution_by_name_and_by_orcid(self):
        oa = {"id": "W7167922915", "authorships": [
            {"author_id": "A5009989201", "display_name": "竹彦 森", "raw": "zhu, yansen", "orcid": ""},
            {"author_id": "A5048188910", "display_name": "J ZHU", "raw": "Jason Zhu", "orcid": "https://orcid.org/0000-0001-2345-6789"},
            {"author_id": "A9", "display_name": "Someone Else", "raw": "Someone Else", "orcid": ""}]}
        row = check_work(work(openalex=oa), TODAY)
        self.assertEqual(kinds(row), ["openalex_misattributed", "openalex_misattributed"])
        self.assertIn("别人的 ORCID", row["issues"][1]["detail"])

    def test_our_profile_without_orcid_is_a_note(self):
        oa = {"id": "W1", "authorships": [{"author_id": "A5163069727", "display_name": "Jason Zhu", "raw": "Zhu, Jason", "orcid": ""}]}
        row = check_work(work(openalex=oa), TODAY)
        self.assertEqual(kinds(row), [])
        self.assertEqual(row["our_openalex_authors"], ["A5163069727"])

    def test_split_profiles_and_status(self):
        rows = [check_work(work(doi=f"10.5281/zenodo.{i}", openalex={"id": f"W{i}", "authorships": [
            {"author_id": a, "display_name": "Jason Zhu", "raw": "Zhu, Jason", "orcid": OURS}]}), TODAY)
            for i, a in ((1, "A1"), (2, "A2"))]
        node = summarize(rows, "", {})
        self.assertEqual([i["kind"] for i in node["issues"]], ["openalex_split"])
        self.assertEqual(node["status"], "ISSUES_FOUND")
        self.assertEqual(summarize(rows[:1], "A1", {})["status"], "VERIFIED")
        self.assertEqual(summarize([], "", {"orcid": "down"})["status"], "PARTIAL_FETCH")


class FetchTests(unittest.TestCase):
    def test_audit_reads_every_source(self):
        doi = "10.5281/zenodo.24420920"
        pages = {
            f"https://pub.orcid.org/v3.0/{ORCID}/works": (200, {"group": [{"work-summary": [{
                "title": {"title": {"value": "Paper"}},
                "external-ids": {"external-id": [{"external-id-type": "doi", "external-id-value": doi.upper()}]},
                "publication-date": {"year": {"value": "2026"}, "month": {"value": "11"}, "day": {"value": "18"}}}]}]}),
            f"https://doi.org/api/handles/{doi}": (404, {"responseCode": 100}),
            f"https://api.datacite.org/dois/{doi}": (404, {"errors": []}),
        }

        def fake_get(url, headers=None, timeout=12.0):
            if url.startswith("https://query.wikidata.org/"):
                return 200, {}, json.dumps({"results": {"bindings": []}})
            code, body = pages.get(url, (404, {}))
            return code, {}, json.dumps(body)

        node = audit_academic_index(fake_get, today=TODAY, pause=0)
        self.assertEqual(node["coverage"]["works"], 1)
        self.assertEqual([i["kind"] for i in node["issues"]], ["doi_unresolved"])
        self.assertIs(node["works"][0]["semantic_scholar"], False)


if __name__ == "__main__":
    unittest.main()

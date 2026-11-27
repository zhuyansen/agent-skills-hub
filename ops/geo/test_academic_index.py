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
        row = check_work(work(openalex=oa, our_dois={"10.5281/zenodo.1", "10.5281/zenodo.2"},
                              author_works={"A5163069727": ["10.5281/zenodo.1", "10.5281/zenodo.2", "10.5281/zenodo.9"]}), TODAY)
        self.assertEqual(kinds(row), [])
        self.assertEqual(row["our_openalex_authors"], ["A5163069727"])
        self.assertIn("没挂 ORCID", row["notes"][0])

    def test_split_profiles_and_status(self):
        rows = [check_work(work(doi=f"10.5281/zenodo.{i}", openalex={"id": f"W{i}", "authorships": [
            {"author_id": a, "display_name": "Jason Zhu", "raw": "Zhu, Jason", "orcid": OURS}]}), TODAY)
            for i, a in ((1, "A1"), (2, "A2"))]
        node = summarize(rows, "", {})
        self.assertEqual(node["issues"], [])             # two pages are not an error to fix: rule 1 merges nothing
        self.assertIn("不认领、不合并", node["notes"][0])
        self.assertEqual(node["status"], "VERIFIED")
        self.assertEqual(summarize(rows[:1], "A1", {})["status"], "VERIFIED")
        self.assertEqual(summarize([], "", {"orcid": "down"})["status"], "PARTIAL_FETCH")


# 11-24: OpenAlex filed the Backlink Spam List under a Stanford researcher's page; 11-26 it moved it to ours.
STANFORD = ["10.1287/mnsc.2023.4695", "10.1111/jofi.13477", "10.1145/3442381.3449842", "10.2139/ssrn.3350138",
            "", "10.2139/ssrn.3600206", "10.32388/27kvo0"]
OUR_FAMILY = {"10.5281/zenodo.24387076", "10.5281/zenodo.24387075", "10.5281/zenodo.24386243", "10.5281/zenodo.24386242",
              "10.5281/zenodo.24387074", "10.5281/zenodo.24387073", "10.5281/zenodo.24387072", "10.5281/zenodo.24387071",
              "10.5281/zenodo.24420871", "10.5281/zenodo.24420870", "10.5281/zenodo.24432858", "10.5281/zenodo.24420919"}
OUR_PAGE = ["10.5281/zenodo.24387081", "10.5281/zenodo.24387069", "10.5281/zenodo.24387075", "10.5281/zenodo.24387073",
            "10.5281/zenodo.24386242", "10.5281/zenodo.24387071", "10.5281/zenodo.24387079", "10.5281/zenodo.24420870",
            "10.5281/zenodo.24420919"]


def spam_list(author_id, author_works):
    oa = {"id": "W7237096646", "authorships": [{"author_id": author_id, "display_name": "Jason Zhu", "raw": "Jason Zhu", "orcid": ""}]}
    return work(doi="10.5281/zenodo.24387076", openalex=oa, our_dois=OUR_FAMILY, author_works=author_works)


class SameNameTests(unittest.TestCase):
    def test_a_page_mostly_someone_elses_is_misfiled(self):
        row = check_work(spam_list("A5087679970", {"A5087679970": STANFORD + ["10.5281/zenodo.24387075"]}), TODAY)
        self.assertEqual(kinds(row), ["openalex_misattributed"])
        self.assertIn("8 个作品里只有 1 个是你的", row["issues"][0]["detail"])
        self.assertIn("移走", row["issues"][0]["fix"])
        self.assertEqual(row["our_openalex_authors"], [])

    def test_the_page_it_moved_to_is_ours(self):
        row = check_work(spam_list("A5163069727", {"A5163069727": OUR_PAGE}), TODAY)
        self.assertEqual(kinds(row), [])
        self.assertEqual(row["our_openalex_authors"], ["A5163069727"])
        self.assertIn("9 个作品里 6 个是你的", row["notes"][0])

    def test_same_name_with_unread_works_is_unverified(self):
        row = check_work(spam_list("A1", {"A1": None}), TODAY)
        self.assertEqual((kinds(row), row["our_openalex_authors"], row["unverified_openalex_authors"]), ([], [], ["A1"]))
        node = summarize([row], "", {})
        self.assertEqual(node["status"], "PARTIAL_FETCH")
        self.assertEqual(node["openalex_unverified_authors"], ["A1"])

    def test_no_text_tells_you_to_claim_or_merge(self):
        rows = [check_work(spam_list(a, w), TODAY) for a, w in (("A5087679970", {"A5087679970": STANFORD}),
                                                               ("A5163069727", {"A5163069727": OUR_PAGE}),
                                                               ("A1", {"A1": None}))]
        node = summarize(rows + [check_work(work(doi="10.5281/zenodo.9", openalex={"id": "W9", "authorships": [
            {"author_id": "A2", "display_name": "Jason Zhu", "raw": "Zhu, Jason", "orcid": OURS}]}), TODAY)], "", {})
        text = json.dumps(node, ensure_ascii=False)
        for advice in ("添加即合并", "认领后", "认领自己的作者页"):
            self.assertNotIn(advice, text)


class FetchTests(unittest.TestCase):
    def test_audit_reads_every_source(self):
        doi = "10.5281/zenodo.24420920"
        pages = {
            f"https://pub.orcid.org/v3.0/{ORCID}/works": (200, {"group": [{"work-summary": [{
                "title": {"title": {"value": "Paper"}},
                "external-ids": {"external-id": [{"external-id-type": "doi", "external-id-value": doi.upper()}]},
                "publication-date": {"year": {"value": "2026"}, "month": {"value": "11"}, "day": {"value": "18"}}}]}]}),
            f"https://doi.org/api/handles/{doi}": (404, {"responseCode": 100}),
            f"https://api.datacite.org/dois/{doi}": (200, {"data": {"attributes": {
                "creators": [{"name": "Zhu, Jason", "nameIdentifiers": [{"nameIdentifier": OURS}]}],
                "relatedIdentifiers": [{"relationType": "IsVersionOf", "relatedIdentifierType": "DOI",
                                        "relatedIdentifier": "10.5281/zenodo.24420919"}]}}}),
            f"https://api.openalex.org/works/doi:{doi}?select=id,authorships": (200, {"id": "https://openalex.org/W1", "authorships": [
                {"author": {"id": "https://openalex.org/A5163069727", "display_name": "Jason Zhu", "orcid": None},
                 "raw_author_name": "Zhu, Jason"}]}),
            "https://api.openalex.org/works?filter=author.id:A5163069727&per-page=200&select=doi": (200, {"results": [
                {"doi": "https://doi.org/10.5281/zenodo.24420919"}, {"doi": "https://doi.org/10.5281/zenodo.24420920"}]}),
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
        # the concept DOI came from DataCite, so the same-name page with both DOIs counts as ours
        self.assertEqual(node["openalex_our_authors"], ["A5163069727"])


if __name__ == "__main__":
    unittest.main()

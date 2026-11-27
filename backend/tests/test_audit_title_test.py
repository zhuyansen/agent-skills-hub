"""ops/gsc/audit_title_test.py: the groups match the build, and the arithmetic of the read-out."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops" / "gsc"))
import audit_title_test as att  # noqa: E402

TEST_ID = "audit-title-grade-date"


def test_buckets_match_the_build():
    # Same numbers as frontend/scripts/audit-meta.test.mjs pins for titleBucket().
    assert att.title_bucket("0xJacky/nginx-ui", TEST_ID) == 17
    assert att.title_bucket("anthropics/skills", TEST_ID) == 80
    assert att.title_bucket("langgenius/dify", TEST_ID) == 33
    assert att.title_bucket("MorDavid/BruteForceAI", TEST_ID) == 20
    assert att.fnv1a32("") == 0x811C9DC5 and att.fnv1a32("a") == 0xE40C292C


def test_groups_from_the_test_file():
    test = att.load_test()
    assert test["id"] == TEST_ID and test["share_percent"] == 10
    excluded = next(iter(test["excluded_set"]))
    assert att.group_of(f"https://agentskillshub.top/audit/{excluded}/", test) == "excluded"
    assert att.group_of("https://agentskillshub.top/audit/0xJacky/nginx-ui/", test) in ("control", "excluded")
    assert att.group_of("https://agentskillshub.top/skill/0xJacky/nginx-ui/", test) is None
    assert att.group_of("https://agentskillshub.top/audit/a/b/?x=1", test) is None
    names = [f"https://agentskillshub.top/audit/owner{i}/repo{i}/" for i in range(20000)]
    treated = sum(att.group_of(u, test) == "treated" for u in names)
    assert 0.09 < treated / len(names) < 0.11


def row(clicks, impressions, position=5.0):
    return {"clicks": clicks, "impressions": impressions, "position": position}


def test_difference_in_differences():
    paired = {
        "treated": [(row(10, 1000), row(30, 1000))],   # 1% -> 3%
        "control": [(row(20, 1000), row(25, 1000))],   # 2% -> 2.5%
    }
    assert abs(att.did(paired) - 1.5) < 1e-9
    assert att.did({"treated": [], "control": paired["control"]}) is None


def test_bootstrap_interval_brackets_the_estimate():
    paired = {
        "treated": [(row(1 + i % 3, 100), row(1 + i % 3 + i % 4, 100)) for i in range(60)],
        "control": [(row(1 + i % 3, 100), row(1 + i % 5, 100)) for i in range(60)],
    }
    lo, hi = att.bootstrap_interval(paired, reps=400)
    assert lo < round(att.did(paired), 3) < hi


def test_only_pages_seen_before_the_start_are_compared():
    test = {"id": TEST_ID, "share_percent": 100, "excluded_set": set()}
    pre = {"https://agentskillshub.top/audit/a/b/": row(1, 10), "https://agentskillshub.top/audit/c/d/": row(0, 0)}
    post = {"https://agentskillshub.top/audit/a/b/": row(2, 10), "https://agentskillshub.top/audit/e/f/": row(9, 9)}
    paired = att.pair_pages(pre, post, test)
    assert [(p["clicks"], q["clicks"]) for p, q in paired["treated"]] == [(1, 2)]
    assert att.totals([q for _, q in paired["treated"]])["ctr_pct"] == 20.0

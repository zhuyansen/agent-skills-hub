"""App picks in the radar mail (10-20): a business's own app or one place's is not a pick.
No network: Apple's lookup and Jev are stubbed."""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import appstore  # noqa: E402
import memes  # noqa: E402
import radar  # noqa: E402


class _Jev:
    def __init__(self, answers=None, fail=False):
        self.answers, self.fail, self.seen = answers or {}, fail, []

    def decisions(self, state, questions):
        self.seen.append((state, questions))
        if self.fail:
            raise RuntimeError("402")
        return SimpleNamespace(answers={k: {"type": "noul", "noul": v} for k, v in self.answers.items()})


def test_one_call_answers_every_app_question():
    jev = _Jev({"build_now": 0.79, "own_app": 0.93, "one_place": 0.40})
    got = memes.answers(jev, {"app": "Derrimut 24:7 Gym"}, memes.APP_OPPORTUNITY)
    assert got == {"build_now": 0.79, "own_app": 0.93, "one_place": 0.40} and len(jev.seen) == 1
    assert set(jev.seen[0][1]) == {"build_now", "own_app", "one_place"}


def test_no_jev_means_no_answers():
    assert memes.answers(None, {}, memes.APP_OPPORTUNITY) == {}
    assert memes.answers(_Jev(fail=True), {}, memes.APP_OPPORTUNITY) == {}
    assert memes.opportunity(_Jev({"build_now": 0.6}), {}) == 0.6


def test_tied_marks():
    assert appstore.tied({"own_app": 0.93, "one_place": 0.1}) == "自家应用"
    assert appstore.tied({"own_app": 0.2, "one_place": 0.7}) == "只限一地"
    assert appstore.tied({"own_app": 0.2, "one_place": 0.1}) == ""
    assert appstore.tied({"score": 0.8}) == ""   # read before 10-20: not asked


def test_jev_sees_who_made_the_app(monkeypatch):
    listing = {"results": [{"sellerName": "Derrimut 24:7 Gym Pty Ltd", "artistName": "Derrimut",
                            "description": "Book classes and check in at your local Derrimut 24:7 gym.  " * 30}]}
    monkeypatch.setattr(appstore, "_json", lambda url: listing)
    got = appstore.about({"id": "1", "home": "au", "artist": "Derrimut"})
    assert got["developer"] == "Derrimut 24:7 Gym Pty Ltd"
    assert got["description"].startswith("Book classes") and len(got["description"]) == appstore.ABOUT_CHARS
    assert appstore.about({"id": "com.x", "home": "us", "platform": "android"}) == {}


def test_lookup_failure_still_names_the_maker(monkeypatch):
    def down(url):
        raise OSError("timeout")
    monkeypatch.setattr(appstore, "_json", down)
    assert appstore._try_about({"id": "1", "home": "au", "artist": "Derrimut"}) == {"developer": "Derrimut"}


def test_own_and_one_place_apps_are_not_picks():
    rows = [{"term": "derrimut gym", "kinds": ["appstore"], "named": 0.79,
             "note": "②榜单 澳健康健美免费 #1(上架 21 天,1 个区上榜),自家应用"},
            {"term": "언제오나(지하철)", "kinds": ["appstore"], "named": 0.70, "tied": "只限一地", "note": "②榜单 韩生活付费 #8"},
            {"term": "2am cam", "kinds": ["appstore"], "named": 0.66, "note": "②榜单 德摄影录像付费 #8(上架 20 天,1 个区上榜)"}]
    picks = radar._app_picks({"recent_sources": {"rows": rows}})
    assert len(picks) == 1 and picks[0]["term"] == "2am cam" and picks[0]["text"].startswith("**2am cam**")


def test_table_shows_why_a_high_score_is_not_bold():
    assert appstore._score_cell({"score": 0.79, "own_app": 0.93}) == "0.79<br>自家应用"
    assert appstore._score_cell({"score": 0.66, "own_app": 0.1, "one_place": 0.1}) == "**0.66**"
    assert appstore._score_cell({}) == "—"

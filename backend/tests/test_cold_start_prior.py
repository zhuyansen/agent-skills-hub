from datetime import datetime

import httpx

from app.services.cold_start_prior import build_state, flatten, score_prior


def _row(readme="# Tool\nDoes a thing."):
    return {"repo_full_name": "a/b", "author_name": "a", "category": "mcp-server", "description": "d",
            "created_at": datetime(2026, 9, 1), "first_seen": datetime(2026, 9, 4, 12), "readme": readme}


def test_state_carries_age_and_strips_star_badges():
    readme = "# Tool\n[![Stars](https://img.shields.io/github/stars/a/b)](x)\nDoes a thing.\n"
    state = build_state(_row(readme))
    assert "3 day(s) after" in state and "Does a thing." in state
    assert "shields" not in state


def test_flatten_all_three_types():
    ans = {"n": {"type": "noul", "noul": 0.7},
           "s": {"type": "score", "score": 1.4},
           "c": {"type": "choice", "choice": "x", "probabilities": {"x": 0.6, "y": 0.4}}}
    assert flatten(ans) == {"n": 0.7, "s": 1.4, "c": "x", "c=x": 0.6, "c=y": 0.4}


def test_score_prior_retries_5xx_then_returns_model():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json={"model": "typesafe/jev-test",
                                         "answers": {"n": {"type": "noul", "noul": 0.5}}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        prior, model = score_prior(_row(), "k", client)
    assert model == "typesafe/jev-test" and prior == {"n": 0.5} and len(calls) == 2

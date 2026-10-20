import json
from datetime import datetime

import httpx

from app.services import cold_start_prior
from app.services.cold_start_prior import (DECISIONS_URL, MODEL, TYPESAFE_MODEL, TYPESAFE_URL, JevEndpoint,
                                           build_state, endpoint_from_env, flatten, score_prior)

OPENROUTER = JevEndpoint("openrouter", DECISIONS_URL, MODEL, "k")


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


def test_score_prior_retries_5xx_then_returns_model(monkeypatch):
    waits = []
    monkeypatch.setattr(cold_start_prior.time, "sleep", waits.append)
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json={"model": "typesafe/jev-test",
                                         "answers": {"n": {"type": "noul", "noul": 0.5}}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        prior, model = score_prior(_row(), OPENROUTER, client)
    assert model == "typesafe/jev-test" and prior == {"n": 0.5} and len(calls) == 2 and waits == [1]


def test_endpoint_prefers_typesafe_then_openrouter():
    both = endpoint_from_env({"TYPESAFE_API_KEY": "t", "OPENROUTER_API_KEY": "o"})
    assert (both.name, both.url, both.model, both.key) == ("typesafe", TYPESAFE_URL, TYPESAFE_MODEL, "t")
    assert endpoint_from_env({"OPENROUTER_API_KEY": "o"}).url == DECISIONS_URL
    assert endpoint_from_env({"TYPESAFE_API_KEY": "", "OPENROUTER_API_KEY": ""}) is None


def test_endpoint_repr_hides_the_key():
    assert "secret" not in repr(JevEndpoint("typesafe", TYPESAFE_URL, TYPESAFE_MODEL, "secret"))


def test_score_prior_posts_to_the_chosen_endpoint():
    seen = {}

    def handler(request):
        seen.update(url=str(request.url), auth=request.headers["authorization"],
                    body=json.loads(request.content))
        return httpx.Response(200, json={"model": "jev-x", "answers": {"n": {"type": "noul", "noul": 0.2}}})

    endpoint = endpoint_from_env({"TYPESAFE_API_KEY": "t"})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        score_prior(_row(), endpoint, client)
    assert seen["url"] == TYPESAFE_URL and seen["auth"] == "Bearer t"
    assert seen["body"]["model"] == "jev-latest" and "will_gain" in seen["body"]["questions"]

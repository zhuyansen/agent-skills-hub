"""ops/seo/keyword_pick.py: the parts that need no network."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("keyword_pick", Path(__file__).resolve().parents[2] / "ops/seo/keyword_pick.py")
kp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kp)


def test_page_traffic_weights_volume_by_position():
    text = "Keyword;Position;Search Volume;CPC\nfree seo tools ai;1;590;6.99\nai tools for website seo;3;390;0.00\nai seo tools;35;3600;15.79\n"
    assert kp.page_traffic(text) == round(590 * kp.CTR[1] + 390 * kp.CTR[3])      # position 35 is not counted
    assert kp.page_traffic("ERROR 50 :: NOTHING FOUND") is None


def test_potential_is_the_first_page_semrush_knows(monkeypatch):
    answers = iter(["ERROR 50 :: NOTHING FOUND", "Keyword;Position;Search Volume;CPC\nx;1;1000;0\n"])
    monkeypatch.setattr(kp.aisa, "call", lambda calls: ({"u": next(answers)}, 20000))
    found, cost = kp.potential(["https://github.com/a/b", "https://example.com/list", "https://third.example/"])
    assert found == {"tp": 276, "tp_page": "https://example.com/list", "tp_rank": 2} and cost == 40000


def test_semrush_top_reads_its_result_rows(monkeypatch):
    text = "Domain;Url;Keywords SERP Features;SERP Features\nwww.xda-developers.com;https://www.xda-developers.com/x/;6,7;6\nwww.reddit.com;https://www.reddit.com/r/y/;6;6\n"
    monkeypatch.setattr(kp.aisa, "call", lambda calls: ({"p": text}, 20000))
    assert kp.semrush_top("vibe coding tool") == (["https://www.xda-developers.com/x/", "https://www.reddit.com/r/y/"], 20000)


def test_first_page_forms():
    items = [{"url": "https://github.com/AgriciDaniel/claude-seo", "title": "claude-seo"},
             {"url": "https://www.youtube.com/watch?v=x", "title": "Claude SEO"},
             {"url": "https://nadiamohamed.me/x", "title": "Best MCP Servers for SEO in 2026: 5 Compared"},
             {"url": "https://mcp.so/tags/gsc", "title": "12 MCP Servers"},
             {"url": "https://www.reddit.com/r/SEO/x", "title": "Would an SEO MCP server be useful?"},
             {"url": "https://searchengineland.com/x", "title": "How to turn Claude Code into your SEO command center"},
             {"url": "https://writesonic.com/", "title": "Writesonic"}]
    assert [kp.form_of(i) for i in items] == ["repository", "video", "list", "directory", "forum", "tutorial", "tool or product"]
    assert kp.form_summary(items) == "榜单 1 · 目录 1 · 仓库 1 · 单个工具 1 · 教程 1 · 视频 1 · 论坛 1"


def test_model_scores_are_checked():
    text = 'Sure:\n[{"keyword": "seo mcp", "value": 3, "reason": "lists"}, {"keyword": "x", "value": 7}, {"keyword": "y"}]'
    assert kp.parse_values(text) == {"seo mcp": (3, "lists")}
    assert kp.parse_values("no json here") == {}


def test_owner_scores_win(monkeypatch, tmp_path):
    overrides = tmp_path / "o.json"
    overrides.write_text('{"seo skill": [3, "the first four results are Claude skills"]}')
    monkeypatch.setattr(kp, "OVERRIDES", overrides)
    monkeypatch.setattr(kp.aisa, "chat", lambda *a, **k: '[{"keyword": "seo skill", "value": 1, "reason": "career"}]')
    scored, model = kp.values([{"keyword": "seo skill", "first_page": []}])
    assert scored["seo skill"] == (3, "the first four results are Claude skills (owner)") and model == kp.VALUE_MODELS[0]


def test_an_understated_potential_is_marked():
    assert kp.understated({"traffic_potential": 76, "volume": 27100})
    assert not kp.understated({"traffic_potential": 1593, "volume": 480})
    assert not kp.understated({"traffic_potential": 2, "volume": 90})          # too few searches to judge
    table = kp.markdown({"rows": [{"keyword": "seo agent", "volume": 27100, "kd": 19, "intent": "commercial",
                                   "traffic_potential": 76, "tp_rank": 1, "value": 2, "form": "单个工具 6",
                                   "first": "https://www.tripledart.com/x", "tp_page": "https://www.tripledart.com/x",
                                   "value_reason": "mixed"}],
                         "cost": 22000, "model": "claude-sonnet-4-6", "errors": []})
    assert "| seo agent | 27,100 | 19 | commercial | 76 ⚠ | 2 |" in table and "$0.022" in table

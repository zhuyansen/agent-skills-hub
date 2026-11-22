"""定时任务运行状态 + API 渠道与余额 + 线上站点可用性监控（AgentSkillsHub 每日巡检）。

输出：ops/health/out/health.json
1. 检查本仓库全部定时任务（WORKFLOWS）最近一次完成状态，任何非 success/skipped 都进 alerts。
2. 检查核心外部 API 通道真实连通性与余额：
   - APIMart（FLATROUTER_API_KEY / gemini-4-hydrogen）：最小推理连通性 + /v1/balance 额度与累计已用
   - OpenRouter（OPENROUTER_API_KEY）：GET /api/v1/credits 剩余美元余额（< $2 告警）与周限额剩余
   - AIsa（AISA_API_KEY）：GET /v1/credits/balance 剩余美元余额（< $1 告警）
   - TypeSafe Jev（TYPESAFE_API_KEY）：POST /v1/systemone 微型选择题真推理探测（校验返回 answers）
3. 检查线上站点关键入口真实可用性（SITES）：首页 HTML、sitemap.xml、llms.txt 状态码、内容标记与延迟。
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests

CST = timezone(timedelta(hours=8))
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
REPO = os.environ.get("GITHUB_REPOSITORY") or "zhuyansen/agent-skills-hub"
MIN_AISA_USD = 1.0
MIN_OR_USD = 2.0

SITES = (
    {"id": "home", "label": "官网首页", "url": "https://agentskillshub.top/", "marker": "AgentSkillsHub"},
    {"id": "sitemap", "label": "sitemap.xml", "url": "https://agentskillshub.top/sitemap.xml", "marker": "<loc>"},
    {"id": "llms", "label": "llms.txt", "url": "https://agentskillshub.top/llms.txt", "marker": "AgentSkillsHub"},
)

WORKFLOWS = {
    "sync.yml": "技能库同步 (Sync)",
    "deploy.yml": "前端部署 (Pages)",
    "daily-skills-report.yml": "AgentSkillsHub 日报 Top 10",
    "daily-report.yml": "每日统计报告",
    "radar-daily.yml": "新词雷达 · 日报",
    "radar-source.yml": "新词雷达 · 源头巡检",
    "video-daily.yml": "专题页每日评测补充",
    "describe-en.yml": "英文卡片描述翻译",
    "sub-skills.yml": "子技能采集 (Sub-skills)",
    "readme-backfill.yml": "README 回填",
    "refresh-stale.yml": "旧技能刷新",
    "renamed-repos.yml": "改名仓库同步",
    "index-watch.yml": "Google 收录巡检",
    "seo-scoreboard.yml": "SEO 记分牌",
    "stripe-poll.yml": "Stripe 订单轮询",
    "github-traffic.yml": "GitHub 流量统计",
    "newsletter.yml": "周刊发送",
    "catalog-coverage.yml": "目录覆盖率检查",
    "page-check.yml": "页面死链巡检",
    "stats-monthly.yml": "月度统计",
}


def check_workflows() -> list[dict]:
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    headers = {"Accept": "application/vnd.github+json"}
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    out = []
    for wf, label in WORKFLOWS.items():
        try:
            r = requests.get(
                f"https://api.github.com/repos/{REPO}/actions/workflows/{wf}/runs?per_page=5",
                headers=headers,
                timeout=30,
            )
            r.raise_for_status()
            runs = r.json().get("workflow_runs") or []
            done = [x for x in runs if x.get("status") == "completed" and x.get("conclusion") != "cancelled"]
            in_prog = [x for x in runs if x.get("status") in ("in_progress", "queued")]
            last = done[0] if done else None
            at_cst = ""
            if last and last.get("created_at"):
                at_cst = (
                    datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
                    .astimezone(CST)
                    .strftime("%m-%d %H:%M")
                )
            out.append({
                "file": wf,
                "label": label,
                "conclusion": last and last.get("conclusion"),
                "at": at_cst,
                "url": last and last.get("html_url"),
                "running": bool(in_prog),
                "ok": (last and last.get("conclusion") in ("success", "skipped")) or (not last and bool(in_prog)),
            })
        except Exception as e:  # noqa: BLE001
            out.append({"file": wf, "label": label, "ok": False, "error": f"{type(e).__name__}: {e}"[:140]})
    return out


def check_channels() -> list[dict]:
    checks = []

    # 1. APIMart (FLATROUTER_API_KEY -> gemini-4-hydrogen)
    fr_key = (os.environ.get("FLATROUTER_API_KEY") or "").strip()
    fr_base = (os.environ.get("FLATROUTER_BASE_URL") or "https://api.apimart.ai/v1").rstrip("/")
    fr_model = (os.environ.get("FLATROUTER_MODEL") or "gemini-4-hydrogen").strip()
    if fr_key:
        try:
            t0 = time.monotonic()
            r = requests.post(
                f"{fr_base}/chat/completions",
                headers={"Authorization": f"Bearer {fr_key}"},
                json={"model": fr_model, "max_tokens": 8, "stream": False, "messages": [{"role": "user", "content": "hi"}]},
                timeout=45,
            )
            ms = round((time.monotonic() - t0) * 1000)
            ok = r.status_code == 200
            checks.append({
                "channel": "APIMart（主力 LLM）",
                "used_by": "日报 Top 10 + 专题卡片翻译",
                "status_text": f"{fr_model} 正常 ({ms}ms)" if ok else f"{fr_model} HTTP {r.status_code}",
                "latency_ms": ms,
                "ok": ok,
                "detail": "" if ok else r.text[:140],
            })
        except Exception as e:  # noqa: BLE001
            checks.append({"channel": "APIMart（主力 LLM）", "used_by": "日报 Top 10 + 专题卡片翻译",
                           "status_text": "连接失败", "ok": False, "detail": f"{type(e).__name__}: {e}"[:140]})
        try:
            rb = requests.get(f"{fr_base}/balance", headers={"Authorization": f"Bearer {fr_key}"}, timeout=30)
            d = rb.json() if rb.status_code == 200 else {}
            unlim = bool(d.get("unlimited_quota"))
            rem = float(d.get("remain_balance") or 0)
            used = float(d.get("used_balance") or 0)
            ok_b = rb.status_code == 200 and d.get("success") and (unlim or rem >= 1.0)
            txt = f"无限额度（累计已用 ${used:,.2f}）" if unlim else f"余额 ${rem:,.2f}（已用 ${used:,.2f}）"
            checks.append({
                "channel": "APIMart 额度",
                "used_by": "日报 Top 10 + 专题卡片翻译",
                "status_text": txt if rb.status_code == 200 else f"HTTP {rb.status_code}",
                "ok": bool(ok_b),
                "detail": "" if ok_b else rb.text[:140],
            })
        except Exception as e:  # noqa: BLE001
            checks.append({"channel": "APIMart 额度", "used_by": "日报 Top 10 + 专题卡片翻译",
                           "status_text": "查询失败", "ok": False, "detail": f"{type(e).__name__}: {e}"[:140]})

    # 2. OpenRouter (OPENROUTER_API_KEY)
    or_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if or_key:
        try:
            rc = requests.get("https://openrouter.ai/api/v1/credits", headers={"Authorization": f"Bearer {or_key}"}, timeout=30)
            rk = requests.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {or_key}"}, timeout=30)
            dc = (rc.json().get("data") or {}) if rc.status_code == 200 else {}
            dk = (rk.json().get("data") or {}) if rk.status_code == 200 else {}
            tot = float(dc.get("total_credits") or 0)
            used = float(dc.get("total_usage") or 0)
            rem = tot - used
            w_rem = dk.get("limit_remaining")
            w_txt = f" · 周限额剩 ${float(w_rem):,.2f}" if isinstance(w_rem, (int, float)) else ""
            ok = rc.status_code == 200 and rem >= MIN_OR_USD
            checks.append({
                "channel": "OpenRouter 余额",
                "used_by": "专题页 Jev 评测 / 翻译复核",
                "status_text": f"余额 ${rem:,.2f}（总充 ${tot:,.0f} / 已用 ${used:,.2f}{w_txt}）" if rc.status_code == 200 else f"HTTP {rc.status_code}",
                "ok": ok,
                "detail": "" if ok else (f"余额低于 ${MIN_OR_USD:.0f}，请及时充值" if rc.status_code == 200 else rc.text[:140]),
            })
        except Exception as e:  # noqa: BLE001
            checks.append({"channel": "OpenRouter 余额", "used_by": "专题页 Jev 评测 / 翻译复核",
                           "status_text": "查询失败", "ok": False, "detail": f"{type(e).__name__}: {e}"[:140]})

    # 3. AIsa (AISA_API_KEY)
    aisa_key = (os.environ.get("AISA_API_KEY") or "").strip()
    if aisa_key:
        try:
            ra = requests.get("https://api.aisa.one/v1/credits/balance", headers={"Authorization": f"Bearer {aisa_key}"}, timeout=30)
            micros = ra.json().get("available_balance_micros_usd") if ra.status_code == 200 else None
            usd = (micros / 1e6) if isinstance(micros, (int, float)) else None
            ok = ra.status_code == 200 and usd is not None and usd >= MIN_AISA_USD
            checks.append({
                "channel": "AIsa 余额",
                "used_by": "新词雷达 (X / YouTube 检索)",
                "status_text": f"余额 ${usd:,.2f}" if usd is not None else f"HTTP {ra.status_code}",
                "ok": ok,
                "detail": "" if ok else (f"余额低于 ${MIN_AISA_USD:.0f}，请及时充值" if usd is not None else ra.text[:140]),
            })
        except Exception as e:  # noqa: BLE001
            checks.append({"channel": "AIsa 余额", "used_by": "新词雷达 (X / YouTube 检索)",
                           "status_text": "查询失败", "ok": False, "detail": f"{type(e).__name__}: {e}"[:140]})

    # 4. TypeSafe Jev (TYPESAFE_API_KEY) — real inference probe via /v1/systemone
    ts_key = (os.environ.get("TYPESAFE_API_KEY") or "").strip()
    if ts_key:
        try:
            t0 = time.monotonic()
            rt = requests.post(
                "https://api.typesafe.ai/v1/systemone",
                headers={"Authorization": f"Bearer {ts_key}"},
                json={
                    "model": "jev-latest",
                    "state": "Card c1: Acme raised $5M in a closed seed round.",
                    "questions": {
                        "c1": {
                            "type": "choice",
                            "instructions": "What does c1 describe?",
                            "criteria": {"done": "A completed funding round", "rumor": "Only rumored"},
                        }
                    },
                },
                timeout=45,
            )
            ms = round((time.monotonic() - t0) * 1000)
            body = rt.json() if rt.status_code == 200 else {}
            ok = rt.status_code == 200 and isinstance(body, dict) and "answers" in body
            checks.append({
                "channel": "TypeSafe Jev 官方",
                "used_by": "新词雷达 + 专题页门禁评测",
                "status_text": f"jev-latest 推理正常 ({ms}ms)" if ok else (
                    "返回缺少 answers" if rt.status_code == 200 else f"HTTP {rt.status_code}"
                ),
                "latency_ms": ms,
                "ok": ok,
                "detail": "" if ok else rt.text[:140],
            })
        except Exception as e:  # noqa: BLE001
            checks.append({"channel": "TypeSafe Jev 官方", "used_by": "新词雷达 + 专题页门禁评测",
                           "status_text": "连接失败", "ok": False, "detail": f"{type(e).__name__}: {e}"[:140]})

    return checks


def check_sites() -> list[dict]:
    out = []
    for spec in SITES:
        url = spec["url"]
        marker = spec.get("marker", "")
        try:
            t0 = time.monotonic()
            r = requests.get(url, timeout=20, headers={"User-Agent": "AgentSkillsHub-HealthCheck/1.0"})
            ms = round((time.monotonic() - t0) * 1000)
            has_marker = (not marker) or (marker in r.text)
            ok = r.status_code == 200 and len(r.text.strip()) > 0 and has_marker
            if ok:
                detail = ""
                status_text = f"HTTP 200 ({ms}ms)"
            elif r.status_code != 200:
                status_text = f"HTTP {r.status_code}"
                detail = f"期望 200，实际 {r.status_code}"
            else:
                status_text = "内容标记缺失"
                detail = f"响应缺少预期内容 `{marker}`"
            out.append({
                "id": spec["id"],
                "label": spec["label"],
                "url": url,
                "status_code": r.status_code,
                "latency_ms": ms,
                "status_text": status_text,
                "ok": ok,
                "detail": detail,
            })
        except Exception as e:  # noqa: BLE001
            out.append({
                "id": spec["id"],
                "label": spec["label"],
                "url": url,
                "status_code": 0,
                "status_text": "连接失败",
                "ok": False,
                "detail": f"{type(e).__name__}: {e}"[:140],
            })
    return out


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    wfs = check_workflows()
    chs = check_channels()
    sites = check_sites()
    payload = {
        "fetched_at": datetime.now(CST).isoformat(timespec="seconds"),
        "workflows": wfs,
        "channels": chs,
        "sites": sites,
    }
    out_path = os.path.join(OUT_DIR, "health.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    bad_wf = [w["label"] for w in wfs if not w.get("ok")]
    bad_ch = [c["channel"] for c in chs if not c.get("ok")]
    bad_site = [s["label"] for s in sites if not s.get("ok")]
    print(
        f"✓ health check written to {out_path} "
        f"({len(wfs)} workflows, {len(chs)} channels, {len(sites)} sites, "
        f"bad_wf={len(bad_wf)}, bad_ch={len(bad_ch)}, bad_site={len(bad_site)})"
    )


if __name__ == "__main__":
    main()

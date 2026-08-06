import os
import subprocess

import requests
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./skills_hub.db"
    supabase_db_url: str = ""
    supabase_service_role_key: str = ""
    github_token: str = ""
    sync_interval_hours: int = 8
    cors_origins: str = "http://localhost:5173,http://localhost:3000,https://agentskillshub.top,https://www.agentskillshub.top"
    admin_token: str = ""

    # BillionMail newsletter integration
    billionmail_api_url: str = ""  # e.g. https://mail.yourdomain.com
    billionmail_api_key: str = ""

    # LLM API (optional — for LLM security analysis, Phase 2)
    # Supports OpenAI-compatible APIs: MiniMax, OpenAI, etc.
    llm_api_key: str = ""  # MiniMax API key
    llm_base_url: str = "https://api.minimax.chat/v1"  # MiniMax endpoint
    llm_model: str = "MiniMax-Text-01"  # Model name
    # Legacy — still checked for backward compat
    anthropic_api_key: str = ""

    # Resend email integration (recommended — free 3000 emails/month)
    resend_api_key: str = ""  # e.g. re_xxxxxxxx
    email_from: str = "Agent Skills Hub <noreply@agentskillshub.top>"
    site_url: str = "https://agentskillshub.top"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def _gh_cli_token() -> str:
    """Token from the `gh` CLI keychain, with the env override stripped.

    `gh` honours GH_TOKEN/GITHUB_TOKEN from the environment ahead of its own
    keychain. Since loading .env puts github_token into the environment, an
    expired .env token makes `gh auth token` echo that same dead token back —
    which is exactly how a stale credential survived undetected (2026-08-05).
    Stripping the override is what makes this a real second opinion.
    """
    clean = {k: v for k, v in os.environ.items()
             if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True,
                              text=True, env=clean, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _token_works(token: str) -> bool:
    if not token:
        return False
    try:
        return requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"Bearer {token}"}, timeout=15).ok
    except requests.RequestException:
        return False  # can't confirm it works → don't claim it does


def resolve_github_token(verify: bool = False) -> str:
    """Return a usable GitHub token, or raise with an actionable message.

    An expired token does not fail loudly — GitHub answers 401 and callers that
    only check for 404/200 tally it as "inconclusive", so a wholly broken run
    reads as a clean result. Any entry point doing real GitHub work should call
    this with verify=True so the failure surfaces at startup instead of as
    silently empty output.
    """
    configured = settings.github_token
    if not verify:
        return configured or _gh_cli_token()

    for label, token in (("GITHUB_TOKEN", configured),
                         ("gh CLI keychain", _gh_cli_token())):
        if _token_works(token):
            return token
        if token:
            print(f"[github] {label} rejected by GitHub (expired or revoked)")
    raise RuntimeError(
        "No working GitHub token. Update GITHUB_TOKEN in backend/.env "
        "(and the GITHUB_TOKEN repo secret if CI is affected), or run `gh auth login`."
    )

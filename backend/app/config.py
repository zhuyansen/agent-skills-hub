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

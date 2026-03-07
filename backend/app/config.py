from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./skills_hub.db"
    supabase_db_url: str = ""
    supabase_service_role_key: str = ""
    github_token: str = ""
    sync_interval_hours: int = 8
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    admin_token: str = ""

    # BillionMail newsletter integration
    billionmail_api_url: str = ""  # e.g. https://mail.yourdomain.com
    billionmail_api_key: str = ""

    # Resend email integration (recommended — free 3000 emails/month)
    resend_api_key: str = ""  # e.g. re_xxxxxxxx
    email_from: str = "Agent Skills Hub <noreply@agent-skills-hub.com>"
    site_url: str = "https://agent-skills-hub.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

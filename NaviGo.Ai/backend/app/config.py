import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Server & Networking
    app_env: str = Field(default="dev", alias="APP_ENV")
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")
    public_base_url: str = Field(default="http://localhost:8000", alias="PUBLIC_BASE_URL")
    allowed_origins: str = Field(
        default="http://localhost:8000,http://127.0.0.1:8000",
        alias="ALLOWED_ORIGINS"
    )

    # Supabase Credentials
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")

    # AI Providers
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    chatgpt_api_key: str = Field(default="", alias="CHATGPT_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    @property
    def effective_openai_api_key(self) -> str:
        return self.openai_api_key or self.chatgpt_api_key

    # External APIs
    ors_api_key: str = Field(default="", alias="ORS_API_KEY")

    # Cron & Background Jobs
    cron_secret: str = Field(default="navigo_local_cron_secret", alias="CRON_SECRET")
    enable_internal_scheduler: bool = Field(default=False, alias="ENABLE_INTERNAL_SCHEDULER")

    # Web Push (VAPID)
    vapid_public_key: str = Field(default="", alias="VAPID_PUBLIC_KEY")
    vapid_private_key: str = Field(default="", alias="VAPID_PRIVATE_KEY")
    vapid_claim_email: str = Field(default="admin@navigo.app", alias="VAPID_CLAIM_EMAIL")

    @property
    def cors_origins(self) -> List[str]:
        origins = [orig.strip() for orig in self.allowed_origins.split(",") if orig.strip()]
        if self.public_base_url and self.public_base_url not in origins:
            origins.append(self.public_base_url)
        return origins

    @property
    def is_demo_mode(self) -> bool:
        # If Supabase credentials or Gemini API key are absent, activate robust Demo Mode
        return not bool(self.supabase_url and self.supabase_anon_key)

    @property
    def is_ai_demo_mode(self) -> bool:
        return not bool(self.gemini_api_key or self.effective_openai_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()

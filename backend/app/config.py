from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULTS = {"change-me", "change-me-rpa", ""}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./buytiming.db"
    db_ssl_ca: str | None = None  # TiDB Cloud 등 TLS 필수 DB의 CA 파일 경로

    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60
    rpa_api_key: str = "change-me-rpa"
    admin_emails: str = ""  # 쉼표 구분, 가입 시 관리자 권한 부여

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    ai_daily_limit: int = 20

    allowed_origins: str = "*"  # 쉼표 구분 (예: https://buytiming.netlify.app)
    tz: str = "Asia/Seoul"
    frontend_dir: str | None = None  # 지정하면 API가 프런트엔드 정적 파일도 서빙 (Render 단독 풀스택)

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

    def validate_for_production(self) -> None:
        if self.app_env == "production":
            weak = [k for k in ("jwt_secret", "rpa_api_key") if getattr(self, k) in INSECURE_DEFAULTS]
            if weak:
                raise RuntimeError(f"운영 환경에서는 {', '.join(weak)} 값을 반드시 설정해야 합니다.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def now_local() -> datetime:
    """DB에는 서비스 기준 시간대(KST)의 naive datetime으로 저장한다."""
    return datetime.now(ZoneInfo(get_settings().tz)).replace(tzinfo=None)

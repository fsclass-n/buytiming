from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULTS = {"change-me", "change-me-rpa", ""}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./buytiming.db"
    db_ssl_ca: str | None = None  # 값이 있으면 TLS 접속(TiDB 필수). 파일이 없는 환경(Windows 로컬)은 certifi/OS 인증서로 검증

    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 60
    rpa_api_key: str = "change-me-rpa"
    admin_emails: str = ""  # 쉼표 구분, 가입 시 관리자 권한 부여

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    ai_daily_limit: int = 20

    allowed_origins: str = "*"  # 쉼표 구분 (예: https://buytiming.netlify.app)
    tz: str = "Asia/Seoul"
    # 프런트엔드 정적 파일 폴더. 비우면 저장소의 frontend/를 찾아 있으면(로컬) 서빙, 없으면(EC2 api 컨테이너) API만 제공
    frontend_dir: str | None = None

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

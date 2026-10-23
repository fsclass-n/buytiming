import os
import ssl
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def _ca_file(path: str) -> str | None:
    """DB_SSL_CA 파일이 있으면 그대로, 없으면(예: Windows 로컬) certifi 번들, 그것도 없으면 OS 기본 인증서 저장소"""
    if os.path.isfile(path):
        return path
    try:
        import certifi

        return certifi.where()
    except ImportError:
        return None


def connect_args(s: Settings) -> dict:
    if s.database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    if s.db_ssl_ca:
        # TiDB 등 TLS 필수 DB: 인증서·호스트 이름을 검증한다. 같은 .env를 컨테이너(Linux)와 Windows 로컬에서 함께 쓸 수 있다.
        return {"ssl": ssl.create_default_context(cafile=_ca_file(s.db_ssl_ca))}
    return {}


def _engine():
    s = get_settings()
    return create_engine(s.database_url, pool_pre_ping=True, pool_recycle=280, connect_args=connect_args(s))


engine = _engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  (모델 등록)

    Base.metadata.create_all(engine)

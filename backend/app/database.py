from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def _engine():
    s = get_settings()
    connect_args: dict = {}
    if s.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    elif s.db_ssl_ca:
        connect_args = {"ssl": {"ca": s.db_ssl_ca}}
    return create_engine(s.database_url, pool_pre_ping=True, pool_recycle=280, connect_args=connect_args)


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

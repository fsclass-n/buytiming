import os
import pathlib
import tempfile

import pytest

_TMP = pathlib.Path(tempfile.mkdtemp(prefix="buytiming-test-"))
# CI의 MySQL 통합 테스트는 TEST_DATABASE_URL로 지정, 기본은 임시 SQLite
os.environ.update({
    "DATABASE_URL": os.getenv("TEST_DATABASE_URL") or f"sqlite:///{(_TMP / 'test.db').as_posix()}",
    "JWT_SECRET": "test-secret",
    "RPA_API_KEY": "test-rpa-key",
    "GEMINI_API_KEY": "",
    "SEED_DEMO_PASSWORD": "demo-pass-1",
    "SEED_ADMIN_PASSWORD": "admin-pass-1",
    "APP_ENV": "test",
})

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402

RPA = {"X-RPA-KEY": "test-rpa-key"}


@pytest.fixture(scope="session")
def client():
    seed(reset=True)
    with TestClient(app) as c:
        yield c


def _token(client, email, pw):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def user_h(client):
    return _token(client, "demo@buytiming.demo", "demo-pass-1")


@pytest.fixture(scope="session")
def admin_h(client):
    return _token(client, "admin@buytiming.demo", "admin-pass-1")

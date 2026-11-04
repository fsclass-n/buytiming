"""Render·로컬 풀스택: API가 React 빌드 결과(SPA)를 같은 도메인으로 서빙"""


def test_serves_index(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"] and "js/config.js" in r.text
    assert r.headers["x-frame-options"] == "DENY"


def test_spa_routes_fall_back_to_index(client):
    """React Router 경로(/login, /product/3, /oauth/callback)는 index.html을 돌려준다"""
    for path in ("/login", "/product/3", "/admin/users", "/oauth/callback"):
        r = client.get(path)
        assert r.status_code == 200 and '<div id="root">' in r.text, path


def test_static_assets_and_missing_files(client):
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/missing.js").status_code == 404  # 확장자가 있는 파일은 실제 404


def test_config_js_uses_same_origin(client):
    r = client.get("/js/config.js")
    assert r.status_code == 200 and 'API_BASE_URL: "/"' in r.text and r.headers["cache-control"] == "no-cache"


def test_api_routes_take_precedence(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/users/me").json()["code"] == "UNAUTHORIZED"
    assert client.get("/openapi.json").status_code == 200

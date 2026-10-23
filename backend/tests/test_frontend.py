"""Render 단독 풀스택: API가 프런트엔드를 같은 도메인으로 서빙"""


def test_serves_frontend_pages(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"] and "js/config.js" in r.text
    assert client.get("/login.html").status_code == 200
    assert r.headers["x-frame-options"] == "DENY"


def test_config_js_uses_same_origin(client):
    r = client.get("/js/config.js")
    assert r.status_code == 200 and 'API_BASE_URL: "/"' in r.text and r.headers["cache-control"] == "no-cache"


def test_api_routes_take_precedence(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/users/me").json()["code"] == "UNAUTHORIZED"
    assert client.get("/openapi.json").status_code == 200


def test_unknown_page_returns_404(client):
    assert client.get("/no-such-page.html").status_code == 404

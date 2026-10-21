import base64

from conftest import RPA

API = "/api/v1/rpa"


def test_rpa_key_required(client):
    r = client.get(f"{API}/listings")
    assert r.status_code == 401 and r.json()["code"] == "INVALID_RPA_KEY"
    assert client.get(f"{API}/listings", headers={"X-RPA-KEY": "wrong"}).status_code == 401


def test_listings_include_last_price(client):
    items = client.get(f"{API}/listings", headers=RPA).json()["items"]
    assert len(items) >= 36 and all("last_price" in i for i in items)


def test_bulk_prices_create_target_alert(client, user_h):
    listings = [i for i in client.get(f"{API}/listings", headers=RPA).json()["items"] if i["model_no"] == "MF800-3"]
    # 시드: 데모 사용자가 분유(MF800-3)를 목표가 80,000원으로 관심 등록
    res = client.post(f"{API}/prices/bulk", headers=RPA,
                      json={"items": [{"listing_id": l["listing_id"], "price": 70000, "shipping_fee": 0} for l in listings] +
                                     [{"listing_id": 999999, "price": 1}]}).json()
    assert res["inserted"] == len(listings) and res["skipped"] == 1 and res["alerts_created"] >= 1
    alerts = client.get("/api/v1/alerts", headers=user_h).json()
    assert any(a["type"] == "TARGET_PRICE" and "분유" in a["message"] for a in alerts["items"])
    # 24시간 안에는 같은 목표가 알림을 다시 보내지 않는다
    again = client.post(f"{API}/prices/bulk", headers=RPA,
                        json={"items": [{"listing_id": l["listing_id"], "price": 69000} for l in listings]}).json()
    before = sum(a["type"] == "TARGET_PRICE" and "분유" in a["message"] for a in alerts["items"])
    after = sum(a["type"] == "TARGET_PRICE" and "분유" in a["message"]
                for a in client.get("/api/v1/alerts", headers=user_h).json()["items"])
    assert again["inserted"] == len(listings) and after == before
    assert client.post("/api/v1/alerts/read-all", headers=user_h).json()["updated"] >= 1


def test_public_prices_and_logs(client):
    r = client.put(f"{API}/public-prices", headers=RPA, json={"items": [
        {"model_no": "W2L12", "good_id": "G1", "price": 8800, "survey_date": "2026-10-20"},
        {"model_no": "NOPE", "good_id": "G2", "price": 1, "survey_date": "2026-10-20"}]}).json()
    assert r == {"saved": 1, "unmatched": 1}
    log = client.post(f"{API}/logs", headers=RPA, json={"job_name": "collect_prices", "status": "SUCCESS", "collected": 3,
                                                       "failed": 0, "started_at": "2026-10-21T10:00:00"})
    assert log.status_code == 201


def test_model_upload_and_weekly_report(client):
    bad = client.post(f"{API}/models", headers=RPA, json={"version": "x", "algorithm": "y", "artifact_b64": "@@@"})
    assert bad.status_code == 400
    up = client.post(f"{API}/models", headers=RPA, json={"version": "upload-test", "algorithm": "none",
                                                          "artifact_b64": base64.b64encode(b"x").decode(), "activate": False})
    assert up.status_code == 201 and up.json()["active"] is False
    rep = client.get(f"{API}/reports/weekly", headers=RPA)
    assert rep.status_code == 200 and rep.content[:2] == b"PK"  # xlsx(zip)
    assert client.post(f"{API}/train", headers=RPA).status_code == 202

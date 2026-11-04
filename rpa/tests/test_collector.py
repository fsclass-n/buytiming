from datetime import datetime

from bs4 import BeautifulSoup

from collector import jobs
from collector.config import Config
from collector.parsers import parse_price, parse_product
from collector.scheduler import due_jobs

HTML = """<div class="product-price"><span class="sale">129,000원</span></div><span class="delivery-fee">3,000원</span>"""
RULE = {"price": ".product-price .sale", "shipping": ".delivery-fee", "soldout": ".btn-soldout"}


def test_parse_price_formats():
    assert parse_price("1,290,000원~") == 1290000
    assert parse_price("12.9만원") == 129000
    assert parse_price("무료배송") == 0
    assert parse_price("") is None and parse_price(None) is None


def test_parse_product_and_soldout():
    assert parse_product(BeautifulSoup(HTML, "html.parser"), RULE) == {"price": 129000, "shipping_fee": 3000, "in_stock": True}
    sold = BeautifulSoup(HTML + '<button class="btn-soldout">품절</button>', "html.parser")
    assert parse_product(sold, RULE)["in_stock"] is False
    zero = BeautifulSoup('<div class="product-price"><span class="sale">0원</span></div>', "html.parser")
    assert parse_product(zero, RULE)["in_stock"] is False  # 0원 수집 방지


def test_clean_removes_outliers_and_duplicates():
    listings = {1: {"last_price": 100000}, 2: {"last_price": 100000}, 3: {"last_price": None}}
    rows = [{"listing_id": 1, "price": 99000, "shipping_fee": 0, "in_stock": True},
            {"listing_id": 1, "price": 98000, "shipping_fee": 0, "in_stock": True},
            {"listing_id": 2, "price": 10000, "shipping_fee": 0, "in_stock": True},
            {"listing_id": 3, "price": 5000, "shipping_fee": 0, "in_stock": True}]
    df = jobs.clean(rows, listings)
    assert sorted(df["listing_id"]) == [1, 3] and int(df.loc[df.listing_id == 1, "price"].iloc[0]) == 98000


def test_simulated_price_is_deterministic():
    l = {"listing_id": 5, "last_price": 100000, "last_shipping_fee": 3000}
    t = datetime(2026, 12, 1, 10)
    a, b = jobs.simulated_price(l, t), jobs.simulated_price(l, t)
    assert a == b and 98000 <= a["price"] <= 102000 and a["shipping_fee"] == 3000


def test_due_jobs():
    assert due_jobs(datetime(2026, 12, 7, 7, 0)) == ["collect", "report"]  # 월요일 07:00
    assert due_jobs(datetime(2026, 12, 8, 3, 0)) == ["collect", "train"]
    assert due_jobs(datetime(2026, 12, 8, 6, 0)) == ["collect", "public"]
    assert due_jobs(datetime(2026, 12, 8, 6, 30)) == []


def test_parse_public_json_and_xml():
    mapping = {"G1": "W2L12"}
    js = '{"response": {"body": {"items": {"item": [{"goodId": "G1", "goodPrice": "8800", "goodInspectDay": "20261020"}]}}}}'
    assert jobs.parse_public(js, mapping) == [{"model_no": "W2L12", "good_id": "G1", "price": 8800, "store_type": None,
                                               "survey_date": "2026-10-20"}]
    xml = "<response><body><items><item><goodId>G1</goodId><goodPrice>8700</goodPrice><goodInspectDay>20261021</goodInspectDay></item></items></body></response>"
    assert jobs.parse_public(xml, mapping)[0]["price"] == 8700


class FakeApi:
    def __init__(self, listings):
        self._l, self.posted, self.logs = listings, None, []

    def listings(self):
        return self._l

    def post_prices(self, items, at):
        self.posted = items
        return {"inserted": len(items)}

    def log(self, *a, **kw):
        self.logs.append((a, kw))


def test_collect_simulated_and_skips_unconfigured(monkeypatch):
    monkeypatch.setenv("SIMULATE_MALLS", "true")
    api = FakeApi([{"listing_id": 1, "mall": "쇼핑몰 A", "url": "https://mall-a.example.com/p/1", "last_price": 10000, "last_shipping_fee": 0},
                   {"listing_id": 2, "mall": "미등록몰", "url": "https://real-shop.test/p/2", "last_price": 10000, "last_shipping_fee": 0}])
    res = jobs.collect(Config(), api)
    assert res["inserted"] == 1 and res["skipped"] == 1 and api.posted[0]["listing_id"] == 1
    assert api.logs[0][0][0] == "collect_prices"


def test_naver_lowest_price_and_query():
    from collector import naver

    url = naver.search_url("무선 이어폰 X2")
    assert naver.is_naver(url) and naver.query_of(url) == "무선 이어폰 X2"
    p = naver.lowest_price([{"lprice": "0"}, {"lprice": "129000", "title": "<b>X2</b>"}])
    assert p["price"] == 129000 and p["in_stock"]
    assert naver.lowest_price([])["in_stock"] is False


def test_collect_uses_naver_api_when_configured(monkeypatch):
    from collector import naver

    monkeypatch.setenv("NAVER_CLIENT_ID", "id")
    monkeypatch.setenv("NAVER_CLIENT_SECRET", "secret")
    monkeypatch.setattr(naver, "fetch_price", lambda url, cid, sec, s=None: {"price": 9900, "shipping_fee": 0, "in_stock": True})
    api = FakeApi([{"listing_id": 3, "mall": "네이버쇼핑", "url": naver.search_url("생수"), "last_price": 9800, "last_shipping_fee": 0}])
    api.ensured = []
    api.ensure_listings = lambda **kw: api.ensured.append(kw) or {"created": 0}
    cfg = Config()
    monkeypatch.setattr(cfg.__class__, "request_interval_sec", 0, raising=False)
    res = jobs.collect(cfg, api)
    assert res["inserted"] == 1 and api.posted[0]["price"] == 9900 and api.ensured[0]["name"] == "네이버쇼핑"


def test_s3_upload_is_skipped_without_bucket():
    from collector import storage

    assert storage.upload("", "k", b"x", "text/plain") is None


def test_naver_search_keys_take_precedence(monkeypatch):
    monkeypatch.setenv("NAVER_CLIENT_ID", "login-id")
    monkeypatch.setenv("NAVER_SEARCH_CLIENT_ID", "search-id")
    monkeypatch.setenv("NAVER_SEARCH_CLIENT_SECRET", "search-secret")
    cfg = Config()
    assert cfg.naver_client_id == "search-id" and cfg.naver_enabled

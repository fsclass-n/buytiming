"""네이버 쇼핑 검색 OpenAPI (https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md)

수집 대상 URL 형식: https://search.shopping.naver.com/search/all?query=<검색어>
API 키(NAVER_CLIENT_ID / NAVER_CLIENT_SECRET)가 있을 때만 사용한다. 크롤링이 아니라 공식 API 호출이다.
"""
from urllib.parse import parse_qs, quote, urlparse

import requests

NAVER_HOST = "search.shopping.naver.com"
NAVER_MALL = {"name": "네이버쇼핑", "base_url": f"https://{NAVER_HOST}", "url_template": f"https://{NAVER_HOST}/search/all?query={{query}}"}
API_URL = "https://openapi.naver.com/v1/search/shop.json"


class NaverError(Exception):
    pass


def is_naver(url: str) -> bool:
    return urlparse(url).netloc == NAVER_HOST


def query_of(url: str) -> str:
    q = parse_qs(urlparse(url).query).get("query", [""])[0].strip()
    if not q:
        raise NaverError(f"검색어가 없는 네이버쇼핑 URL: {url}")
    return q


def search_url(query: str) -> str:
    return NAVER_MALL["url_template"].format(query=quote(query))


def lowest_price(items: list[dict]) -> dict:
    """검색 결과(정확도순) 첫 상품의 최저가 — 액세서리 등 관련 없는 저가 상품이 섞이는 것을 피한다"""
    for it in items:
        price = int(it.get("lprice") or 0)
        if price > 0:
            return {"price": price, "shipping_fee": 0, "in_stock": True, "title": it.get("title", ""), "link": it.get("link", "")}
    return {"price": 0, "shipping_fee": 0, "in_stock": False}


def fetch_price(url: str, client_id: str, client_secret: str, session: requests.Session | None = None) -> dict:
    s = session or requests.Session()
    r = s.get(API_URL, params={"query": query_of(url), "display": 5, "sort": "sim"},
              headers={"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}, timeout=10)
    if r.status_code != 200:
        raise NaverError(f"네이버 API 오류 {r.status_code}: {r.text[:120]}")
    return lowest_price(r.json().get("items", []))

"""상품 페이지 파싱 (쇼핑몰별 CSS 셀렉터는 malls.json으로 분리)"""
import re

from bs4 import BeautifulSoup


def parse_price(text: str | None) -> int | None:
    """'129,000원', '12.9만원', '무료', '3,000원~' 등 → 정수(원). 무료는 0"""
    if text is None:
        return None
    t = text.replace(",", "").replace(" ", "")
    if "무료" in t or t.lower() in {"free", "0"}:
        return 0
    if m := re.search(r"(\d+(?:\.\d+)?)만", t):
        return int(round(float(m.group(1)) * 10_000))
    m = re.search(r"(\d{2,})", t)
    return int(m.group(1)) if m else None


def parse_product(soup: BeautifulSoup, rule: dict) -> dict:
    """rule: {"price": "css", "shipping": "css"(선택), "soldout": "css"(선택)}"""
    price_el = soup.select_one(rule["price"])
    price = parse_price(price_el.get_text(strip=True) if price_el else None)
    ship_el = soup.select_one(rule["shipping"]) if rule.get("shipping") else None
    shipping = parse_price(ship_el.get_text(strip=True)) if ship_el else 0
    sold_out = bool(rule.get("soldout") and soup.select_one(rule["soldout"]))
    if price is None or price <= 0:
        sold_out = True  # 가격이 없거나 0원이면 품절로 처리 (BUG-04)
    return {"price": price or 0, "shipping_fee": shipping or 0, "in_stock": not sold_out}

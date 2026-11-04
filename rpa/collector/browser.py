"""JavaScript로 가격을 그리는 쇼핑몰용 Playwright 렌더링 (malls.json 규칙에 "render": "playwright")

브라우저(Chromium)는 rpa Docker 이미지에만 설치된다. 로컬에서 쓰려면: playwright install chromium
robots.txt 확인·요청 간격은 http.PoliteSession이 먼저 적용한다.
"""
from bs4 import BeautifulSoup


def render(url: str, user_agent: str, timeout_ms: int = 20_000, wait_for: str | None = None) -> BeautifulSoup:
    from playwright.sync_api import sync_playwright  # 필요한 경우에만 불러온다(무거운 의존성)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=user_agent)
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            if wait_for:
                page.wait_for_selector(wait_for, timeout=timeout_ms)
            return BeautifulSoup(page.content(), "html.parser")
        finally:
            browser.close()

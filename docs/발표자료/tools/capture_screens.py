"""공개 Netlify 데모만 캡처한다. 운영 API·회원 데이터는 사용하지 않는다."""
import json
import math
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "assets"
BASE = "https://picktiming.netlify.app"


def main():
    records = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1.5)

        def capture(name, locator=None, clip=None):
            page.evaluate("document.fonts.ready")
            page.screenshot(path=str(ASSETS / name), clip=clip) if clip else (
                locator or page.get_by_role("main")
            ).screenshot(path=str(ASSETS / name))
            records.append({"file": name, "url": page.url, "mode": "Netlify 브라우저 데모"})

        page.goto(BASE)
        expect(page.get_by_role("heading", name="가격을 비교하고,\n살 때를 발견하세요.")).to_be_visible()
        page.wait_for_load_state("networkidle")
        capture("home.png", page.locator(".hero-surface"))
        page.set_viewport_size({"width": 1440, "height": 1600})
        page.goto(BASE + "/product/1")
        expect(page.get_by_role("heading", name="구매 타이밍 신호등")).to_be_visible()
        page.wait_for_load_state("networkidle")
        chart = page.get_by_role("heading", name="가격의 흐름").locator("../..")
        grid = page.locator("main .grid.items-start")
        capture("product-chart.png", grid)
        # 원본 캡처의 차트·신호등 행만 자른다. 가격·문구·UI는 바꾸지 않는다.
        shot = Image.open(ASSETS / "product-chart.png")
        scale = shot.width / grid.bounding_box()["width"]
        height = max(chart.bounding_box()["height"], grid.locator("aside").bounding_box()["height"])
        shot.crop((0, 0, shot.width, math.ceil(height * scale))).save(ASSETS / "product-chart.png")
        page.get_by_role("button", name="목표가 알림", exact=True).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        capture("target-alert.png", page.get_by_role("dialog"))
        page.keyboard.press("Escape")
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.goto(BASE + "/watchlist")
        expect(page.get_by_role("heading", name="내 관심 상품")).to_be_visible()
        page.wait_for_load_state("networkidle")
        capture("watchlist.png")
        page.goto(BASE + "/signup")
        page.get_by_label("서비스 이용 안내에 동의합니다 (필수)").check()
        page.get_by_label("개인정보 처리 안내에 동의합니다 (필수)").check()
        page.get_by_role("button", name="동의하고 계속").click()
        capture("signup.png")
        page.goto(BASE + "/login")
        page.get_by_role("button", name="관리자 테스트").click()
        expect(page.get_by_role("link", name="관리자 센터")).to_be_visible()
        page.goto(BASE + "/admin/users")
        expect(page.get_by_role("table")).to_be_visible()
        capture("admin-users.png")
        browser.close()
    (ASSETS / "capture-manifest.json").write_text(json.dumps({
        "captured_at": datetime.now(UTC).isoformat(),
        "default_viewport": [1440, 1000], "product_viewport": [1440, 1600], "records": records,
        "notice": "실제 서비스 UI를 캡처했으며 상품·가격·계정은 명시된 데모 데이터이다.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

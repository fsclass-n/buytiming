"""데모 시연(03:00–09:00)을 Playwright로 녹화한다. 공개 데모·API 문서·GitHub 페이지만 사용하고 운영 데이터는 바꾸지 않는다.

출력: WORK/demo/*.webm, WORK/demo_marks.json(장면별 녹화 시작 오프셋, 초)
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from video_scenes import timeline

WORK = Path(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/pc06-00/AppData/Local/Temp/pt-video")
BASE = "https://picktiming.netlify.app"
RENDER = "https://picktiming.onrender.com"
DUR = {s["id"]: s["dur"] for s in timeline() if s["kind"] == "demo"}

OVERLAY = """
(() => {
  const css = `#pt-cursor{position:fixed;left:-100px;top:-100px;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;
    background:rgba(250,204,21,.35);border:2px solid rgba(250,204,21,.95);pointer-events:none;z-index:2147483647;transition:transform .12s}
    #pt-cursor.down{transform:scale(.7)}
    .pt-ring{position:fixed;width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;border:3px solid #facc15;pointer-events:none;
    z-index:2147483646;animation:ptring .6s ease-out forwards}@keyframes ptring{to{transform:scale(3.2);opacity:0}}
    .pt-hl{position:fixed;border:3px solid #22d3ee;border-radius:12px;box-shadow:0 0 14px rgba(34,211,238,.45);
    pointer-events:none;z-index:2147483645;opacity:0;transition:opacity .3s ease}
    main{min-height:100vh}`;
  const boot = () => {
    if (document.getElementById('pt-cursor')) return;
    const st = document.createElement('style'); st.textContent = css; document.documentElement.appendChild(st);
    const c = document.createElement('div'); c.id = 'pt-cursor'; document.documentElement.appendChild(c);
    addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', e => { c.classList.add('down'); const r = document.createElement('div'); r.className = 'pt-ring';
      r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px'; document.documentElement.appendChild(r); setTimeout(() => r.remove(), 700); }, true);
    addEventListener('mouseup', () => c.classList.remove('down'), true);
    // 앱 밖에서 Netlify가 덧붙인 배지만 숨긴다(앱 UI는 그대로).
    setInterval(() => { if (!location.host.includes('netlify')) return; for (const el of document.body ? document.body.children : [])
      if (el.id !== 'root' && !['SCRIPT', 'DIALOG', 'STYLE'].includes(el.tagName)) el.style.display = 'none'; }, 300);
  };
  window.__ptHL = (x, y, w, h, ms) => { const d = document.createElement('div'); d.className = 'pt-hl';
    Object.assign(d.style, {left: (x - 6) + 'px', top: (y - 6) + 'px', width: (w + 12) + 'px', height: (h + 12) + 'px'});
    document.documentElement.appendChild(d); requestAnimationFrame(() => requestAnimationFrame(() => { d.style.opacity = 1; }));
    setTimeout(() => { d.style.opacity = 0; setTimeout(() => d.remove(), 350); }, ms); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
"""


class Director:
    def __init__(self, page):
        self.page, self.t0, self.marks, self.x, self.y = page, time.monotonic(), {}, 960, 540

    def wait(self, sec):
        time.sleep(sec)

    def nav(self, path, settle=1.0):
        """앱 안에서 주소만 바꿔 이동한다. 전체 새로고침의 흰 화면 깜박임을 막는다."""
        self.page.evaluate("p => { history.pushState({}, '', p); dispatchEvent(new PopStateEvent('popstate')); scrollTo(0, 0); }", path)
        self.page.wait_for_load_state("networkidle")
        self.wait(settle)

    def move(self, target, pause=.7):
        if isinstance(target, tuple):
            x, y = target
        else:
            target.scroll_into_view_if_needed()
            b = target.bounding_box()
            x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        self.page.mouse.move(x, y, steps=22)
        self.x, self.y = x, y
        self.wait(pause)

    def click(self, loc, pause=.6):
        self.move(loc, .8)
        loc.click()
        self.wait(pause)

    def hl(self, loc, ms=2600, pad_wait=True):
        # 강조 상자는 연출용이므로 대상을 못 찾으면 경고만 남기고 장면을 계속한다.
        try:
            loc.first.scroll_into_view_if_needed(timeout=4000)
            b = loc.first.bounding_box(timeout=4000)
        except Exception as exc:
            print("[warn] highlight skipped:", str(exc).splitlines()[0][:120])
            b = None
        if b:
            self.page.evaluate("([x,y,w,h,ms]) => window.__ptHL(x,y,w,h,ms)", [b["x"], b["y"], b["width"], min(b["height"], 1000), ms])
        if pad_wait:
            self.wait(ms / 1000 * .55)

    def scroll(self, dy, steps=8):
        for _ in range(steps):
            self.page.mouse.wheel(0, dy / steps)
            self.wait(.06)
        self.wait(.5)

    def scene(self, sid, fn, pre=None):
        if pre:
            pre()
        start = time.monotonic()
        self.marks[sid] = round(start - self.t0, 3)
        fn()
        used = time.monotonic() - start
        if used > DUR[sid]:
            print(f"[warn] {sid} used {used:.1f}s > {DUR[sid]}s")
        self.wait(max(0, DUR[sid] - used))


def run():
    try:
        urllib.request.urlopen(RENDER + "/health", timeout=120).read()  # 콜드 스타트 해소
    except Exception as exc:
        print("[warn] Render health:", exc)
    run_id = subprocess.check_output(["gh", "run", "list", "--branch", "main", "--workflow", "deploy.yml", "--status", "success",
                                      "--limit", "1", "--json", "databaseId", "--jq", ".[0].databaseId"], text=True).strip()
    (WORK / "demo").mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=str(WORK / "demo"),
                                  record_video_size={"width": 1920, "height": 1080}, locale="ko-KR")
        ctx.add_init_script(OVERLAY)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        d = Director(page)
        page.goto(BASE)
        expect(page.get_by_role("heading", name="가격을 비교하고,\n살 때를 발견하세요.")).to_be_visible()
        page.wait_for_load_state("networkidle")
        d.wait(1.5)

        def d01():
            d.move((960, 300), .5)
            d.hl(page.get_by_text("PickTiming 체험 공간 · 상품과 가격은 데모 데이터입니다"), 3500)
            d.move(page.get_by_role("search", name="메인 상품 검색").get_by_role("searchbox"), 1.5)

        def d02():
            sec = page.locator("#discover")
            d.move((960, 700), .3)
            d.scroll(620)
            d.hl(sec.get_by_role("heading", name="오늘, 눈여겨볼 가격"), 2200)
            d.hl(sec.locator("article").first, 3500)

        def d03():
            d.nav("/signup")
            d.wait(1)
            d.click(page.get_by_label("서비스 이용 안내에 동의합니다 (필수)"), .4)
            d.click(page.get_by_label("개인정보 처리 안내에 동의합니다 (필수)"), .4)
            d.click(page.get_by_role("button", name="동의하고 계속"), 1)
            d.hl(page.get_by_role("main").locator("ol").first, 2500)
            d.click(page.get_by_role("button", name="디지털", exact=True), 1)

        def d04():
            d.nav("/login")
            d.wait(1.2)
            d.hl(page.get_by_role("button", name="일반 사용자 테스트"), 1800)
            d.click(page.get_by_role("button", name="일반 사용자 테스트"), .5)
            expect(page.get_by_role("button", name="로그아웃").first).to_be_visible()
            d.hl(page.get_by_role("button", name="로그아웃").first, 2000)

        def d05():
            d.nav("/search")
            box = page.get_by_role("search", name="결과 내 상품 검색").get_by_role("searchbox")
            d.click(box, .3)
            box.type("이어폰", delay=140)
            d.click(page.get_by_role("search", name="결과 내 상품 검색").get_by_role("button"), 1.2)
            d.click(page.get_by_label("검색 카테고리").get_by_role("button", name="디지털", exact=True), 1)
            d.click(page.get_by_label("지금 구매 추천만"), 1)
            d.hl(page.get_by_text("지금 구매 추천만").locator("../.."), 2600)
            d.hl(page.get_by_role("heading", name="무선 이어폰 X2", exact=True).locator("xpath=ancestor::article[1]"), 3000)

        def d06():
            d.click(page.get_by_role("heading", name="무선 이어폰 X2", exact=True), 1.5)
            d.hl(page.get_by_text("배송비 포함 현재 최저가").locator(".."), 3200)
            for n in ("90일", "30일", "7일"):
                d.click(page.get_by_role("button", name=n, exact=True), 1.6)
            chart = page.get_by_role("img", name="가격 변동 차트")
            chart.scroll_into_view_if_needed()
            b = chart.bounding_box()
            for f in (.15, .4, .65, .9):
                d.move((b["x"] + b["width"] * f, b["y"] + b["height"] * .55), .6)
            table = page.get_by_role("heading", name="쇼핑몰별 실구매가")
            d.move((960, 800), .2)
            d.scroll(520)
            d.hl(table.locator("..").locator("table"), 4200)

        def d07():
            d.scroll(-520)
            d.hl(page.get_by_role("heading", name="구매 타이밍 신호등").locator(".."), 3500)
            d.click(page.get_by_role("button", name="AI 구매 조언", exact=True), .8)
            d.click(page.get_by_role("button", name="구매 조언 받기"), 1)
            expect(page.get_by_text("규칙 기반 분석", exact=True)).to_be_visible()
            d.hl(page.get_by_role("heading", name="내 구매를 위한 한 줄 조언").locator(".."), 5200)

        def d08():
            page.evaluate("scrollTo({top: 0, behavior: 'smooth'})")
            d.wait(1)
            d.click(page.get_by_role("link", name="AI와 상담하기"), 1.5)
            d.click(page.get_by_role("button", name="어느 쇼핑몰이 제일 싸?"), 1)
            expect(page.get_by_role("log")).to_contain_text("실구매가")
            d.hl(page.get_by_role("log"), 4200)

        def d09():
            d.nav("/product/1")
            d.wait(1.3)
            d.click(page.get_by_role("button", name="목표가 알림", exact=True).first, 1)
            field = page.get_by_role("dialog").get_by_label("목표 가격 (원)")
            d.click(field, .3)
            field.fill("")
            field.type("115000", delay=120)
            d.click(page.get_by_role("dialog").get_by_role("button", name="알림 저장"), .8)
            d.hl(page.get_by_role("dialog").get_by_text("목표가 알림이 저장되었습니다."), 2200)
            page.keyboard.press("Escape")
            d.nav("/watchlist")
            d.wait(1)
            d.hl(page.get_by_text("115,000원", exact=True).locator("xpath=ancestor::article[1]"), 3000)

        def d10():
            d.nav("/alerts")
            d.wait(1)
            d.hl(page.get_by_role("main").locator("ul, ol").first, 2600)
            d.click(page.get_by_role("button", name="모두 읽음"), 1)

        def d11():
            d.nav("/admin")
            heading = page.get_by_role("heading", name="관리자 전용 화면입니다")
            expect(heading).to_be_visible()
            d.wait(.6)
            d.move(heading, .3)
            d.hl(heading.locator(".."), 4500)

        def d12():
            d.click(page.get_by_role("button", name="로그아웃").first, .8)
            d.nav("/login")
            d.wait(.8)
            d.click(page.get_by_role("button", name="관리자 테스트"), .8)
            center = page.get_by_role("link", name="관리자 센터")
            expect(center).to_be_visible()
            d.hl(center, 2200)
            d.click(center, 1)

        def d13():
            expect(page.get_by_role("heading", name="관리자 · 수집·모델")).to_be_visible()
            d.wait(1)
            d.hl(page.get_by_text("오늘 수집 실행").locator("xpath=ancestor::div[contains(@class,'grid')][1]"), 4500)
            d.hl(page.get_by_role("heading", name="최근 7일 수집").locator(".."), 4500)
            d.hl(page.get_by_role("heading", name="모델 버전").locator(".."), 5500)
            d.move((960, 700), .2)
            d.scroll(600)
            d.hl(page.get_by_role("heading", name="작업 로그").locator(".."), 4500)

        def d14():
            page.evaluate("scrollTo({top: 0})")
            d.click(page.get_by_role("link", name="AI 사용량"), 1.2)
            expect(page.get_by_role("heading", name="관리자 · AI 사용량")).to_be_visible()
            d.hl(page.get_by_text("7일 호출 수").locator("xpath=ancestor::div[contains(@class,'grid')][1]"), 3500)
            d.hl(page.get_by_text("검증 실패율").locator("xpath=ancestor::div[contains(@class,'card') or contains(@class,'rounded')][1]"), 3500)
            d.hl(page.get_by_role("heading", name="평균 응답 시간 (목표 3초)").locator(".."), 3500)
            d.move((960, 700), .2)
            d.scroll(560)
            d.hl(page.get_by_role("heading", name="최근 호출").locator(".."), 3800)

        def d15():
            page.evaluate("scrollTo({top: 0})")
            d.click(page.get_by_role("link", name="회원 관리"), 1)
            expect(page.get_by_role("heading", name="관리자 · 회원 관리")).to_be_visible()
            box = page.get_by_label("회원 검색")
            d.click(box, .3)
            box.type("demo", delay=150)
            page.keyboard.press("Enter")
            d.wait(1.2)
            d.click(page.get_by_label("권한 필터"), .3)
            page.get_by_label("권한 필터").select_option("USER")
            d.wait(1.2)
            d.hl(page.get_by_role("table"), 2600)
            d.click(page.get_by_role("button", name="관리자로").first, .3)
            msg = page.get_by_text("조회만 가능").last
            expect(msg).to_be_visible()
            d.hl(msg, 5000)

        def d16_pre():
            page.goto(RENDER + "/docs")
            page.wait_for_selector(".opblock", timeout=90000)
            page.wait_for_load_state("networkidle")
            d.wait(1.5)

        def d16():
            d.wait(.8)
            d.hl(page.locator(".opblock-tag-section").first, 2600)
            d.move((960, 700), .2)
            for _ in range(3):
                d.scroll(700)
            d.hl(page.locator(".opblock-tag-section").nth(2), 2400)

        def d17_pre():
            page.goto(f"https://github.com/fsclass-n/picktiming/actions/runs/{run_id}")
            page.wait_for_load_state("networkidle")
            d.wait(1.5)

        def d17():
            d.wait(.8)
            jobs = page.get_by_text("ci / Backend (pytest on MySQL 8)").first
            try:
                d.hl(jobs.locator("xpath=ancestor::ul[1]"), 4200)
            except Exception:
                d.move((300, 520), 2)
            d.move((960, 560), 2)

        for sid, fn in [("D01", d01), ("D02", d02), ("D03", d03), ("D04", d04), ("D05", d05), ("D06", d06), ("D07", d07),
                        ("D08", d08), ("D09", d09), ("D10", d10), ("D11", d11), ("D12", d12), ("D13", d13), ("D14", d14),
                        ("D15", d15), ("D16", d16), ("D17", d17)]:
            d.scene(sid, fn, {"D16": d16_pre, "D17": d17_pre}.get(sid))
        video = page.video
        ctx.close()
        browser.close()
        (WORK / "demo_marks.json").write_text(json.dumps({"video": str(video.path()), "marks": d.marks}, indent=1), encoding="utf-8")
        print("recorded", video.path())


if __name__ == "__main__":
    run()

"""10분 발표·시연 영상의 장면 정의(단일 기준). 대본·가이드·자막·영상이 모두 이 파일을 사용한다.

시간 단위는 초. kind: slide(PPT 슬라이드 이미지) / demo(브라우저 녹화).
hl: 슬라이드 강조 사각형(인치, 13.333×7.5 기준) 목록. 여러 개면 장면 시간을 나눠 순서대로 표시한다.
"""

PARTS = {"ppt": "① PPT 발표", "switch": "② 화면 전환", "user": "③ 일반 회원 시연", "admin": "④ 관리자 시연", "close": "⑤ 클로징"}

SCENES = [
    # ---------------- ① PPT 00:00–03:00 (18장 중 1~16장)
    dict(id="P01", part="ppt", kind="slide", slide=1, dur=10, screen="PPT 1장 표지", action="슬라이드 쇼 시작",
         say="안녕하세요, 3조 조장 박미금입니다. 구매 타이밍 추천 플랫폼, 픽타이밍을 소개합니다.",
         fx="팀원 역할 칩 4개 하이라이트", hl=[(.6, 4.2, 6.45, 1.02)]),
    dict(id="P02", part="ppt", kind="slide", slide=2, dur=10, screen="PPT 2장 한눈에 보기", action="다음 장",
         say="코드 사천여 줄, API 서른네 개, 자동 검사 일흔한 개 규모의 프로젝트입니다.",
         fx="숫자 카드 4개 강조", hl=[(.55, 1.67, 12.25, 1.6)]),
    dict(id="P03", part="ppt", kind="slide", slide=3, dur=14, screen="PPT 3장 팀 구성", action="다음 장",
         say="저는 PM과 데이터·AI를, 김모란은 백엔드와 배포, 이오리는 화면, 홍기흥은 가격 수집을 맡았습니다.",
         fx="담당자 카드를 순서대로 강조", hl=[(.55 + i * 3.08, 1.67, 3.02, 4.55) for i in range(4)]),
    dict(id="P04", part="ppt", kind="slide", slide=4, dur=9, screen="PPT 4장 문제·요구사항·제약", action="다음 장",
         say="가격은 판매처마다 다르고 매일 바뀝니다. 무료 서버 같은 제약도 함께 풀었습니다.",
         fx="‘제약 조건’ 카드 강조", hl=[(8.75, 1.67, 4.05, 5.05)]),
    dict(id="P05", part="ppt", kind="slide", slide=5, dur=14, screen="PPT 5장 아키텍처", action="다음 장",
         say="화면은 리액트, 서버는 FastAPI, 데이터는 TiDB에 저장합니다. 수집 로봇과 AI는 서버를 통해서만 연결됩니다.",
         fx="SPA → FastAPI → TiDB 강조", hl=[(.55, 1.8, 8.9, 1.65), (3.4, 1.8, 3.1, 2.75)]),
    dict(id="P06", part="ppt", kind="slide", slide=6, dur=12, screen="PPT 6장 기술 선택", action="다음 장",
         say="기술마다 고른 이유와 대가를 정리했습니다. 무료 서버 한계 때문에 수집은 따로 예약 실행합니다.",
         fx="‘배포’ 행 강조", hl=[(.55, 2.07, 12.25, 4.65), (.55, 5.92, 12.25, .77)]),
    dict(id="P07", part="ppt", kind="slide", slide=7, dur=10, screen="PPT 7장 데이터 파이프라인", action="다음 장",
         say="가격이 들어오면 저장, 점수 계산, 알림까지 한 번에 처리합니다.",
         fx="①~⑥ 단계 강조", hl=[(.55, 1.8, 12.25, 2.2)]),
    dict(id="P08", part="ppt", kind="slide", slide=8, dur=12, screen="PPT 8장 [박미금] 적기 판정", action="다음 장",
         say="점수는 칠 일 안에 내려갈 가능성과 구십 일 중 현재 가격 위치로 계산하고, 시간 순서로 검증합니다.",
         fx="산식 박스 강조", hl=[(.55, 1.67, 6.2, 1.2), (6.9, 1.67, 5.9, 3.4)]),
    dict(id="P09", part="ppt", kind="slide", slide=9, dur=12, screen="PPT 9장 [박미금] LLM 검증", action="다음 장",
         say="AI 답변 속 숫자가 입력과 다르면 다시 요청하고, 그래도 틀리면 정해진 설명으로 바꿉니다.",
         fx="‘숫자 대조’ 단계 강조", hl=[(5.45, 1.75, 2.3, 1.45), (.55, 3.35, 6.6, 3.4)]),
    dict(id="P10", part="ppt", kind="slide", slide=10, dur=11, screen="PPT 10장 [김모란] API·무결성", action="다음 장",
         say="이 부분은 김모란이 맡았습니다. 인증을 역할별로 나눴고, 같은 시간대 가격은 한 번만 저장합니다.",
         fx="인증 분리 → 멱등 적재 코드 강조", hl=[(.55, 1.67, 6.0, 2.45), (6.65, 1.67, 6.15, 4.0)]),
    dict(id="P11", part="ppt", kind="slide", slide=11, dur=9, screen="PPT 11장 [김모란] CI/CD", action="다음 장",
         say="코드를 올리면 테스트가 돌고, 바뀐 부분만 배포됩니다.",
         fx="변경 경로 → 배포 대상 표 강조", hl=[(.55, 3.67, 6.1, 2.65)]),
    dict(id="P12", part="ppt", kind="slide", slide=12, dur=9, screen="PPT 12장 [이오리] 프런트엔드", action="다음 장",
         say="이오리가 맡은 화면은 데모와 운영이 같은 코드를 쓰고, 모바일까지 검사했습니다.",
         fx="설계 포인트 카드 강조", hl=[(6.95, 1.7, 5.85, 2.65)]),
    dict(id="P13", part="ppt", kind="slide", slide=13, dur=9, screen="PPT 13장 [홍기흥] RPA", action="다음 장",
         say="홍기흥의 수집기는 허용된 페이지만, 삼 초 간격으로, 실패하면 다시 시도합니다.",
         fx="수집기 코드 강조", hl=[(.55, 1.67, 6.5, 4.2)]),
    dict(id="P14", part="ppt", kind="slide", slide=14, dur=13, screen="PPT 14장 문제 해결 사례", action="다음 장",
         say="두 수집기의 중복 저장, AI의 틀린 숫자 같은 문제를 원인부터 찾아 테스트로 막았습니다.",
         fx="사례 카드 강조", hl=[(6.7, 1.67, 6.1, 2.5), (.55, 4.22, 6.1, 2.5)]),
    dict(id="P15", part="ppt", kind="slide", slide=15, dur=9, screen="PPT 15장 테스트와 품질", action="다음 장",
         say="백엔드 쉰한 건, 수집기 열한 건, 화면 시나리오 아홉 개를 통과했습니다.",
         fx="테스트 3단 강조", hl=[(.55, 1.75, 10.5, 2.95)]),
    dict(id="P16", part="ppt", kind="slide", slide=16, dur=7, screen="PPT 16장 실제 동작하는 서비스", action="다음 장",
         say="이제 실제 화면으로 직접 보여 드리겠습니다.", fx="화면 6개 강조", hl=[(.55, 1.67, 12.25, 4.75)]),
    dict(id="P16b", part="switch", kind="slide", slide=16, dur=10, screen="PPT 16장 → 브라우저", action="말 없이 전환(마지막 0.5초 페이드)",
         say="", fx="페이드 전환", hl=[]),
    # ---------------- ②~④ 시연 03:00–09:00 (Netlify 데모 → Render API 문서 → GitHub Actions)
    dict(id="D01", part="switch", kind="demo", dur=15, screen="Netlify 홈 · 데모 배너", action="상단 배너에 커서 정지",
         say="지금부터 실제 화면입니다. 운영 데이터를 건드리지 않도록, 상단 안내처럼 데모 데이터로 시연하겠습니다.",
         fx="데모 배너 하이라이트"),
    dict(id="D02", part="switch", kind="demo", dur=15, screen="Netlify 홈 · 추천 상품", action="검색창 → ‘오늘, 눈여겨볼 가격’ 스크롤",
         say="홈에서는 지금 사기 좋은 상품과 최근 내려간 상품을 보여 줍니다. 미리 계산해 둔 점수를 바로 읽어 옵니다.",
         fx="추천 카드 하이라이트"),
    dict(id="D03", part="user", kind="demo", dur=15, screen="/signup 회원가입 3단계", action="필수 약관 2개 체크 → 동의하고 계속 → 관심 카테고리 ‘디지털’ "
                                                                                       "(제출 안 함)",
         say="가입은 세 단계입니다. 약관에 동의하고 관심 품목을 고르면, 첫 가격 알림까지 이어집니다.",
         fx="단계 표시줄 하이라이트"),
    dict(id="D04", part="user", kind="demo", dur=15, screen="/login 로그인", action="‘일반 사용자 테스트’ 클릭",
         say="이제 일반 회원으로 로그인하겠습니다. 이메일과 소셜 로그인도 같은 화면에서 쓸 수 있습니다.",
         fx="일반 사용자 테스트 버튼 클릭 링"),
    dict(id="D05", part="user", kind="demo", dur=25, screen="/search 상품 탐색", action="‘이어폰’ 검색 → ‘디지털’ → ‘지금 구매 추천만’ → 정렬 확인",
         say="이어폰을 검색하고, 디지털 카테고리와 지금 구매 추천만 골라 보겠습니다. 점수 순으로 정렬해서 지금 사기 좋은 "
             "상품이 위에 옵니다. 검색과 필터는 서버 API 한 곳에서 처리합니다.",
         fx="필터 영역 하이라이트"),
    dict(id="D06", part="user", kind="demo", dur=40, screen="상품 상세 · 무선 이어폰 X2", action="실구매가 → 90일·30일·7일 → 차트 위 이동 → 판매처 비교 표",
         say="상품 상세입니다. 이 가격은 판매가에 배송비까지 더한 실구매가입니다. 기간을 구십 일, 삼십 일, 칠 일로 바꾸면 가격 흐름이 바로 바뀝니다. 아래 표에서는 "
             "쇼핑몰마다 판매가와 배송비, 실구매가를 한눈에 비교합니다. 가격 기록에 이 세 값을 함께 저장해 두었기 때문입니다.",
         fx="실구매가·기간 버튼·차트·배송비 열 하이라이트"),
    dict(id="D07", part="user", kind="demo", dur=25, screen="상품 상세 · 신호등 · AI 구매 조언", action="신호등 점수 → ‘AI 구매 조언’ 탭 → ‘구매 조언 받기’",
         say="오른쪽 신호등은 하락 가능성과 현재 가격 위치로 계산한 점수입니다. 조언 받기를 누르면 근거를 쉬운 말로 "
             "설명합니다. 실제 서버에서는 제미나이 답변의 숫자를 한 번 더 검증합니다.",
         fx="점수·‘규칙 기반 분석’ 배지 하이라이트"),
    dict(id="D08", part="user", kind="demo", dur=20, screen="AI 상담", action="‘AI와 상담하기’ → 추천 질문 ‘어느 쇼핑몰이 제일 싸?’",
         say="궁금한 점은 바로 물어볼 수 있습니다. 어느 쇼핑몰이 제일 싼지 물으면 실구매가로 답합니다. 하루 사용 횟수도 관리합니다.",
         fx="답변 말풍선·남은 횟수 하이라이트"),
    dict(id="D09", part="user", kind="demo", dur=20, screen="목표가 알림 → 내 관심 상품", action="‘목표가 알림’ → 목표가 입력 → ‘알림 저장’ → 관심 상품",
         say="바로 사지 않을 때는 원하는 가격을 목표가로 등록해 둡니다. 저장하면 내 관심 상품에서 확인할 수 있습니다.",
         fx="저장 완료 문구·목표가 하이라이트"),
    dict(id="D10", part="user", kind="demo", dur=10, screen="/alerts 가격 알림", action="‘모두 읽음’ 클릭",
         say="목표가에 도달하거나 판정이 바뀌면, 이렇게 알려 드립니다.", fx="알림 목록 하이라이트"),
    dict(id="D11", part="user", kind="demo", dur=10, screen="/admin (일반 회원)", action="주소창에 /admin 이동",
         say="일반 회원이 관리자 화면에 들어가면, 이렇게 막힙니다.", fx="‘관리자 전용 화면입니다’ 하이라이트"),
    dict(id="D12", part="admin", kind="demo", dur=15, screen="/login → 관리자 센터", action="‘로그아웃’ → ‘관리자 테스트’ → ‘관리자 센터’",
         say="이번에는 관리자로 로그인하겠습니다. 관리자에게만 관리자 센터 메뉴가 보입니다.", fx="관리자 센터 메뉴 하이라이트"),
    dict(id="D13", part="admin", kind="demo", dur=40, screen="관리자 · 수집 현황", action="지표 카드 → 7일 수집 차트 → 모델 버전 표 → 작업 로그",
         say="수집 현황입니다. 수집 로봇이 한 시간마다 가격을 모으고, 성공과 실패가 작업 로그에 남습니다. 모델 버전 표에서 학습한 모델을 비교하는데, 새 모델은 "
             "성능이 같거나 좋을 때만 교체됩니다. 화면 숫자는 데모 데이터라서, 이런 지표를 본다는 의미로 봐 주세요.",
         fx="지표 카드·모델 표 하이라이트, 자막 ‘데모 수치’"),
    dict(id="D14", part="admin", kind="demo", dur=30, screen="관리자 · AI 사용량", action="지표 카드 5개 → 응답 시간 차트 → 최근 호출 검증 열",
         say="AI 사용량 화면입니다. 호출 수와 응답 시간, 캐시 사용, 그리고 검증 실패율을 봅니다. AI를 그대로 믿지 "
             "않고, 얼마나 자주 틀리는지 관찰할 수 있게 만들었습니다.",
         fx="검증 실패율 카드 하이라이트"),
    dict(id="D15", part="admin", kind="demo", dur=35, screen="관리자 · 회원 관리", action="‘demo’ 검색 → 권한 필터 → ‘관리자로’ → 거부 메시지",
         say="회원 관리에서는 이름이나 이메일로 찾고, 권한으로 걸러 볼 수 있습니다. 권한을 바꿔 보겠습니다. 테스트 관리자는 조회만 "
             "가능해서, 서버가 이렇게 거부합니다. 화면뿐 아니라 서버에서도 권한을 검사합니다.",
         fx="거부 메시지 하이라이트, 자막 ‘서버 권한 검사’"),
    dict(id="D16", part="admin", kind="demo", dur=15, screen="Render /docs (실제 서버 API 문서)", action="API 목록 스크롤",
         say="데모 화면 뒤에 있는 실제 서버입니다. FastAPI가 만든 문서로 서른네 개 API를 확인할 수 있습니다.", fx="엔드포인트 묶음 하이라이트"),
    dict(id="D17", part="admin", kind="demo", dur=15, screen="GitHub Actions 최근 실행", action="성공한 작업 목록 정지",
         say="코드를 올리면 테스트가 자동으로 돌고, 바뀐 부분만 배포됩니다.", fx="성공 job 목록 하이라이트"),
    # ---------------- ⑤ 클로징 09:00–10:00
    dict(id="C17", part="close", kind="slide", slide=17, dur=35, screen="PPT 17장 회고", action="슬라이드 쇼 복귀",
         say="아쉬운 점도 있습니다. 실제 데이터 기준 모델 성능과 AI 품질은 아직 측정하지 못했고, EC2 운영 연결도 남아 있습니다. "
             "다음 단계로 판정 적중률을 집계하고, 인증 방식과 알림을 개선하겠습니다.",
         fx="‘한계’ 카드 강조", hl=[(4.65, 1.67, 4.05, 5.1), (8.75, 1.67, 4.05, 5.1)]),
    dict(id="C18", part="close", kind="slide", slide=18, dur=25, screen="PPT 18장 마무리", action="링크 카드 정지 → 페이드아웃",
         say="픽타이밍은 가격 비교를 넘어, 언제 살지까지 판단을 돕습니다. 코드와 문서는 GitHub에서 확인하실 수 있습니다. 시청해 주셔서 감사합니다.",
         fx="GitHub 링크 강조", hl=[(.55, 4.1, 6.1, .8)]),
]


def timeline():
    t = 0.0
    for s in SCENES:
        s["start"] = t
        t += s["dur"]
    assert abs(t - 600) < 1e-6, t
    return SCENES


def stamp(sec, ms=False):
    m, s = divmod(sec, 60)
    return f"{int(m):02d}:{s:06.3f}" if ms else f"{int(m):02d}:{int(s):02d}"

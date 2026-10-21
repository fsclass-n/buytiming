"""Google Gemini 자연어 조언·상담 (API 명세서 3.4 프롬프트 설계)

- 분석 수치를 표시 형식(반올림 완료) 문자열로 넘겨 반올림 불일치를 막는다.
- 응답 속 숫자를 입력 수치와 대조하고, 없는 숫자가 있으면 위반 내용을 넣어 1회 재요청한다.
- 키가 없거나 실패하면 규칙 기반 템플릿 문장으로 대체한다.
"""
import json
import logging
import re
import time

from pydantic import BaseModel, Field

from ..config import get_settings

log = logging.getLogger(__name__)

VERDICT = {"BUY_NOW": "지금 구매 추천", "WAIT_A_BIT": "조금 더 지켜보기", "WAIT": "기다리기 권장", "HOLD": "판단 보류"}
CAUTION = "가격 예측은 과거 데이터 기반 참고 정보이며 실제 가격과 다를 수 있습니다."

SYSTEM_ADVICE = (
    "너는 소비자 구매 상담가다. 제공된 분석 데이터의 수치만 사용하고 새로운 숫자를 만들지 않는다. "
    "'과거 패턴상'처럼 근거를 밝히고 구매를 강요하거나 단정하지 않는다. 데이터에 없는 내용은 언급하지 않는다. "
    "verdict는 제공된 verdict를 그대로 쓰고, summary는 2문장, reasons는 근거 3개, caution은 참고 정보 고지 1문장으로 한국어로 작성한다."
)
SYSTEM_CHAT = (
    "너는 소비자 구매 상담가다. 제공된 분석 데이터의 수치만 근거로 사용자의 질문에 2~3문장 한국어로 답한다. "
    "새로운 숫자를 만들지 않으며, 데이터로 알 수 없는 질문에는 '제공된 데이터로는 알 수 없습니다'라고 답한다. 구매를 강요하지 않는다."
)


class AdviceOut(BaseModel):
    verdict: str
    summary: str
    reasons: list[str] = Field(min_length=1, max_length=4)
    caution: str


class ChatOut(BaseModel):
    answer: str


def won(n: int | float | None) -> str:
    return "-" if n is None else f"{int(round(n)):,}원"


def facts_from(a: dict, product_name: str, cheapest: dict | None) -> dict:
    """모델에 넘길 분석 데이터(표시 형식). 이 값에 들어 있는 숫자만 응답에 허용된다."""
    f = {"상품": product_name, "verdict": VERDICT[a["label"]], "가격_이력_일수": f"{a['history_days']}일",
         "판단_기간": "최근 90일", "예측_범위": "7일 안에 5% 이상 하락"}
    if a.get("current_price") is not None:
        f.update(현재_최저_실구매가=won(a["current_price"]), 최근90일_최저가=won(a["min_90d"]),
                 최근90일_최저가_날짜=a.get("min_90d_date"), 최근90일_평균가=won(a.get("avg_90d")))
    if a.get("score") is not None:
        gap = (a["current_price"] / a["min_90d"] - 1) * 100
        trend = a["trend_30d_pct"]
        f.update(적기_점수=f"{a['score']}점", 가격_위치=f"최근 90일 중 하위 {round(a['percentile_90d'] * 100)}%",
                 하락_확률=f"{round(a['prob_drop_7d'] * 100)}%", 최저가와_차이=f"{gap:.1f}%",
                 최근30일_추세="오르는 추세" if trend > 0.05 else "내리는 추세" if trend < -0.05 else "변동 작음",
                 할인_주기=f"약 {a['discount_cycle_days']}일" if a.get("discount_cycle_days") else "뚜렷한 주기 없음",
                 마지막_할인_후=f"{a['days_since_drop']}일 경과")
    if cheapest:
        f["최저가_쇼핑몰"] = f"{cheapest['mall']} {won(cheapest['total_price'])}(배송비 포함)"
    return f


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set[str]:
    return {m.replace(",", "") for m in _NUM.findall(text)}


def unknown_numbers(text: str, facts: dict) -> list[str]:
    """응답 문장 속 숫자 중 입력 데이터에 없는 숫자"""
    allowed = _numbers(json.dumps(facts, ensure_ascii=False)) | {"1", "2", "3"}
    return sorted(_numbers(text) - allowed)


# ---------------------------------------------------------------- 템플릿(대체 문장)
def template_advice(a: dict) -> AdviceOut:
    if a["label"] == "HOLD":
        return AdviceOut(verdict=VERDICT["HOLD"],
                         summary=f"가격 이력이 {a['history_days']}일로 30일 미만이라 구매 적기를 판단하기 어렵습니다.",
                         reasons=["가격 이력 30일 이상부터 판정", "목표가를 설정하면 도달 시 알려 드립니다"], caution=CAUTION)
    f = facts_from(a, "", None)
    return AdviceOut(
        verdict=VERDICT[a["label"]],
        summary=f"현재 최저 실구매가 {f['현재_최저_실구매가']}은 {f['가격_위치']} 수준입니다. 과거 패턴상 7일 안에 5% 이상 더 내려갈 가능성은 {f['하락_확률']}입니다.",
        reasons=[f"90일 최저가 {f['최근90일_최저가']}과의 차이 {f['최저가와_차이']}", f"최근 30일 가격 {f['최근30일_추세']}",
                 f"할인 주기 {f['할인_주기']}, 마지막 할인 후 {f['마지막_할인_후']}"],
        caution=CAUTION)


def template_chat(a: dict, question: str, cheapest: dict | None) -> str:
    q = re.sub(r"\s", "", question)
    if a["label"] == "HOLD" and re.search("기다|싸질|다음주|언제", q):
        return f"가격 이력이 {a['history_days']}일뿐이라 앞으로의 가격 변화를 판단하기 어렵습니다. 목표가 알림을 설정해 두시는 것을 권합니다."
    if a.get("score") is not None and re.search("기다|싸질|다음주|내려", q):
        return (f"과거 패턴상 7일 안에 5% 이상 더 내려갈 가능성은 {round(a['prob_drop_7d'] * 100)}%입니다. "
                f"현재 판정은 '{VERDICT[a['label']]}'이며, 지금 가격은 최근 90일 중 하위 {round(a['percentile_90d'] * 100)}% 수준입니다.")
    if a.get("min_90d") and re.search("최저|역대|제일싼", q):
        return f"최근 90일 최저 실구매가는 {won(a['min_90d'])}({a['min_90d_date']})이고, 현재는 {won(a['current_price'])}입니다."
    if re.search("언제|주기|할인", q):
        if a.get("discount_cycle_days"):
            return f"과거 데이터에서 할인은 약 {a['discount_cycle_days']}일 간격으로 나타났고, 마지막 할인 이후 {a['days_since_drop']}일이 지났습니다."
        return "제공된 가격 이력에서는 뚜렷한 할인 주기를 찾지 못했습니다."
    if cheapest and re.search("어디|쇼핑몰|몰", q):
        return f"지금은 {cheapest['mall']}의 실구매가가 {won(cheapest['total_price'])}(배송비 포함)으로 가장 저렴합니다."
    return "제공된 가격 데이터로는 답하기 어려운 질문입니다. 가격 추이나 구매 시점에 대해 질문해 주세요."


# ---------------------------------------------------------------- Gemini 호출
_client = None


def get_client():
    """키가 없으면 None (템플릿 모드). 테스트에서는 monkeypatch로 교체한다."""
    global _client
    key = get_settings().gemini_api_key
    if not key:
        return None
    if _client is None:
        from google import genai

        _client = genai.Client(api_key=key)
    return _client


def _call(client, system: str, schema, payload: dict, extra: str = ""):
    from google.genai import types

    contents = json.dumps(payload, ensure_ascii=False) + (f"\n\n{extra}" if extra else "")
    resp = client.models.generate_content(
        model=get_settings().gemini_model, contents=contents,
        config=types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json",
                                           response_schema=schema, temperature=0.3))
    usage = getattr(resp, "usage_metadata", None)
    tokens = (getattr(usage, "prompt_token_count", 0) or 0, getattr(usage, "candidates_token_count", 0) or 0)
    return schema.model_validate_json(resp.text), tokens


def _generate(system: str, schema, payload: dict, facts: dict, to_text, fallback):
    """반환: (결과, meta) — meta: source, validation, input_tokens, output_tokens, latency_ms"""
    started = time.perf_counter()
    meta = {"source": "template", "validation": "TEMPLATE", "input_tokens": 0, "output_tokens": 0}
    client = get_client()
    result = None
    if client is not None:
        try:
            out, tok = _call(client, system, schema, payload)
            meta.update(source="gemini", validation="OK", input_tokens=tok[0], output_tokens=tok[1])
            bad = unknown_numbers(to_text(out), facts)
            if bad:
                out, tok2 = _call(client, system, schema, payload,
                                  extra=f"직전 응답에 입력 데이터에 없는 숫자 {', '.join(bad)}가 있었다. 입력 데이터의 숫자만 사용해 다시 작성하라.")
                meta.update(validation="RETRY", input_tokens=tok[0] + tok2[0], output_tokens=tok[1] + tok2[1])
                if unknown_numbers(to_text(out), facts):
                    out, meta["validation"] = None, "FALLBACK"
            result = out
        except Exception:  # 네트워크·한도(429)·스키마 오류 → 템플릿 대체
            log.exception("Gemini 호출 실패")
            meta["validation"] = "ERROR"
    if result is None:
        result = fallback()
        meta["source"] = "template"
    meta["latency_ms"] = int((time.perf_counter() - started) * 1000)
    return result, meta


def generate_advice(a: dict, product_name: str, cheapest: dict | None) -> tuple[AdviceOut, dict]:
    if a["label"] == "HOLD":
        return template_advice(a), {"source": "template", "validation": "TEMPLATE", "input_tokens": 0, "output_tokens": 0, "latency_ms": 0}
    facts = facts_from(a, product_name, cheapest)
    return _generate(SYSTEM_ADVICE, AdviceOut, facts, facts,
                     to_text=lambda o: " ".join([o.summary, *o.reasons]), fallback=lambda: template_advice(a))


def generate_chat(a: dict, product_name: str, cheapest: dict | None, question: str) -> tuple[str, dict]:
    facts = facts_from(a, product_name, cheapest)
    out, meta = _generate(SYSTEM_CHAT, ChatOut, {"분석_데이터": facts, "질문": question}, {**facts, "질문": question},
                          to_text=lambda o: o.answer, fallback=lambda: ChatOut(answer=template_chat(a, question, cheapest)))
    return out.answer, meta

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd

from app.ai import gemini
from app.ml.features import FEATURES, feature_frame, labels

ANALYSIS = {"product_id": 1, "history_days": 120, "current_price": 120500, "min_90d": 117600, "avg_90d": 132000,
            "min_90d_date": "2026-09-19", "percentile_90d": 0.034, "prob_drop_7d": 0.103, "score": 92, "label": "BUY_NOW",
            "trend_30d_pct": -0.08, "days_since_drop": 0, "discount_cycle_days": 25, "model_version": "rf-test"}


def test_features_and_labels():
    idx = pd.date_range("2026-06-01", periods=120, freq="D")
    s = pd.Series(100000 + np.sin(np.arange(120) / 5) * 5000, index=idx)
    s.iloc[-1] = s.min() - 1000
    f = feature_frame(s)
    assert list(f.columns) == FEATURES
    assert f["percentile_90d"].iloc[-1] == 0.0  # 최근 90일 최저가
    y = labels(s)
    assert y.iloc[-7:].isna().all() and set(y.dropna().unique()) <= {0.0, 1.0}


def test_unknown_numbers_validator():
    facts = gemini.facts_from(ANALYSIS, "무선 이어폰 X2", None)
    ok = "현재 120,500원은 최근 90일 중 하위 3% 수준이며 7일 안에 5% 이상 하락할 가능성은 10%입니다."
    assert gemini.unknown_numbers(ok, facts) == []
    bad = "작년 블랙프라이데이에는 30% 할인되어 89,000원이었습니다."
    assert set(gemini.unknown_numbers(bad, facts)) == {"89000"}  # 30은 '최근30일' 키로 허용, 89000은 입력에 없음


def test_template_advice_hold():
    out = gemini.template_advice({**ANALYSIS, "label": "HOLD", "history_days": 21, "score": None})
    assert out.verdict == "판단 보류" and "21일" in out.summary


class FakeModels:
    def __init__(self, texts):
        self.texts, self.calls = list(texts), 0

    def generate_content(self, **kw):
        self.calls += 1
        usage = SimpleNamespace(prompt_token_count=100, candidates_token_count=50)
        return SimpleNamespace(text=self.texts.pop(0), usage_metadata=usage)


def _advice_json(summary):
    return json.dumps({"verdict": "지금 구매 추천", "summary": summary, "reasons": ["90일 최저가 117,600원"],
                       "caution": "참고 정보입니다."}, ensure_ascii=False)


def test_gemini_retry_on_hallucinated_number(monkeypatch):
    fake = SimpleNamespace(models=FakeModels([_advice_json("작년에는 77,000원이었습니다."),
                                              _advice_json("현재 120,500원은 최근 90일 중 하위 3%입니다.")]))
    monkeypatch.setattr(gemini, "get_client", lambda: fake)
    out, meta = gemini.generate_advice(ANALYSIS, "무선 이어폰 X2", None)
    assert fake.models.calls == 2 and meta["validation"] == "RETRY" and meta["source"] == "gemini"
    assert "120,500원" in out.summary and meta["input_tokens"] == 200


def test_gemini_fallback_after_two_bad_answers(monkeypatch):
    fake = SimpleNamespace(models=FakeModels([_advice_json("77,000원"), _advice_json("66,000원")]))
    monkeypatch.setattr(gemini, "get_client", lambda: fake)
    out, meta = gemini.generate_advice(ANALYSIS, "무선 이어폰 X2", None)
    assert meta["validation"] == "FALLBACK" and meta["source"] == "template"
    assert gemini.unknown_numbers(out.summary, gemini.facts_from(ANALYSIS, "", None)) == []


def test_gemini_error_falls_back(monkeypatch):
    class Boom:
        def generate_content(self, **kw):
            raise RuntimeError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(gemini, "get_client", lambda: SimpleNamespace(models=Boom()))
    answer, meta = gemini.generate_chat(ANALYSIS, "무선 이어폰 X2", None, "더 기다리면 싸질까?")
    assert meta["validation"] == "ERROR" and "7일 안에" in answer

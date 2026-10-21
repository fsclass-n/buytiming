"""구매 적기 판정 피처 (설계서 1.3: 피처 8종). 추론과 학습이 같은 함수를 사용한다."""
import numpy as np
import pandas as pd

FEATURES = ["percentile_90d", "ratio_min_90d", "gap_ma7", "gap_ma30", "slope_30d", "volatility_30d",
            "days_since_drop", "is_month_end"]
HORIZON_DAYS = 7
DROP_THRESHOLD = 0.05
MIN_HISTORY = 30


def _percentile(window: np.ndarray) -> float:
    cur = window[-1]
    return float((window < cur).sum() / max(len(window) - 1, 1))


def _slope(window: np.ndarray) -> float:
    x = np.arange(len(window))
    return float(np.polyfit(x, window, 1)[0] / window.mean() * 100)  # 하루 변화율(%)


def feature_frame(s: pd.Series) -> pd.DataFrame:
    """일별 최저가 시계열 → 날짜별 피처 행렬"""
    s = s.astype(float)
    f = pd.DataFrame(index=s.index)
    f["percentile_90d"] = s.rolling(90, min_periods=MIN_HISTORY).apply(_percentile, raw=True)
    f["ratio_min_90d"] = s / s.rolling(90, min_periods=MIN_HISTORY).min()
    f["gap_ma7"] = s / s.rolling(7, min_periods=3).mean()
    f["gap_ma30"] = s / s.rolling(30, min_periods=10).mean()
    f["slope_30d"] = s.rolling(30, min_periods=10).apply(_slope, raw=True)
    f["volatility_30d"] = s.rolling(30, min_periods=10).std() / s.rolling(30, min_periods=10).mean()
    dropped = s <= 0.92 * s.shift(1).rolling(14, min_periods=7).max()
    counter, since = [], 60
    for flag in dropped:
        since = 0 if flag else min(since + 1, 60)
        counter.append(since)
    f["days_since_drop"] = counter
    f["is_month_end"] = (s.index.day >= 26).astype(int)
    return f


def labels(s: pd.Series) -> pd.Series:
    """향후 7일 안에 현재가 대비 5% 이상 하락하면 1"""
    future_min = s[::-1].rolling(HORIZON_DAYS, min_periods=HORIZON_DAYS).min()[::-1].shift(-1)
    y = (future_min <= s * (1 - DROP_THRESHOLD)).astype(float)
    y[future_min.isna()] = np.nan
    return y


def drop_events(s: pd.Series) -> list[pd.Timestamp]:
    dropped = s <= 0.92 * s.shift(1).rolling(14, min_periods=7).max()
    events: list[pd.Timestamp] = []
    for ts in s.index[dropped.fillna(False).to_numpy()]:
        if not events or (ts - events[-1]).days > 7:
            events.append(ts)
    return events


def heuristic_prob(row: pd.Series) -> float:
    """모델이 없을 때 쓰는 규칙 기반 하락 확률 (프런트엔드 데모 모드와 같은 개념)"""
    logit = (-1.0 + 4.0 * (row["percentile_90d"] - 0.35) + (0.9 if row["days_since_drop"] > 20 else -0.3)
             + (0.4 if row["slope_30d"] > 0.05 else 0) + (0.2 if row["is_month_end"] else 0))
    return float(np.clip(1 / (1 + np.exp(-logit)), 0.03, 0.95))

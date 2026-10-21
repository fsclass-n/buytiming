"""모델 재학습 (RPA 작업 BOT-03, 매일 03:00): 가격 이력 → 피처·라벨 → RandomForest → 성능 비교 후 교체

실행: python -m app.ml.train
"""
import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score
from sklearn.model_selection import TimeSeriesSplit
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import now_local
from ..models import ModelVersion, Product, RpaJobLog
from ..services.pricing import daily_lowest
from .features import FEATURES, feature_frame, labels
from .model_store import dump_model

log = logging.getLogger(__name__)


def build_dataset(db: Session) -> pd.DataFrame:
    frames = []
    for pid in db.execute(select(Product.id)).scalars():
        s = daily_lowest(db, pid)
        if len(s) < 40:
            continue
        df = feature_frame(s)
        df["y"] = labels(s)
        df["date"] = s.index
        frames.append(df.dropna())
    if not frames:
        return pd.DataFrame(columns=[*FEATURES, "y", "date"])
    return pd.concat(frames).sort_values("date").reset_index(drop=True)


def new_model() -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=150, max_depth=8, min_samples_leaf=3, class_weight="balanced",
                                  random_state=42, n_jobs=1)


def train_and_register(db: Session, force: bool = False) -> dict:
    started = now_local()
    data = build_dataset(db)
    if len(data) < 100 or data["y"].nunique() < 2:
        result = {"status": "SKIPPED", "message": f"학습 데이터 부족({len(data)}행)"}
        db.add(RpaJobLog(job_name="train_model", status="PARTIAL", message=result["message"], started_at=started, ended_at=now_local()))
        db.commit()
        return result
    X, y = data[FEATURES], data["y"].astype(int)
    f1s, precs = [], []
    for tr, te in TimeSeriesSplit(n_splits=5).split(X):
        if y.iloc[tr].nunique() < 2:
            continue
        m = new_model().fit(X.iloc[tr], y.iloc[tr])
        pred = m.predict(X.iloc[te])
        f1s.append(f1_score(y.iloc[te], pred, zero_division=0))
        precs.append(precision_score(y.iloc[te], pred, zero_division=0))
    f1, prec = float(np.mean(f1s)), float(np.mean(precs))
    active = db.execute(select(ModelVersion).where(ModelVersion.is_active.is_(True))).scalar_one_or_none()
    improve = force or active is None or active.f1 is None or f1 >= active.f1
    version = f"rf-{started:%Y%m%d-%H%M}"
    if improve:
        model = new_model().fit(X, y)
        db.execute(update(ModelVersion).values(is_active=False))
        db.add(ModelVersion(version=version, algorithm="RandomForestClassifier", f1=round(f1, 4), precision=round(prec, 4),
                            trained_rows=len(data), artifact=dump_model(model), is_active=True))
    msg = (f"F1 {f1:.2f}" + (f" (직전 {active.f1:.2f})" if active and active.f1 is not None else "")
           + (" → 모델 교체" if improve else " → 기존 모델 유지"))
    db.add(RpaJobLog(job_name="train_model", status="SUCCESS", collected=len(data), message=msg, started_at=started, ended_at=now_local()))
    db.commit()
    return {"status": "SUCCESS", "version": version if improve else (active.version if active else None),
            "f1": round(f1, 4), "precision": round(prec, 4), "rows": len(data), "replaced": improve}


if __name__ == "__main__":
    from ..database import SessionLocal, init_db

    logging.basicConfig(level=logging.INFO)
    init_db()
    with SessionLocal() as session:
        print(train_and_register(session))

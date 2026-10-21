"""가격 등록 직후: 적기 판정 사전 계산 → 목표가 도달·판정 변경 알림 생성"""
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import now_local
from ..models import Alert, Product, Watchlist
from .timing import VERDICT, analyze, latest_prediction, save_prediction

RENOTIFY_HOURS = 24


def refresh_product(db: Session, product: Product) -> int:
    prev = latest_prediction(db, product.id)
    a = analyze(db, product)
    save_prediction(db, a)
    created = 0
    watchers = db.execute(select(Watchlist).where(Watchlist.product_id == product.id)).scalars().all()
    now = now_local()
    for w in watchers:
        cur = a["current_price"]
        if (w.target_price is not None and cur is not None and cur <= w.target_price
                and (w.notified_at is None or w.notified_at < now - timedelta(hours=RENOTIFY_HOURS))):
            db.add(Alert(user_id=w.user_id, product_id=product.id, type="TARGET_PRICE",
                         message=f"{product.name} 실구매가가 {cur:,}원으로 목표가 {w.target_price:,}원 이하가 되었습니다."))
            w.notified_at = now
            created += 1
        if prev and prev.label != a["label"] and "HOLD" not in (prev.label, a["label"]):
            db.add(Alert(user_id=w.user_id, product_id=product.id, type="TIMING_CHANGE",
                         message=f"{product.name} 판정이 '{VERDICT[prev.label]}'에서 '{VERDICT[a['label']]}'(으)로 바뀌었습니다."))
            created += 1
    return created

import hashlib
from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai import gemini
from ..config import get_settings, now_local
from ..database import get_db
from ..errors import ApiError
from ..models import AiAdviceLog, User
from ..schemas import ChatIn
from ..security import current_user
from ..services import pricing
from ..services.timing import analyze, public_view
from .products import get_product

router = APIRouter(tags=["AI 판정·조언"])
CACHE_HOURS = 24


def _used_today(db: Session, user: User) -> int:
    start = datetime.combine(now_local().date(), time.min)
    return db.execute(select(func.count()).select_from(AiAdviceLog).where(
        AiAdviceLog.user_id == user.id, AiAdviceLog.created_at >= start, AiAdviceLog.cache_hit.is_(False),
        AiAdviceLog.source == "gemini")).scalar_one()


def _check_quota(db: Session, user: User) -> int:
    used = _used_today(db, user)
    limit = get_settings().ai_daily_limit
    if used >= limit:
        raise ApiError(429, "AI_LIMIT_EXCEEDED", f"AI 사용 한도(일 {limit}회)를 초과했습니다. 내일 다시 이용해 주세요.")
    return limit - used


def _cheapest(db: Session, product_id: int) -> dict | None:
    return next((i for i in pricing.compare(db, product_id)["items"] if i["is_lowest"]), None)


@router.get("/products/{product_id}/timing")
def timing(product_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return public_view(analyze(db, get_product(db, product_id)))


@router.post("/products/{product_id}/advice")
def advice(product_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    product = get_product(db, product_id)
    a = analyze(db, product)
    key = hashlib.sha256(f"{product.id}:{a['current_price']}:{a['label']}:{a['model_version']}".encode()).hexdigest()
    hit = db.execute(select(AiAdviceLog).where(
        AiAdviceLog.cache_key == key, AiAdviceLog.type == "ADVICE", AiAdviceLog.advice_json.is_not(None),
        AiAdviceLog.created_at >= now_local() - timedelta(hours=CACHE_HOURS)).order_by(AiAdviceLog.id.desc()).limit(1)).scalar_one_or_none()
    limit = get_settings().ai_daily_limit
    if hit:
        db.add(AiAdviceLog(product_id=product.id, user_id=user.id, type="ADVICE", cache_key=key, cache_hit=True,
                           source=hit.source, validation=hit.validation, advice_json=hit.advice_json, latency_ms=1))
        db.commit()
        return {**hit.advice_json, "cached": True, "source": hit.source, "remaining": limit - _used_today(db, user)}
    _check_quota(db, user)
    out, meta = gemini.generate_advice(a, product.name, _cheapest(db, product.id))
    body = out.model_dump()
    db.add(AiAdviceLog(product_id=product.id, user_id=user.id, type="ADVICE", cache_key=key, cache_hit=False, advice_json=body, **meta))
    db.commit()
    return {**body, "cached": False, "source": meta["source"], "remaining": limit - _used_today(db, user)}


@router.post("/ai/chat")
def chat(body: ChatIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    product = get_product(db, body.product_id)
    _check_quota(db, user)
    a = analyze(db, product)
    answer, meta = gemini.generate_chat(a, product.name, _cheapest(db, product.id), body.question.strip())
    db.add(AiAdviceLog(product_id=product.id, user_id=user.id, type="CHAT", advice_json={"q": body.question, "a": answer}, **meta))
    db.commit()
    return {"answer": answer, "source": meta["source"], "remaining": get_settings().ai_daily_limit - _used_today(db, user)}

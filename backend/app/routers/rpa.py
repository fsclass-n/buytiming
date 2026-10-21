"""RPA 수신 API (X-RPA-KEY 인증) — 수집기·스케줄러 전용"""
import base64
import logging
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..config import get_settings, now_local
from ..database import SessionLocal, get_db
from ..errors import ApiError
from ..jobs.weekly_report import build_report
from ..ml.train import train_and_register
from ..models import Mall, ModelVersion, PriceHistory, Product, ProductListing, PublicPrice, RpaJobLog
from ..schemas import JobLogIn, ModelUploadIn, PriceBulkIn, PublicPriceIn
from ..security import rpa_key
from ..services.alerts import refresh_product

router = APIRouter(prefix="/rpa", tags=["RPA"], dependencies=[Depends(rpa_key)])
log = logging.getLogger(__name__)


@router.get("/listings")
def listings(db: Session = Depends(get_db)):
    """수집 대상 판매 페이지 목록 (활성 쇼핑몰·활성 판매처)"""
    latest = (select(PriceHistory.listing_id, func.max(PriceHistory.id).label("pid")).group_by(PriceHistory.listing_id).subquery())
    rows = db.execute(select(ProductListing, Product, Mall, PriceHistory)
                      .join(Product, Product.id == ProductListing.product_id).join(Mall, Mall.id == ProductListing.mall_id)
                      .outerjoin(latest, latest.c.listing_id == ProductListing.id)
                      .outerjoin(PriceHistory, PriceHistory.id == latest.c.pid)
                      .where(ProductListing.is_active.is_(True), Mall.is_active.is_(True))).all()
    return {"items": [{"listing_id": l.id, "product_id": p.id, "model_no": p.model_no, "product": p.name,
                       "mall_id": m.id, "mall": m.name, "url": l.url,
                       "last_price": ph.price if ph else None, "last_shipping_fee": ph.shipping_fee if ph else None}
                      for l, p, m, ph in rows]}


@router.post("/prices/bulk")
def prices_bulk(body: PriceBulkIn, db: Session = Depends(get_db)):
    """가격 일괄 등록 → 판정 갱신(사전 계산) → 목표가·판정 변경 알림"""
    at = body.collected_at or now_local()
    if at.tzinfo is not None:
        at = at.astimezone(ZoneInfo(get_settings().tz)).replace(tzinfo=None)
    valid = {lid: pid for lid, pid in db.execute(select(ProductListing.id, ProductListing.product_id)
                                                 .where(ProductListing.id.in_([i.listing_id for i in body.items])))}
    touched: set[int] = set()
    for i in body.items:
        if i.listing_id not in valid:
            continue
        db.add(PriceHistory(listing_id=i.listing_id, price=i.price, shipping_fee=i.shipping_fee,
                            total_price=i.price + i.shipping_fee, in_stock=i.in_stock, collected_at=at))
        touched.add(valid[i.listing_id])
    db.flush()
    alerts = sum(refresh_product(db, db.get(Product, pid)) for pid in touched)
    db.commit()
    return {"inserted": sum(i.listing_id in valid for i in body.items), "skipped": sum(i.listing_id not in valid for i in body.items),
            "products_updated": len(touched), "alerts_created": alerts}


@router.put("/public-prices")
def public_prices(body: PublicPriceIn, db: Session = Depends(get_db)):
    by_model = {p.model_no: p.id for p in db.execute(select(Product)).scalars()}
    saved = 0
    for i in body.items:
        pid = by_model.get(i.model_no)
        if pid is None:
            continue
        row = db.execute(select(PublicPrice).where(PublicPrice.product_id == pid, PublicPrice.good_id == i.good_id,
                                                   PublicPrice.survey_date == i.survey_date)).scalar_one_or_none()
        if row:
            row.price, row.store_type = i.price, i.store_type
        else:
            db.add(PublicPrice(product_id=pid, good_id=i.good_id, price=i.price, store_type=i.store_type, survey_date=i.survey_date))
        saved += 1
    db.commit()
    return {"saved": saved, "unmatched": len(body.items) - saved}


@router.post("/models", status_code=201)
def upload_model(body: ModelUploadIn, db: Session = Depends(get_db)):
    try:
        artifact = base64.b64decode(body.artifact_b64, validate=True)
    except ValueError:
        raise ApiError(400, "INVALID_ARTIFACT", "artifact_b64가 올바른 base64 형식이 아닙니다.") from None
    if body.activate:
        db.execute(update(ModelVersion).values(is_active=False))
    mv = ModelVersion(version=body.version, algorithm=body.algorithm, f1=body.f1, precision=body.precision,
                      trained_rows=body.trained_rows, artifact=artifact, is_active=body.activate)
    db.add(mv)
    db.commit()
    return {"id": mv.id, "version": mv.version, "active": mv.is_active}


@router.post("/logs", status_code=201)
def job_log(body: JobLogIn, db: Session = Depends(get_db)):
    row = RpaJobLog(**body.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


def _train_job() -> None:
    with SessionLocal() as db:
        try:
            log.info("train result: %s", train_and_register(db))
        except Exception as exc:  # 학습 실패는 로그로 남기고 API는 계속 동작
            log.exception("train failed")
            db.rollback()
            db.add(RpaJobLog(job_name="train_model", status="FAIL", message=str(exc)[:500], started_at=now_local(), ended_at=now_local()))
            db.commit()


@router.post("/train", status_code=202)
def train(background: BackgroundTasks):
    """모델 재학습을 백그라운드로 실행 (스케줄러가 매일 03:00 호출)"""
    background.add_task(_train_job)
    return {"status": "ACCEPTED"}


@router.get("/reports/weekly")
def weekly_report(db: Session = Depends(get_db)):
    data, name = build_report(db)
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})

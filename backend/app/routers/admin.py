from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings, now_local
from ..database import get_db
from ..models import AiAdviceLog, ModelVersion, Product, RpaJobLog, User
from ..security import admin_user

router = APIRouter(prefix="/admin", tags=["관리자"])


def _days(n: int) -> list:
    today = now_local().date()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


@router.get("/rpa-logs")
def rpa_logs(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    since = datetime.combine(_days(7)[0], time.min)
    logs = db.execute(select(RpaJobLog).where(RpaJobLog.started_at >= since).order_by(RpaJobLog.started_at.desc())).scalars().all()
    collect = [l for l in logs if l.job_name == "collect_prices"]
    daily = []
    for d in _days(7):
        day = [l for l in collect if l.started_at.date() == d]
        daily.append({"date": d.isoformat(), "runs": len(day), "success": sum(l.collected for l in day),
                      "failed": sum(l.failed for l in day), "collected": sum(l.collected for l in day)})
    total = sum(r["collected"] + r["failed"] for r in daily)
    models = db.execute(select(ModelVersion).order_by(ModelVersion.id.desc()).limit(10)).scalars().all()
    return {
        "summary": {"runs_today": daily[-1]["runs"], "collected_today": daily[-1]["collected"],
                    "success_rate": round(1 - sum(r["failed"] for r in daily) / total, 4) if total else None,
                    "last_run_at": logs[0].started_at if logs else None},
        "daily": daily,
        "logs": [{"id": l.id, "job_name": l.job_name, "status": l.status, "collected": l.collected, "failed": l.failed,
                  "message": l.message, "started_at": l.started_at, "ended_at": l.ended_at} for l in logs[:50]],
        "models": [{"version": m.version, "algorithm": m.algorithm, "f1": m.f1, "precision": m.precision,
                    "trained_rows": m.trained_rows, "created_at": m.created_at, "active": m.is_active} for m in models],
    }


@router.get("/ai-metrics")
def ai_metrics(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    since = datetime.combine(_days(7)[0], time.min)
    rows = db.execute(select(AiAdviceLog, Product.name).join(Product, Product.id == AiAdviceLog.product_id)
                      .where(AiAdviceLog.created_at >= since).order_by(AiAdviceLog.id.desc())).all()
    logs = [r[0] for r in rows]
    daily = []
    for d in _days(7):
        day = [l for l in logs if l.created_at.date() == d]
        live = [l for l in day if not l.cache_hit]
        daily.append({"date": d.isoformat(), "calls": len(day), "cache_hits": sum(l.cache_hit for l in day),
                      "avg_latency_ms": round(sum(l.latency_ms for l in live) / len(live)) if live else 0,
                      "tokens": sum(l.input_tokens + l.output_tokens for l in day),
                      "validation_fail": sum(l.validation in ("FALLBACK", "ERROR") for l in day)})
    calls = len(logs)
    live = [l for l in logs if not l.cache_hit]
    return {
        "summary": {"calls_7d": calls, "avg_latency_ms": round(sum(l.latency_ms for l in live) / len(live)) if live else 0,
                    "tokens_7d": sum(l.input_tokens + l.output_tokens for l in logs),
                    "cache_hit_rate": round(sum(l.cache_hit for l in logs) / calls, 3) if calls else 0,
                    "validation_fail_rate": round(sum(l.validation in ("FALLBACK", "ERROR") for l in logs) / calls, 4) if calls else 0,
                    "model": get_settings().gemini_model + ("" if get_settings().gemini_api_key else " (키 미설정: 규칙 기반 대체)")},
        "daily": daily,
        "recent": [{"created_at": l.created_at, "type": l.type, "product": name, "latency_ms": l.latency_ms,
                    "cache_hit": l.cache_hit, "validation": l.validation} for l, name in rows[:20]],
    }

"""운영 모델 로드: DB(model_versions)의 활성 버전을 메모리에 캐시"""
import io
import threading

import joblib
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ModelVersion

_lock = threading.Lock()
_cache: dict[int, object] = {}


def dump_model(model) -> bytes:
    buf = io.BytesIO()
    joblib.dump(model, buf, compress=3)
    return buf.getvalue()


def load_active(db: Session) -> tuple[object | None, ModelVersion | None]:
    mv = db.execute(select(ModelVersion).where(ModelVersion.is_active.is_(True), ModelVersion.artifact.is_not(None))
                    .order_by(ModelVersion.id.desc()).limit(1)).scalar_one_or_none()
    if mv is None:
        return None, None
    with _lock:
        if mv.id not in _cache:
            _cache.clear()
            _cache[mv.id] = joblib.load(io.BytesIO(mv.artifact))
        return _cache[mv.id], mv

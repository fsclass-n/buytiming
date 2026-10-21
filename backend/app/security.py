import hmac
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .errors import ApiError
from .models import User

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(user: User) -> str:
    s = get_settings()
    payload = {"sub": str(user.id), "role": user.role,
               "exp": datetime.now(UTC) + timedelta(minutes=s.jwt_expire_minutes)}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if cred is None:
        raise ApiError(401, "UNAUTHORIZED", "로그인이 필요합니다.")
    try:
        payload = jwt.decode(cred.credentials, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRED", "로그인이 만료되었습니다. 다시 로그인해 주세요.") from None
    except jwt.PyJWTError:
        raise ApiError(401, "INVALID_TOKEN", "유효하지 않은 인증 정보입니다.") from None
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise ApiError(401, "INVALID_TOKEN", "사용자를 찾을 수 없습니다.")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "ADMIN":
        raise ApiError(403, "FORBIDDEN", "관리자 권한이 필요합니다.")
    return user


def rpa_key(x_rpa_key: str | None = Header(default=None)) -> None:
    expected = get_settings().rpa_api_key
    if not x_rpa_key or not hmac.compare_digest(x_rpa_key, expected):
        raise ApiError(401, "INVALID_RPA_KEY", "RPA 인증 키가 올바르지 않습니다.")

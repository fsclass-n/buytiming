from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..errors import ApiError
from ..models import User
from ..schemas import LoginIn, SignupIn, TokenOut, UserOut
from ..security import create_token, current_user, hash_password, verify_password

router = APIRouter(tags=["인증"])


@router.post("/auth/signup", response_model=UserOut, status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        raise ApiError(409, "EMAIL_EXISTS", "이미 가입된 이메일입니다.")
    role = "ADMIN" if email in get_settings().admin_email_set else "USER"
    user = User(email=email, password_hash=hash_password(body.password), name=body.name.strip(), role=role)
    db.add(user)
    db.commit()
    return user


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise ApiError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")
    return TokenOut(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/users/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user

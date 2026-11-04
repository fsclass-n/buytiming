"""소셜 로그인(구글·네이버·카카오) — OAuth 2.0 Authorization Code 방식

흐름: 프런트 → GET /api/v1/auth/oauth/{p}/start → 제공자 로그인 → /callback?code&state
      → 토큰 교환·프로필 조회 → 사용자 생성/조회 → 프런트 /oauth/callback#token=... 로 이동
키(Client ID/Secret)는 서버 .env에만 둔다. 키가 없는 제공자는 /auth/providers에서 false로 표시된다.
"""
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
import jwt

from .config import Settings


@dataclass(frozen=True)
class Provider:
    name: str
    authorize_url: str
    token_url: str
    profile_url: str
    scope: str


PROVIDERS = {
    "google": Provider("google", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token",
                       "https://openidconnect.googleapis.com/v1/userinfo", "openid email profile"),
    "naver": Provider("naver", "https://nid.naver.com/oauth2.0/authorize", "https://nid.naver.com/oauth2.0/token",
                      "https://openapi.naver.com/v1/nid/me", ""),
    "kakao": Provider("kakao", "https://kauth.kakao.com/oauth/authorize", "https://kauth.kakao.com/oauth/token",
                      "https://kapi.kakao.com/v2/user/me", "profile_nickname account_email"),
}


def credentials(s: Settings, provider: str) -> tuple[str, str]:
    return getattr(s, f"{provider}_client_id", ""), getattr(s, f"{provider}_client_secret", "")


def enabled(s: Settings, provider: str) -> bool:
    cid, secret = credentials(s, provider)
    return bool(cid and (secret or provider == "kakao"))  # 카카오는 Client Secret이 선택


def make_state(s: Settings, provider: str, next_path: str) -> str:
    payload = {"p": provider, "n": next_path, "nonce": secrets.token_urlsafe(8), "exp": datetime.now(UTC) + timedelta(minutes=10)}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def read_state(s: Settings, state: str, provider: str) -> str:
    """state 서명·만료·제공자를 확인하고 로그인 후 이동할 경로를 돌려준다"""
    data = jwt.decode(state, s.jwt_secret, algorithms=["HS256"])
    if data.get("p") != provider:
        raise jwt.InvalidTokenError("provider mismatch")
    return safe_next(data.get("n"))


def safe_next(path: str | None) -> str:
    """외부 주소로 보내는 오픈 리다이렉트를 막는다 (같은 사이트의 경로만 허용)"""
    return path if path and path.startswith("/") and not path.startswith("//") else "/"


def authorize_url(s: Settings, provider: str, redirect_uri: str, state: str) -> str:
    p = PROVIDERS[provider]
    params = {"client_id": credentials(s, provider)[0], "redirect_uri": redirect_uri, "response_type": "code", "state": state}
    if p.scope:
        params["scope"] = p.scope
    return f"{p.authorize_url}?{urlencode(params)}"


def fetch_profile(s: Settings, provider: str, code: str, state: str, redirect_uri: str) -> dict:
    """인가 코드 → 액세스 토큰 → 프로필. 반환: {"email", "name"}"""
    p = PROVIDERS[provider]
    cid, secret = credentials(s, provider)
    form = {"grant_type": "authorization_code", "client_id": cid, "redirect_uri": redirect_uri, "code": code}
    if secret:
        form["client_secret"] = secret
    if provider == "naver":
        form["state"] = state
    with httpx.Client(timeout=10) as client:
        tok = client.post(p.token_url, data=form, headers={"Accept": "application/json"})
        tok.raise_for_status()
        access = tok.json().get("access_token")
        if not access:
            raise ValueError(f"{provider} 토큰 발급 실패: {tok.json().get('error_description') or tok.json().get('error')}")
        prof = client.get(p.profile_url, headers={"Authorization": f"Bearer {access}"})
        prof.raise_for_status()
    return normalize(provider, prof.json())


def normalize(provider: str, data: dict) -> dict:
    if provider == "google":
        return {"email": data.get("email"), "name": data.get("name") or data.get("email", "").split("@")[0]}
    if provider == "naver":
        r = data.get("response", {})
        return {"email": r.get("email") or f"naver_{r.get('id')}@naver.oauth", "name": r.get("name") or r.get("nickname") or "네이버 사용자"}
    acct = data.get("kakao_account", {})
    nick = acct.get("profile", {}).get("nickname") or data.get("properties", {}).get("nickname") or "카카오 사용자"
    # 카카오 이메일은 동의 항목 설정(비즈 앱)에 따라 제공되지 않을 수 있어 회원 번호로 대체 식별자를 만든다
    return {"email": acct.get("email") or f"kakao_{data.get('id')}@kakao.oauth", "name": nick}

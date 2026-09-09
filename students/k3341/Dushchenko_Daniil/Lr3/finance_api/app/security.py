"""Пароли и JWT. Регистрация и проверка пользователя реализованы вручную."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.db import get_session
from app.models import User

SECRET_KEY = os.environ.get("JWT_SECRET", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("Задайте JWT_SECRET длиной не менее 32 символов в .env")
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/token")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000)
    return f"pbkdf2_sha256$600000${salt}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False  # У записей из старой практики пароля ещё нет.
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(actual.hex(), digest)
    except (ValueError, TypeError):
        return False


def create_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=30),
         "version": user.token_version}, SECRET_KEY, algorithm="HS256",
    )


def get_current_user(token: str = Depends(oauth2), session: Session = Depends(get_session)) -> User:
    error = HTTPException(401, "Требуется действующий токен", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"],
                             options={"require": ["sub", "exp", "iat", "version"]})
        user = session.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error
    if user is None or user.token_version != payload["version"]:
        raise error
    return user

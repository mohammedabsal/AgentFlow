from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    payload = {
        "sub": subject,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

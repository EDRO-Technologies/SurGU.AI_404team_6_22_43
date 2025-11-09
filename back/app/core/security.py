from jose import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Optional
from uuid import UUID

from app.core.config import settings

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.JWT_ALGORITHM


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли обычный пароль хешированному."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Генерирует хеш для пароля."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT Access Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})

    # Конвертируем UUID в str для сериализации в JWT
    for key, value in to_encode.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Создает JWT Refresh Token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})

    for key, value in to_encode.items():
        if isinstance(value, UUID):
            to_encode[key] = str(value)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Декодирует токен, возвращает payload или None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Токен истек
        return None
    except jwt.InvalidTokenError:
        # Невалидный токен
        return None
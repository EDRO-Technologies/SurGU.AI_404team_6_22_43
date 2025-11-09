from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError
from uuid import UUID
from jose import jwt

from app.core.database import get_db_session
from app.core import security
from app.core.config import settings
from app import models, schemas

# Схема OAuth2, указывает FastAPI, откуда брать токен
# (в данном случае, из заголовка Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db_session)
) -> models.User:
    """
    Dependency для получения текущего пользователя из JWT токена.
    Проверяет валидность токена, тип 'access' и находит пользователя в БД.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.decode_token(token)
    if payload is None:
        raise credentials_exception

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'access'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    # Находим пользователя в БД
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_workspace_member(
        workspace_id: UUID,
        current_user: models.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
) -> models.WorkspaceMembership:
    """
    Проверяет, что текущий пользователь имеет доступ (любую роль)
    к указанному workspace_id.
    """
    result = await db.execute(
        select(models.WorkspaceMembership)
        .where(
            models.WorkspaceMembership.workspace_id == workspace_id,
            models.WorkspaceMembership.user_id == current_user.id
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this workspace"
        )
    return membership


async def get_workspace_admin(
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
) -> models.WorkspaceMembership:
    """
    Проверяет, что пользователь является 'Admin' в данном воркспейсе.
    """
    if membership.role != models.UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an Admin to perform this action"
        )
    return membership


async def get_workspace_editor(
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
) -> models.WorkspaceMembership:
    """
    Проверяет, что пользователь является 'Admin' или 'Editor'.
    """
    if membership.role not in [models.UserRoleEnum.ADMIN, models.UserRoleEnum.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an Admin or Editor to perform this action"
        )
    return membership
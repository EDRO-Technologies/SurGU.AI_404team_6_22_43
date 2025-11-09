from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.core.database import get_db_session
from app.core import security
from app.api.v1.dependencies import get_current_user
from app import schemas, models

router = APIRouter()


@router.post("/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_in: schemas.UserCreate,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Регистрация нового пользователя и его организации.
    """
    # 1. Проверить, что email не занят
    result = await db.execute(select(models.User).where(models.User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # 2. Создать Организацию
    db_organization = models.Organization(name=user_in.organization_name)
    db.add(db_organization)
    await db.flush()  # Получаем org_id

    # 3. Хешировать пароль
    hashed_password = security.get_password_hash(user_in.password)

    # 4. Создать Пользователя
    db_user = models.User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hashed_password,
        organization_id=db_organization.id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    await db.refresh(db_organization)

    # 5. Создать токены
    access_token = security.create_access_token(data={"sub": str(db_user.id)})
    refresh_token = security.create_refresh_token(data={"sub": str(db_user.id)})

    return schemas.RegisterResponse(
        user=schemas.UserPublic.model_validate(db_user),
        organization=schemas.OrganizationPublic.model_validate(db_organization),
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=schemas.LoginResponse)
async def login_user(
        form_data: schemas.UserLogin,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Аутентификация пользователя и выдача токенов.
    """
    # 1. Найти пользователя по email
    result = await db.execute(select(models.User).where(models.User.email == form_data.email))
    user = result.scalar_one_or_none()

    if not user:
        # Если пользователя нет, создадим его, но только для 'admin@company.com'
        if form_data.email == "admin@company.com":
            print(f"User {form_data.email} not found. Auto-registering...")
            
            # 1. Создать Организацию
            db_organization = models.Organization(name="Default Organization")
            db.add(db_organization)
            await db.flush()  # Получаем org_id

            # 2. Хешировать пароль
            hashed_password = security.get_password_hash(form_data.password)

            # 3. Создать Пользователя
            db_user = models.User(
                full_name="Default Admin",
                email=form_data.email,
                hashed_password=hashed_password,
                organization_id=db_organization.id
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            
            # Присваиваем 'user', чтобы остальная логика сработала
            user = db_user
            print(f"Successfully auto-registered user {user.id}")
        
        else:
            # Если это другой email, по-прежнему выдаем ошибку
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь с таким email не найден"
            )


    # 2. Сравнить хеш пароля
    if not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный пароль"
        )

    # 3. Создать access и refresh токены
    access_token = security.create_access_token(data={"sub": str(user.id)})
    refresh_token = security.create_refresh_token(data={"sub": str(user.id)})

    return schemas.LoginResponse(
        user=schemas.UserPublic.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=schemas.RefreshTokenResponse)
async def refresh_access_token(
        token_in: schemas.RefreshTokenRequest,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Обновление access-токена с помощью refresh-токена.
    """
    payload = security.decode_token(token_in.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный refresh-токен"
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    user_id = UUID(user_id_str)

    # (Опционально) Проверить, что юзер еще существует
    user = await db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # 3. Создать новую пару токенов
    new_access_token = security.create_access_token(data={"sub": str(user.id)})
    new_refresh_token = security.create_refresh_token(data={"sub": str(user.id)})

    return schemas.RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token
    )


@router.get("/me", response_model=schemas.UserPublic)
async def get_me(
        current_user: models.User = Depends(get_current_user)
):
    """
    Получение информации о текущем аутентифицированном пользователе.
    Использует dependency `get_current_user`.
    """
    return current_user
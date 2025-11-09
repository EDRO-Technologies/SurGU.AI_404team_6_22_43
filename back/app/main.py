import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config
from alembic import command
import os
from contextlib import asynccontextmanager
import asyncio

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine, Base


def run_migrations():
    """
    Применяет миграции Alembic при старте.
    В production лучше это делать отдельной командой.
    """
    alembic_cfg_path = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")

    if not os.path.exists(alembic_cfg_path):
        print("alembic.ini not found, skipping migrations.")
        print("Running SQLAlchemy create_all() as fallback...")
        print("Tables will be created by lifespan event.")
        return

    print(f"Running Alembic migrations from {alembic_cfg_path}...")
    alembic_cfg = Config(alembic_cfg_path)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    try:
        command.upgrade(alembic_cfg, "head")
        print("Migrations applied successfully.")
    except Exception as e:
        print(f"Failed to apply migrations: {e}")


async def init_db():
    """Создает таблицы в БД"""
    print("Running SQLAlchemy create_all()...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/checked.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код для выполнения при старте
    print("Application startup: Running init_db()...")
    run_migrations() 
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "alembic.ini")):
        await init_db()
    yield
    # Код для выполнения при завершении
    print("Application shutdown.")


# Создание основного экземпляра FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Настройка CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production замените "*" на домен вашего фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутера API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def read_root():
    """
    Корневой эндпоинт для проверки работоспособности.
    """
    return {"message": f"Welcome to {settings.APP_NAME}!"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
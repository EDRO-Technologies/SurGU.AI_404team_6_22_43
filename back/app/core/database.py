from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Создаем асинхронный "движок" для SQLAlchemy
# Он будет управлять подключениями к БД
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True, # Проверять подключение перед каждым запросом
    echo=False # Включите (True) для отладки SQL-запросов
)

# Создаем "фабрику" асинхронных сессий
# Каждая сессия - это отдельный разговор с БД
AsyncSessionFactory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False # Не сбрасывать объекты после коммита
)

# Базовый класс для всех наших моделей (таблиц)
class Base(DeclarativeBase):
    pass

# Dependency для FastAPI: предоставляет сессию в эндпоинты
async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
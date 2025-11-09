from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List

class Settings(BaseSettings):
    """
    Настройки 'back'
    Добавлены AI_SERVICE_URL и API_V1_STR_AI
    Удалены OLLAMA_HOST, CHROMA_HOST, CHROMA_PORT
    """
    APP_NAME: str = "KnowledgeBot API"
    API_V1_STR: str = "/api/v1"

    # Настройки JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    # Настройки базы данных
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str

    # --- НОВОЕ ---
    # Настройки клиента AI-сервиса
    AI_SERVICE_URL: AnyHttpUrl
    API_V1_STR_AI: str

    # --- УДАЛЕНО ---
    # OLLAMA_HOST: AnyHttpUrl
    # CHROMA_HOST: str
    # CHROMA_PORT: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
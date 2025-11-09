# (НОВЫЙ ФАЙЛ)
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    """
    Настройки для AI-сервиса
    """
    APP_NAME: str = "KnowledgeBot AI Service"
    API_V1_STR: str = "/api/v1/ai"

    # Настройки RAG
    OLLAMA_HOST: AnyHttpUrl
    CHROMA_HOST: str
    CHROMA_PORT: int

    EMBEDDING_MODEL_NAME: str = 'all-MiniLM-L6-v2'
    RELEVANCE_THRESHOLD: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
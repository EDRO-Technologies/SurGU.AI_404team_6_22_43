from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    workspaces,
    knowledge,
    query,
    analytics,
    connectors, # Добавлено
    tools,      # Добавлено
    public      # Добавлено
)

# Главный роутер для API v1
api_router = APIRouter()

# 1. Аутентификация
api_router.include_router(auth.router, prefix="/auth", tags=["1. Authentication"])

# 2. Воркспейсы
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["2. Workspaces"])

# 3. База Знаний (префикс /workspaces)
api_router.include_router(knowledge.router, prefix="/workspaces", tags=["3. Knowledge Base"])

# 4. RAG-запросы (внутренние) (префикс /workspaces)
# (query.py также содержит /public/query, поэтому мы не можем дать ему префикс /workspaces)
api_router.include_router(query.router, tags=["4. RAG Query"])

# 5. Публичный API Виджета (префикс /)
api_router.include_router(public.router, prefix="", tags=["5. RAG Query (Public Widget)"])

# 6. Аналитика и HITL (префикс /workspaces)
api_router.include_router(analytics.router, prefix="/workspaces", tags=["6. Analytics & HITL"])

# 7. (Beyond MVP) Коннекторы (префикс /workspaces)
api_router.include_router(connectors.router, prefix="/workspaces", tags=["7. Connectors"])

# 8. (Beyond MVP) Инструменты (Агенты) (префикс /workspaces)
api_router.include_router(tools.router, prefix="/workspaces", tags=["8. Agent Tools"])
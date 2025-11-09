# (НОВЫЙ ФАЙЛ)
from fastapi import APIRouter
from .endpoints import ai

api_router = APIRouter()
api_router.include_router(ai.router, prefix="", tags=["AI Service"])
# (НОВЫЙ ФАЙЛ)
# Этот клиент будет общаться с 'back-ai' сервисом
import httpx
from fastapi import HTTPException, status
from uuid import UUID
from typing import List, Tuple, Optional
import asyncio

from app.core.config import settings
from app.core.database import AsyncSessionFactory
from app import schemas, models  # Используем основные схемы Pydantic из 'back'


class AIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=str(base_url), timeout=300.0)
        print(f"[AI Client] Initialized for {self.base_url}")

    async def _post(self, endpoint: str, json_data: dict) -> dict:
        """Вспомогательный метод для POST-запросов."""
        try:
            response = await self.client.post(endpoint, json=json_data)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            print(f"[AI Client] CRITICAL: Cannot connect to AI service at {self.base_url}: {e}")
            raise HTTPException(status_code=503, detail="AI service is unavailable (Connection Error)")
        except httpx.HTTPStatusError as e:
            print(f"[AI Client] Error from AI service: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code,
                                detail=f"AI Service Error: {e.response.json().get('detail', 'Unknown')}")
        except Exception as e:
            print(f"[AI Client] Unknown error: {e}")
            raise HTTPException(status_code=500, detail=f"Unknown AI client error: {e}")

    # --- Методы для BackgroundTasks ---

    async def process_file(
            self, workspace_id: UUID, source_id: UUID, file_path: str, filename: str
    ):
        """Вызывает /process-file в back-ai."""
        print(f"[AI Client Task] Processing file {filename} (Source ID: {source_id})")
        payload = {
            "workspace_id": str(workspace_id),
            "source_id": str(source_id),
            "file_path": file_path,
            "filename": filename
        }
        try:
            await self._post(f"{settings.API_V1_STR_AI}/process-file", json_data=payload)
            await self._update_source_status(source_id, models.KnowledgeSourceStatusEnum.COMPLETED)
        except Exception as e:
            print(f"[AI Client Task] FAILED processing file {source_id}: {e}")
            await self._update_source_status(source_id, models.KnowledgeSourceStatusEnum.FAILED)

    async def process_qa(
            self, workspace_id: UUID, source_id: UUID, qa_in: schemas.KnowledgeSourceCreateQA
    ):
        """Вызывает /process-qa в back-ai."""
        print(f"[AI Client Task] Processing Q&A (Source ID: {source_id})")
        payload = {
            "workspace_id": str(workspace_id),
            "source_id": str(source_id),
            "qa_in": qa_in.model_dump()
        }
        try:
            await self._post(f"{settings.API_V1_STR_AI}/process-qa", json_data=payload)
            await self._update_source_status(source_id, models.KnowledgeSourceStatusEnum.COMPLETED)
        except Exception as e:
            print(f"[AI Client Task] FAILED processing Q&A {source_id}: {e}")
            await self._update_source_status(source_id, models.KnowledgeSourceStatusEnum.FAILED)

    async def process_article(
            self, workspace_id: UUID, source_id: UUID, article_in: schemas.KnowledgeSourceCreateArticle
    ):
        """Вызывает /process-article в back-ai."""
        print(f"[AI Client Task] Processing Article (Source ID: {source_id})")
        payload = {
            "workspace_id": str(workspace_id),
            "source_id": str(source_id),
            "article_in": article_in.model_dump()
        }
        try:
            await self._post(f"{settings.API_V1_STR_AI}/process-article", json_data=payload)
            await self._update_source_status(source_id, models.KnowledgeSourceStatusEnum.COMPLETED)
        except Exception as e:
            print(f"[AI Client Task] FAILED processing Article {source_id}: {e}")
            await self._update_source_status(source_id, models.KnowledgeSourceStatusEnum.FAILED)

    async def delete_embeddings(self, collection_name: str, source_id: UUID):
        """Вызывает /delete-embeddings в back-ai."""
        print(f"[AI Client Task] Deleting embeddings (Source ID: {source_id})")
        payload = {
            "collection_name": collection_name,
            "source_id": str(source_id)
        }
        try:
            await self._post(f"{settings.API_V1_STR_AI}/delete-embeddings", json_data=payload)
        except Exception as e:
            print(f"[AI Client Task] FAILED deleting embeddings {source_id}: {e}")

    async def _update_source_status(self, source_id: UUID, status: models.KnowledgeSourceStatusEnum):
        """Вспомогательная функция для обновления статуса в БД (в 'back')."""
        async with AsyncSessionFactory() as db:
            try:
                await db.execute(
                    models.KnowledgeSource.__table__.update()
                    .where(models.KnowledgeSource.id == source_id)
                    .values(status=status)
                )
                await db.commit()
                print(f"[AI Client Task] Updated source {source_id} status to {status}")
            except Exception as e:
                print(f"[AI Client Task] CRITICAL: Failed to update DB status for {source_id}: {e}")

    # --- Методы для Эндпоинтов ---

    async def answer_query(
            self, workspace_id: UUID, question: str, session_id: UUID
    ) -> Tuple[str, List[schemas.QueryResponseSource]]:
        """Вызывает /query в back-ai и возвращает (answer, sources)."""
        print(f"[AI Client] Answering query for workspace {workspace_id}")
        payload = {
            "workspace_id": str(workspace_id),
            "question": question,
            "session_id": str(session_id)
        }
        response_json = await self._post(f"{settings.API_V1_STR_AI}/query", json_data=payload)

        answer = response_json.get("answer", "Ошибка: AI-сервис вернул пустой ответ.")
        sources_data = response_json.get("sources", [])

        sources = [schemas.QueryResponseSource(**s) for s in sources_data]
        return answer, sources


# --- Единый экземпляр AIClient ---
ai_client = AIClient(base_url=settings.AI_SERVICE_URL)
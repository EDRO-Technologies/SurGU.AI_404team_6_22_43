# (НОВЫЙ ФАЙЛ)
# Это оригинальный, РАБОЧИЙ 'rag_service.py' из '404team_project/back'
# Он перемещен сюда, в 'back-ai'
import httpx  # (ВАЖНО) Раскомментируем httpx
import chromadb
import asyncio
import torch
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from app.core.config import settings
from app import schemas_ai  # Используем локальные схемы _ai

# --- Конфигурация RAG ---
EMBEDDING_MODEL_NAME = settings.EMBEDDING_MODEL_NAME
OLLAMA_MODEL_NAME = 'llama3:8b-instruct'
RELEVANCE_THRESHOLD = settings.RELEVANCE_THRESHOLD


class RAGService:

    def __init__(self):
        print("[RAG Service] Initializing...")

        # 1. Определение устройства (e.g., RTX 3060)
        if torch.cuda.is_available():
            self.device = 'cuda:0'
            print(f"[RAG Service] Found CUDA device. Using 'cuda:0' for embeddings.")
        else:
            self.device = 'cpu'
            print("[RAG Service] WARNING: CUDA not available. Using 'cpu' for embeddings.")

        # 2. Загрузка Embedding-модели
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=self.device)
            print(f"[RAG Service] Embedding model '{EMBEDDING_MODEL_NAME}' loaded on {self.device}.")
            self.embed_dim = self.embedding_model.get_sentence_embedding_dimension()
            print(f"[RAG Service] Embedding dimension: {self.embed_dim}")
        except Exception as e:
            print(f"[RAG Service] CRITICAL: Failed to load embedding model: {e}")
            raise e

        # 3. (ChromaDB) Инициализация клиента
        try:
            self.chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
            self.chroma_client.heartbeat()
            print(f"[RAG Service] ChromaDB client connected to {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        except Exception as e:
            print(f"[RAG Service] CRITICAL: Failed to connect to ChromaDB: {e}")
            raise e

        # 4. (Ollama) Инициализация HTTP-клиента
        # (Используем ЗАГЛУШКУ из оригинального файла v1, чтобы он работал как раньше)
        self.ollama_client = None
        print(f"[RAG Service] STUB: Ollama client (httpx) is NOT initialized.")

        # --- (ЗАКОММЕНТИРОВАННЫЙ РЕАЛЬНЫЙ КОД) ---
        # self.ollama_client = httpx.AsyncClient(base_url=str(settings.OLLAMA_HOST), timeout=60.0)
        # print(f"[RAG Service] Ollama client initialized for {settings.OLLAMA_HOST}")

    async def get_collection(self, collection_name: str) -> chromadb.Collection:
        """Получает или создает коллекцию в ChromaDB."""
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return collection
        except Exception as e:
            print(f"[Chroma] Error getting/creating collection {collection_name}: {e}")
            raise e

    async def process_and_embed_chunks(
            self,
            collection_name: str,
            source_id: UUID,
            text_chunks: List[str],
            metadata_list: List[dict]
    ):
        """Генерирует эмбеддинги и сохраняет в ChromaDB."""
        print(f"[RAG Service] Processing {len(text_chunks)} chunks for source: {source_id}")
        try:
            # 1. Генерируем эмбеддинги
            embeddings = await asyncio.to_thread(
                self.embedding_model.encode,
                text_chunks,
                show_progress_bar=False,
                device=self.device
            )

            # 2. Дополняем метаданные
            full_metadatas = []
            ids = []
            for i, meta in enumerate(metadata_list):
                meta["source_id"] = str(source_id)
                full_metadatas.append(meta)
                ids.append(f"{source_id}_{i}")

            # 3. Сохраняем в ChromaDB
            collection = await self.get_collection(collection_name)
            collection.add(
                embeddings=embeddings.tolist(),
                documents=text_chunks,
                metadatas=full_metadatas,
                ids=ids
            )
            print(f"[RAG Service] Successfully added {len(ids)} chunks to ChromaDB.")
        except Exception as e:
            print(f"[RAG Service] Error processing chunks for source {source_id}: {e}")
            raise e

    async def delete_embeddings(self, collection_name: str, source_id: UUID):
        """Удаляет эмбеддинги из ChromaDB."""
        print(f"[RAG Service] Deleting embeddings for source: {source_id}")
        try:
            collection = await self.get_collection(collection_name)
            collection.delete(
                where={"source_id": str(source_id)}
            )
            print(f"[RAG Service] Successfully deleted embeddings from ChromaDB.")
        except Exception as e:
            print(f"[RAG Service] Error deleting embeddings for source {source_id}: {e}")
            raise e

    async def answer_query(
            self,
            workspace_id: UUID,
            question: str,
            session_id: UUID
    ) -> Tuple[str, List[schemas_ai.QueryResponseSource], Optional[UUID]]:
        """
        Полный RAG-пайплайн.
        (Возвращает (answer, sources, ticket_id) - ticket_id будет None,
        но мы сохраняем сигнатуру из v1)
        """
        collection_name = str(workspace_id)
        print(f"[RAG Service] Answering query for workspace {workspace_id}")

        try:
            # 1. Создаем эмбеддинг для вопроса
            query_embedding = await asyncio.to_thread(
                self.embedding_model.encode,
                [question],
                device=self.device
            )

            # 2. Ищем релевантные чанки
            collection = await self.get_collection(collection_name)
            search_results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=3
            )

            # 3. Проверяем релевантность
            distances = search_results.get("distances", [[]])[0]

            if not distances or distances[0] > RELEVANCE_THRESHOLD:
                print(
                    f"[RAG Service] No relevant context found. (Min distance: {distances[0] if distances else 'N/A'})")
                return (
                    "Я не нашел информации по вашему вопросу. Ваш вопрос записан, и администратор скоро на него ответит.",
                    [],
                    None  # ticket_id (логика v1)
                )

            # 4. Формируем контекст и промпт
            context = ""
            sources: List[schemas_ai.QueryResponseSource] = []

            doc_chunks = search_results.get("documents", [[]])[0]
            metadatas = search_results.get("metadatas", [[]])[0]

            for i in range(len(doc_chunks)):
                if distances[i] <= RELEVANCE_THRESHOLD:
                    chunk = doc_chunks[i]
                    meta = metadatas[i]
                    source_name = meta.get('source_name', 'Unknown')
                    page = meta.get('page')

                    context += f"Документ: '{source_name}', стр. {page if page else 'N/A'}:\n"
                    context += f"\"{chunk}\"\n\n"

                    sources.append(schemas_ai.QueryResponseSource(
                        name=source_name,
                        page=page,
                        text_chunk=chunk
                    ))

            if not sources:
                print("[RAG Service] Context filtered out by threshold.")
                return ("Я не нашел информации по вашему вопросу...", [], None)

            # 5. Промпт-инжиниринг
            prompt = f"""Ты - ИИ-ассистент. Используй ТОЛЬКО приведенный ниже контекст, чтобы ответить на вопрос.
Цитируй источники в формате [Источник: Название документа, стр. X].
Если ответ в контексте не найден, скажи "Я не нашел информации по вашему вопросу".

[Контекст]
{context}
[/Контекст]

[Вопрос]
{question}
"""

            # 6. (Ollama) Получаем ответ (ЗАГЛУШКА ИЗ v1)
            if not self.ollama_client:
                print(f"[RAG Service] STUB: LLM call is commented out.")
                stub_answer = f"Это заглушка. LLM не вызывалась.\n\nНайденный контекст:\n{context}"
                answer = stub_answer
                print(f"[RAG Service] Stub Answer generated.")
                return answer, sources, None  # Успешный ответ

            # --- (РЕАЛЬНЫЙ КОД v1, ЗАКОММЕНТИРОВАН) ---
            # print(f"[RAG Service] Sending prompt to Ollama (model: {OLLAMA_MODEL_NAME})...")
            # ollama_response = await self.ollama_client.post(
            #     "/api/generate",
            #     json={ "model": OLLAMA_MODEL_NAME, "prompt": prompt, "stream": False }
            # )
            # ollama_response.raise_for_status()
            # answer = ollama_response.json().get("response", "Ошибка: получен пустой ответ от LLM.")
            # print(f"[RAG Service] Answer generated: '{answer[:100]}...'")
            # return answer, sources, None
            # --- (КОНЕЦ РЕАЛЬНОГО КОДА) ---

        except httpx.ConnectError as e:
            print(f"[RAG Service] CRITICAL: Cannot connect to Ollama: {e}")
            return (f"Ошибка: не могу подключиться к сервису LLM ({e}).", [], None)
        except Exception as e:
            print(f"[RAG Service] Error during query: {e}")
            return (f"Произошла внутренняя ошибка при обработке вашего запроса: {e}", [], None)


# --- Единый экземпляр RAGService ---
try:
    rag_service = RAGService()
except Exception as e:
    print(f"FATAL: Failed to initialize RAGService. Application might not work. Error: {e}")
    rag_service = None
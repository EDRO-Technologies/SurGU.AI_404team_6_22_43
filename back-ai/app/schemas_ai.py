# (НОВЫЙ ФАЙЛ)
# Схемы Pydantic, которые использует только 'back-ai'
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID

# Эти схемы дублируют часть из 'back/app/schemas.py',
class KnowledgeSourceCreateQA(BaseModel):
    question: str
    answer: str

class KnowledgeSourceCreateArticle(BaseModel):
    title: str
    content: str

# --- Схемы для API 'back-ai' ---

class FileProcessingRequest(BaseModel):
    workspace_id: UUID
    source_id: UUID
    file_path: str
    filename: str

class QASProcessingRequest(BaseModel):
    workspace_id: UUID
    source_id: UUID
    qa_in: KnowledgeSourceCreateQA

class ArticleProcessingRequest(BaseModel):
    workspace_id: UUID
    source_id: UUID
    article_in: KnowledgeSourceCreateArticle

class EmbeddingDeleteRequest(BaseModel):
    collection_name: str
    source_id: UUID

# --- Схемы для RAG-запросов ---

class QueryRequest(BaseModel):
    workspace_id: UUID
    question: str
    session_id: UUID

class QueryResponseSource(BaseModel):
    name: str
    page: Optional[int] = None
    text_chunk: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[QueryResponseSource]
from pydantic import BaseModel, EmailStr, Field, AnyHttpUrl
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from app.models import UserRoleEnum, KnowledgeSourceTypeEnum, KnowledgeSourceStatusEnum, TicketStatusEnum, \
    ConnectorTypeEnum, ToolApiMethodEnum


# --- Вспомогательные схемы ---

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenData(BaseModel):
    user_id: Optional[UUID] = None


# --- 1. Auth API ---

class UserCreate(BaseModel):
    full_name: str = Field(..., example="Иван Иванов")
    email: EmailStr = Field(..., example="admin@company.com")
    password: str = Field(..., min_length=8, example="MyComplexP@ssw0rd!")
    organization_name: str = Field(..., example="Газпром")


class UserPublic(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    organization_id: UUID

    class Config:
        from_attributes = True  # (v2 - ДОБАВЛЕНО)


class OrganizationPublic(BaseModel):
    id: UUID
    name: str

    class Config:  # (v2 - Добавлено для согласованности)
        from_attributes = True


class RegisterResponse(BaseModel):
    user: UserPublic
    organization: OrganizationPublic
    access_token: str
    refresh_token: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user: UserPublic
    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


# --- 2. Workspace API ---

class WorkspaceCreate(BaseModel):
    name: str = Field(..., example="Бот по технике безопасности")
    description: Optional[str] = Field(None, example="Отвечает на вопросы по внутренним регламентам безопасности")


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspacePublic(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True  # orm_mode = True


class WorkspaceUser(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    role: UserRoleEnum


class WorkspaceUserInvite(BaseModel):
    email: EmailStr
    role: UserRoleEnum = Field(..., example="Editor")


class WorkspaceUserUpdateRole(BaseModel):
    role: UserRoleEnum


# --- 3. Knowledge Base API ---

# POST /qa
class KnowledgeSourceCreateQA(BaseModel):
    question: str = Field(..., example="За сколько дней подавать заявление на отпуск?")
    answer: str = Field(..., example="Заявление на отпуск необходимо подавать за 2 недели.")


# POST /article
class KnowledgeSourceCreateArticle(BaseModel):
    title: str = Field(..., example="Политика работы из дома")
    content: str = Field(..., example="Сотрудники могут работать из дома до 2 дней в неделю...")


# GET /knowledge (список)
class KnowledgeSourcePublic(BaseModel):
    id: UUID
    type: KnowledgeSourceTypeEnum
    name: str
    status: KnowledgeSourceStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


# GET /knowledge/{id} (детали)
class KnowledgeSourceContentQA(BaseModel):
    question: str
    answer: str


class KnowledgeSourceContentArticle(BaseModel):
    title: str
    content: str


class KnowledgeSourceDetail(KnowledgeSourcePublic):
    content: Optional[Union[KnowledgeSourceContentQA, KnowledgeSourceContentArticle, Dict[str, Any]]] = None


# PUT /knowledge/{id} (обновление)
class KnowledgeSourceUpdateQA(BaseModel):
    question: str
    answer: str


class KnowledgeSourceUpdateArticle(BaseModel):
    title: str
    content: str


# --- 4. RAG API ---

class QueryRequest(BaseModel):
    question: str = Field(..., example="За сколько дней подавать на отпуск?")
    session_id: UUID = Field(..., example="chat-session-uuid-456")


class QueryResponseSource(BaseModel):
    name: str
    page: Optional[int] = None
    text_chunk: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[QueryResponseSource]
    ticket_id: Optional[UUID] = None


# --- 5. Public Widget API ---

class PublicQueryRequest(BaseModel):
    workspace_id: UUID = Field(..., example="workspace-uuid-789")
    question: str = Field(..., example="Сколько дней длится отпуск?")
    session_id: UUID = Field(..., example="public-chat-session-uuid-123")


# Ответ: QueryResponse

# --- 6. Analytics & HITL API ---

class AnalyticsTopQuestion(BaseModel):
    question: str
    count: int


class AnalyticsTopUnansweredQuestion(AnalyticsTopQuestion):
    ticket_id: Optional[UUID] = None  # Может быть несколько тикетов на 1 вопрос


class AnalyticsResponse(BaseModel):
    total_queries: int
    answered_queries: int
    unanswered_queries: int
    top_questions: List[AnalyticsTopQuestion]
    top_unanswered_questions: List[AnalyticsTopUnansweredQuestion]


class TicketPublic(BaseModel):
    id: UUID
    question: str
    status: TicketStatusEnum
    created_at: datetime
    session_id: UUID

    class Config:  # (v2 - Добавлено)
        from_attributes = True


class TicketResolve(BaseModel):
    answer: str = Field(..., example="Да, ДМС предоставляется...")
    add_to_knowledge_base: bool = Field(..., example=True)


class TicketResolvedResponse(BaseModel):
    id: UUID
    question: str
    status: TicketStatusEnum
    created_at: datetime
    resolved_at: Optional[datetime]
    answer: str
    new_source_id: Optional[UUID]


# --- 7. Connectors & Tools API ---

class ConnectorAuthDetails(BaseModel):
    url: Optional[AnyHttpUrl] = None
    api_token: Optional[str] = None
    # ... другие поля для GDrive...


class ConnectorCreate(BaseModel):
    type: ConnectorTypeEnum
    display_name: str = Field(..., example="База знаний HR (Confluence)")
    auth_details: ConnectorAuthDetails
    sync_schedule: Optional[str] = Field("daily", example="daily")


class ConnectorPublic(BaseModel):
    id: UUID
    type: ConnectorTypeEnum
    display_name: str
    status: str
    last_sync: Optional[datetime]

    class Config:
        from_attributes = True


class SyncResponse(BaseModel):
    status: str = "SYNC_STARTED"
    message: str = "Синхронизация успешно запущена."


class AudioQueryResponse(QueryResponse):
    transcribed_question: str


class ToolParameterSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str]


class ToolCreate(BaseModel):
    name: str = Field(..., example="book_meeting_room")
    description: str = Field(..., example="Используй этот инструмент, чтобы забронировать переговорную комнату.")
    api_endpoint: AnyHttpUrl = Field(..., example="https://api.calendar.com/book")
    api_method: ToolApiMethodEnum = Field(ToolApiMethodEnum.POST, example="POST")
    parameters_schema: ToolParameterSchema


class ToolPublic(ToolCreate):
    id: UUID

    class Config:
        from_attributes = True
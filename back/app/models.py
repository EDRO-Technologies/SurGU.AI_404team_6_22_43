import uuid
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Enum, JSON, Text, Boolean, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


# --- Enum классы для полей в БД ---

class UserRoleEnum(str, enum.Enum):
    ADMIN = "Admin"
    EDITOR = "Editor"
    USER = "User"  # Конечный пользователь (из плана), хотя API спека фокусируется на Admin/Editor


class KnowledgeSourceTypeEnum(str, enum.Enum):
    FILE = "FILE"
    QNA = "Q&A"
    ARTICLE = "ARTICLE"
    CONNECTOR = "CONNECTOR"


class KnowledgeSourceStatusEnum(str, enum.Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TicketStatusEnum(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ConnectorTypeEnum(str, enum.Enum):
    CONFLUENCE = "CONFLUENCE"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"


class ToolApiMethodEnum(str, enum.Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"


# --- Модели Таблиц ---

class Organization(Base):
    """
    Модель Организации (Tenant).
    """
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    users = relationship("User", back_populates="organization")
    workspaces = relationship("Workspace", back_populates="organization")


class User(Base):
    """
    Модель Пользователя (Админ, Редактор).
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    organization = relationship("Organization", back_populates="users")
    workspaces = relationship("WorkspaceMembership", back_populates="user")  # Связь через таблицу членства


class Workspace(Base):
    """
    Модель Рабочего Пространства (AI-ассистент).
    """
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    organization = relationship("Organization", back_populates="workspaces")
    users = relationship("WorkspaceMembership", back_populates="workspace")  # Связь через таблицу членства
    knowledge_sources = relationship("KnowledgeSource", back_populates="workspace", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="workspace", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="workspace", cascade="all, delete-orphan")
    connectors = relationship("Connector", back_populates="workspace", cascade="all, delete-orphan")
    tools = relationship("Tool", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMembership(Base):
    """
    Ассоциативная таблица (многие-ко-многим)
    Связывает Пользователей и Воркспейсы, определяя роль.
    """
    __tablename__ = "workspace_memberships"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), primary_key=True)
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.EDITOR)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user = relationship("User", back_populates="workspaces")
    workspace = relationship("Workspace", back_populates="users")


class KnowledgeSource(Base):
    """
    Модель Источника Знаний (Файл, Q&A, Статья).
    """
    __tablename__ = "knowledge_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    type = Column(Enum(KnowledgeSourceTypeEnum), nullable=False)
    name = Column(String(512), nullable=False)  # Имя файла или заголовок статьи/Q&A
    status = Column(Enum(KnowledgeSourceStatusEnum), nullable=False, default=KnowledgeSourceStatusEnum.PROCESSING)

    # JSON поле для хранения Q&A или контента Статьи
    content = Column(JSON, nullable=True)

    # Путь к файлу в томе (volume) file_storage
    file_path = Column(String(1024), nullable=True)

    # Связь с коннектором (если источник пришел оттуда)
    connector_id = Column(UUID(as_uuid=True), ForeignKey("connectors.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    workspace = relationship("Workspace", back_populates="knowledge_sources")
    connector = relationship("Connector", back_populates="knowledge_sources")
    # Примечание: Векторы (чанки) хранятся в ChromaDB.
    # Связь здесь логическая, по `knowledge_source_id` в метаданных Chroma.


class ChatSession(Base):
    """
    Модель Сессии Чата (для истории).
    """
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    workspace = relationship("Workspace", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Модель одного Сообщения в чате (вопрос-ответ).
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # JSONB со списком источников

    # Связь с созданным тикетом
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    session = relationship("ChatSession", back_populates="messages")
    ticket = relationship("Ticket", back_populates="chat_message")


class Ticket(Base):
    """
    Модель Тикета (Human-in-the-Loop).
    Создается, когда бот не может ответить.
    """
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    question = Column(Text, nullable=False)
    status = Column(Enum(TicketStatusEnum), nullable=False, default=TicketStatusEnum.OPEN)

    # Ответ от Редактора
    answer = Column(Text, nullable=True)

    # ID нового источника знаний, если он был создан при решении тикета
    new_source_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_sources.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Связи
    workspace = relationship("Workspace", back_populates="tickets")
    chat_message = relationship("ChatMessage", back_populates="ticket", uselist=False)


class Connector(Base):
    """
    Модель Коннектора (Confluence, GDrive)
    """
    __tablename__ = "connectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    type = Column(Enum(ConnectorTypeEnum), nullable=False)
    display_name = Column(String(255), nullable=False)

    # Зашифрованные credentials
    auth_details = Column(JSON, nullable=False)

    sync_schedule = Column(String(100), nullable=True, default="daily")
    status = Column(String(100), nullable=False, default="ACTIVE")
    last_sync = Column(DateTime(timezone=True), nullable=True)

    # Связи
    workspace = relationship("Workspace", back_populates="connectors")
    knowledge_sources = relationship("KnowledgeSource", back_populates="connector")


class Tool(Base):
    """
    Модель Инструмента (Agent Tool)
    """
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)

    name = Column(String(255), nullable=False)  # e.g., "book_meeting_room"
    description = Column(Text, nullable=False)
    api_endpoint = Column(String(1024), nullable=False)
    api_method = Column(Enum(ToolApiMethodEnum), nullable=False, default=ToolApiMethodEnum.POST)
    parameters_schema = Column(JSON, nullable=False)  # JSON Schema

    # Связи
    workspace = relationship("Workspace", back_populates="tools")
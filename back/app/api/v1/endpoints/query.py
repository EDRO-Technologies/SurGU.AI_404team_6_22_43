from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.core.database import get_db_session
from app.api.v1.dependencies import get_workspace_member
from app.services.ai_client import ai_client
from app import schemas, models

router = APIRouter()


async def get_or_create_session(db: AsyncSession, workspace_id: UUID, session_id: UUID) -> models.ChatSession:
    """Находит или создает сессию чата в БД."""
    result = await db.execute(
        select(models.ChatSession)
        .where(
            models.ChatSession.id == session_id,
            models.ChatSession.workspace_id == workspace_id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        session = models.ChatSession(id=session_id, workspace_id=workspace_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def create_ticket_and_message(
        db: AsyncSession,
        session: models.ChatSession,
        question: str,
        answer: str
) -> models.Ticket:
    """Создает Тикет и Сообщение в БД, когда ответ не найден."""
    # 1. Создаем Тикет
    db_ticket = models.Ticket(
        workspace_id=session.workspace_id,
        question=question,
        status=models.TicketStatusEnum.OPEN
    )
    db.add(db_ticket)
    await db.flush()

    # 2. Создаем Сообщение, связанное с тикетом
    db_message = models.ChatMessage(
        session_id=session.id,
        question=question,
        answer=answer,
        sources=[],
        ticket_id=db_ticket.id
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_ticket)
    return db_ticket


@router.post(
    "/workspaces/{workspace_id}/query",
    response_model=schemas.QueryResponse,
    tags=["4. RAG Query"]
)
async def query_workspace(
        workspace_id: UUID,
        query_in: schemas.QueryRequest,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
):
    """
    Отправка вопроса боту от имени администратора/редактора.
    """
    # 1. Найти или создать сессию чата
    session = await get_or_create_session(db, workspace_id, query_in.session_id)

    # 2. Вызов RAG-пайплайна через ai_client
    try:
        answer, sources = await ai_client.answer_query(
            workspace_id=workspace_id,
            question=query_in.question,
            session_id=query_in.session_id
        )
    except HTTPException as e:
        raise e # Пробрасываем ошибки 503, 500 и т.д. от ai_client

    ticket_id = None

    # 3. Логика "Не найдено" / "Создание тикета"
    if not sources:
        db_ticket = await create_ticket_and_message(
            db=db,
            session=session,
            question=query_in.question,
            answer=answer
        )
        ticket_id = db_ticket.id
    else:
        # 4. Логируем успешный ответ
        db_message = models.ChatMessage(
            session_id=session.id,
            question=query_in.question,
            answer=answer,
            sources=[s.model_dump() for s in sources],
            ticket_id=None
        )
        db.add(db_message)
        await db.commit()

    return schemas.QueryResponse(
        answer=answer,
        sources=sources,
        ticket_id=ticket_id
    )


@router.post(
    "/public/query",
    response_model=schemas.QueryResponse,
    tags=["5. RAG Query (Public Widget)"]
)
async def public_query(
        query_in: schemas.PublicQueryRequest,
        db: AsyncSession = Depends(get_db_session)
):
    """
    Публичный эндпоинт для отправки запросов из виджета.
    """
    # 1. Проверить, что workspace_id существует
    result = await db.execute(select(models.Workspace.id).where(models.Workspace.id == query_in.workspace_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found")

    # 2. Найти или создать сессию
    session = await get_or_create_session(db, query_in.workspace_id, query_in.session_id)

    # 3. Вызов RAG-пайплайна через ai_client
    try:
        answer, sources = await ai_client.answer_query(
            workspace_id=query_in.workspace_id,
            question=query_in.question,
            session_id=query_in.session_id
        )
    except HTTPException as e:
        raise e

    ticket_id = None

    # 4. Логика "Не найдено" / "Создание тикета"
    if not sources:
        db_ticket = await create_ticket_and_message(
            db=db,
            session=session,
            question=query_in.question,
            answer=answer
        )
        ticket_id = db_ticket.id
    else:
        # 5. Логируем успешный ответ
        db_message = models.ChatMessage(
            session_id=session.id,
            question=query_in.question,
            answer=answer,
            sources=[s.model_dump() for s in sources],
            ticket_id=None
        )
        db.add(db_message)
        await db.commit()

    return schemas.QueryResponse(
        answer=answer,
        sources=sources,
        ticket_id=ticket_id
    )
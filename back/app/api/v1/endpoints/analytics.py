# 'analytics' эндпоинт
# Заменяет `rag_service` на `ai_client` в `resolve_ticket`

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from sqlalchemy.sql.expression import text
from typing import List
from uuid import UUID
from datetime import datetime, timedelta, timezone

from app.core.database import get_db_session
from app.api.v1.dependencies import get_workspace_member, get_workspace_editor
from app import schemas, models
# (ИЗМЕНЕНО) Импортируем ai_client
from app.services.ai_client import ai_client

router = APIRouter()


@router.get(
    "/{workspace_id}/analytics",
    response_model=schemas.AnalyticsResponse
)
async def get_analytics(
        workspace_id: UUID,
        period: str = "7d",
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
):
    """
    Получение агрегированных данных для дашборда аналитики.
    """
    if period == "24h":
        start_date = datetime.now() - timedelta(hours=24)
    elif period == "30d":
        start_date = datetime.now() - timedelta(days=30)
    else:
        start_date = datetime.now() - timedelta(days=7)

    print(f"Getting analytics for workspace {workspace_id} since {start_date}")

    total_queries = 150
    unanswered_queries = 30
    top_questions = [
        schemas.AnalyticsTopQuestion(question="Сколько дней отпуск?", count=25),
        schemas.AnalyticsTopQuestion(question="Как оформить больничный?", count=15)
    ]
    top_unanswered_questions = [
        schemas.AnalyticsTopUnansweredQuestion(
            question="Есть ли ДМС?",
            count=10,
            ticket_id=UUID(int=1)
        )
    ]

    return schemas.AnalyticsResponse(
        total_queries=total_queries,
        answered_queries=total_queries - unanswered_queries,
        unanswered_queries=unanswered_queries,
        top_questions=top_questions,
        top_unanswered_questions=top_unanswered_questions
    )


@router.get(
    "/{workspace_id}/tickets",
    response_model=List[schemas.TicketPublic]
)
async def get_tickets(
        workspace_id: UUID,
        status: schemas.TicketStatusEnum = schemas.TicketStatusEnum.OPEN,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
):
    """
    (Оставлена заглушка из v1)
    Получение списка "тикетов".
    """
    query = (
        select(models.Ticket)
        .where(
            models.Ticket.workspace_id == workspace_id,
            models.Ticket.status == status
        )
        .order_by(models.Ticket.created_at.desc())
    )
    result = await db.execute(query)
    tickets = result.scalars().all()

    response = []
    for t in tickets:
        response.append(schemas.TicketPublic(
            id=t.id,
            question=t.question,
            status=t.status,
            created_at=t.created_at,
            session_id=UUID(int=1) # (STUB)
        ))

    if not response and status == schemas.TicketStatusEnum.OPEN:
        return [
            schemas.TicketPublic(
                id=UUID(int=1),
                question="Есть ли ДМС? (Stub)",
                status=schemas.TicketStatusEnum.OPEN,
                created_at=datetime.now(),
                session_id=UUID(int=2)
            )
        ]

    return response


@router.post(
    "/{workspace_id}/tickets/{ticket_id}/resolve",
    response_model=schemas.TicketResolvedResponse
)
async def resolve_ticket(
        workspace_id: UUID,
        ticket_id: UUID,
        resolve_in: schemas.TicketResolve,
        background_tasks: BackgroundTasks, # (ИЗМЕНЕНО) Добавлены
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """
    Решение тикета. Использует ai_client для добавления Q&A в Базу Знаний.
    """
    # 1. Найти тикет
    result = await db.execute(
        select(models.Ticket)
        .where(
            models.Ticket.id == ticket_id,
            models.Ticket.workspace_id == workspace_id
        )
    )
    db_ticket = result.scalar_one_or_none()

    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if db_ticket.status == models.TicketStatusEnum.RESOLVED:
        raise HTTPException(status_code=400, detail="Ticket is already resolved")

    # 2. Обновить тикет
    db_ticket.status = models.TicketStatusEnum.RESOLVED
    db_ticket.answer = resolve_in.answer
    db_ticket.resolved_at = datetime.now(timezone.utc)

    new_source_id = None

    # 3. (ИЗМЕНЕНО) Если add_to_knowledge_base == True
    if resolve_in.add_to_knowledge_base:
        # a. Создаем KnowledgeSource (здесь, в 'back')
        db_source = models.KnowledgeSource(
            workspace_id=workspace_id,
            type=models.KnowledgeSourceTypeEnum.QNA,
            name=db_ticket.question[:255],
            status=models.KnowledgeSourceStatusEnum.PROCESSING, # Ставим PROCESSING
            content={"question": db_ticket.question, "answer": resolve_in.answer}
        )
        db.add(db_source)
        await db.flush()

        new_source_id = db_source.id
        db_ticket.new_source_id = new_source_id

        # b. (ИЗМЕНЕНО) Вызываем RAG-сервис (ai_client) для эмбеддинга (фоном)
        qa_schema = schemas.KnowledgeSourceCreateQA(
            question=db_ticket.question,
            answer=resolve_in.answer
        )
        background_tasks.add_task(
            ai_client.process_qa,
            workspace_id=workspace_id,
            source_id=db_source.id,
            qa_in=qa_schema
        )
        # ai_client сам обновит статус на COMPLETED/FAILED

    await db.commit()
    await db.refresh(db_ticket)

    return schemas.TicketResolvedResponse(
        id=db_ticket.id,
        question=db_ticket.question,
        status=db_ticket.status,
        created_at=db_ticket.created_at,
        resolved_at=db_ticket.resolved_at,
        answer=db_ticket.answer,
        new_source_id=new_source_id
    )
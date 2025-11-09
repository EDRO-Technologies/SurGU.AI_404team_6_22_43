from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from uuid import UUID
import os
import aiofiles

from app.core.database import get_db_session, AsyncSessionFactory
from app.api.v1.dependencies import get_workspace_editor
from app.services.ai_client import ai_client
from app import schemas, models

router = APIRouter()

FILE_STORAGE_PATH = "/app/storage"
os.makedirs(FILE_STORAGE_PATH, exist_ok=True)


@router.post(
    "/{workspace_id}/knowledge/upload",
    response_model=schemas.KnowledgeSourcePublic,
    status_code=status.HTTP_202_ACCEPTED
)
async def upload_knowledge_file(
        workspace_id: UUID,
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """
    Загрузка файла. Запускает обработку в фоновом режиме через ai_client.
    """
    # 1. Сохраняем файл
    safe_filename = f"{workspace_id}_{UUID(bytes=os.urandom(16))}_{file.filename}"
    file_path = os.path.join(FILE_STORAGE_PATH, safe_filename)

    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2. Создаем запись в БД со статусом 'PROCESSING'
    db_source = models.KnowledgeSource(
        workspace_id=workspace_id,
        type=models.KnowledgeSourceTypeEnum.FILE,
        name=file.filename,
        status=models.KnowledgeSourceStatusEnum.PROCESSING,
        file_path=file_path
    )
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)

    # 3. Запускаем background task через ai_client
    background_tasks.add_task(
        ai_client.process_file,
        workspace_id=workspace_id,
        source_id=db_source.id,
        file_path=file_path,
        filename=file.filename
    )

    return db_source


@router.post(
    "/{workspace_id}/knowledge/qa",
    response_model=schemas.KnowledgeSourcePublic,
    status_code=status.HTTP_202_ACCEPTED
)
async def add_knowledge_qa(
        workspace_id: UUID,
        qa_in: schemas.KnowledgeSourceCreateQA,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """
    Добавление Q&A. Запускает обработку в фоне через ai_client.
    """
    # 1. Создаем KnowledgeSource в БД
    db_source = models.KnowledgeSource(
        workspace_id=workspace_id,
        type=models.KnowledgeSourceTypeEnum.QNA,
        name=qa_in.question[:255],
        status=models.KnowledgeSourceStatusEnum.PROCESSING,
        content={"question": qa_in.question, "answer": qa_in.answer}
    )
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)

    # 2. Запускаем task для эмбеддинга через ai_client
    background_tasks.add_task(
        ai_client.process_qa,
        workspace_id=workspace_id,
        source_id=db_source.id,
        qa_in=qa_in
    )

    return db_source


@router.post(
    "/{workspace_id}/knowledge/article",
    response_model=schemas.KnowledgeSourcePublic,
    status_code=status.HTTP_202_ACCEPTED
)
async def add_knowledge_article(
        workspace_id: UUID,
        article_in: schemas.KnowledgeSourceCreateArticle,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """
    Добавление Статьи. Запускает обработку в фоне через ai_client.
    """
    # 1. Создаем в БД
    db_source = models.KnowledgeSource(
        workspace_id=workspace_id,
        type=models.KnowledgeSourceTypeEnum.ARTICLE,
        name=article_in.title,
        status=models.KnowledgeSourceStatusEnum.PROCESSING,
        content={"title": article_in.title, "content": article_in.content}
    )
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)

    # 2. Запускаем task для эмбеддинга через ai_client
    background_tasks.add_task(
        ai_client.process_article,
        workspace_id=workspace_id,
        source_id=db_source.id,
        article_in=article_in
    )

    return db_source


@router.get(
    "/{workspace_id}/knowledge",
    response_model=List[schemas.KnowledgeSourcePublic]
)
async def get_knowledge_sources(
        workspace_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """Получение списка всех источников знаний."""
    query = (
        select(models.KnowledgeSource)
        .where(models.KnowledgeSource.workspace_id == workspace_id)
        .order_by(models.KnowledgeSource.created_at.desc())
    )
    result = await db.execute(query)
    sources = result.scalars().all()
    return sources


@router.get(
    "/{workspace_id}/knowledge/{source_id}",
    response_model=schemas.KnowledgeSourceDetail
)
async def get_knowledge_source_detail(
        workspace_id: UUID,
        source_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """Получение детальной информации об одном источнике."""
    result = await db.execute(
        select(models.KnowledgeSource)
        .where(
            models.KnowledgeSource.id == source_id,
            models.KnowledgeSource.workspace_id == workspace_id
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")

    return source


@router.put(
    "/{workspace_id}/knowledge/{source_id}",
    response_model=schemas.KnowledgeSourceDetail,
    status_code=status.HTTP_202_ACCEPTED
)
async def update_knowledge_source(
        workspace_id: UUID,
        source_id: UUID,
        update_data: schemas.KnowledgeSourceUpdateQA,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """
    Обновление Q&A. Использует ai_client для удаления и пере-индексации.
    """
    result = await db.execute(
        select(models.KnowledgeSource)
        .where(
            models.KnowledgeSource.id == source_id,
            models.KnowledgeSource.workspace_id == workspace_id
        )
    )
    db_source = result.scalar_one_or_none()

    if not db_source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")

    if db_source.type not in [models.KnowledgeSourceTypeEnum.QNA, models.KnowledgeSourceTypeEnum.ARTICLE]:
        raise HTTPException(status_code=400, detail="Cannot update a FILE source. Please delete and re-upload.")

    # 1. Удаляем старые эмбеддинги через ai_client (фоном)
    background_tasks.add_task(
        ai_client.delete_embeddings,
        collection_name=str(workspace_id),
        source_id=source_id
    )

    # 2. Обновляем контент в БД и ставим статус PROCESSING
    if db_source.type == models.KnowledgeSourceTypeEnum.QNA:
        db_source.content = {"question": update_data.question, "answer": update_data.answer}
        db_source.name = update_data.question[:255]
        db_source.status = models.KnowledgeSourceStatusEnum.PROCESSING

        # 3. Запускаем фоновую задачу re-process через ai_client
        background_tasks.add_task(
            ai_client.process_qa,
            workspace_id=workspace_id,
            source_id=db_source.id,
            qa_in=update_data
        )

    await db.commit()
    await db.refresh(db_source)

    return db_source


@router.delete(
    "/{workspace_id}/knowledge/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_knowledge_source(
        workspace_id: UUID,
        source_id: UUID,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_editor)
):
    """
    Удаление источника. Использует ai_client для удаления эмбеддингов.
    """
    result = await db.execute(
        select(models.KnowledgeSource)
        .where(
            models.KnowledgeSource.id == source_id,
            models.KnowledgeSource.workspace_id == workspace_id
        )
    )
    db_source = result.scalar_one_or_none()

    if not db_source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")

    # 1. Удаляем эмбеддинги из ChromaDB через ai_client (фоном)
    background_tasks.add_task(
        ai_client.delete_embeddings,
        collection_name=str(workspace_id),
        source_id=source_id
    )

    # 2. (Фоном) Удаляем файл (логика остается здесь)
    if db_source.type == models.KnowledgeSourceTypeEnum.FILE and db_source.file_path:
        def delete_file(path: str):
            try:
                os.remove(path)
                print(f"[Task] Deleted file: {path}")
            except OSError as e:
                print(f"[Task] Error deleting file {path}: {e}")
        background_tasks.add_task(delete_file, path=db_source.file_path)

    # 3. Удаляем из БД
    await db.delete(db_source)
    await db.commit()

    return None
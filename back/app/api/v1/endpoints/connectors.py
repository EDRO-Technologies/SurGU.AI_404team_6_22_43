from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.core.database import get_db_session
from app.api.v1.dependencies import get_workspace_admin
from app import schemas, models

router = APIRouter()


@router.post(
    "/{workspace_id}/connectors",
    response_model=schemas.ConnectorPublic,
    status_code=status.HTTP_201_CREATED
)
async def create_connector(
        workspace_id: UUID,
        connector_in: schemas.ConnectorCreate,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Добавление "Коннектора" (Confluence, Google Drive).
    """
    print(f"Creating connector {connector_in.type} for workspace {workspace_id}")

    # (STUB) Логика:
    # 1. Зашифровать auth_details (используя settings.SECRET_KEY)
    encrypted_auth = connector_in.auth_details.model_dump()  # (Заглушка)

    # 2. Сохранить в БД
    db_connector = models.Connector(
        workspace_id=workspace_id,
        type=connector_in.type,
        display_name=connector_in.display_name,
        auth_details=encrypted_auth,  # (Должны быть зашифрованы)
        sync_schedule=connector_in.sync_schedule,
        status="ACTIVE"
    )
    db.add(db_connector)
    await db.commit()
    await db.refresh(db_connector)

    # 3. (STUB) Запустить первую синхронизацию в фоне
    print(f"TODO: Start initial sync for connector {db_connector.id}")

    return db_connector


@router.post(
    "/{workspace_id}/connectors/{connector_id}/sync",
    response_model=schemas.SyncResponse
)
async def sync_connector(
        workspace_id: UUID,
        connector_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Принудительный запуск синхронизации коннектора.
    """
    # (STUB) 1. Найти коннектор
    result = await db.execute(select(models.Connector).where(models.Connector.id == connector_id,
                                                             models.Connector.workspace_id == workspace_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Connector not found")

    # (STUB) 2. Запустить фоновую задачу синхронизации
    print(f"TODO: Start background sync for connector {connector_id}")

    return schemas.SyncResponse(
        status="SYNC_STARTED",
        message="Синхронизация успешно запущена."
    )


@router.get(
    "/{workspace_id}/connectors",
    response_model=List[schemas.ConnectorPublic]
)
async def get_connectors(
        workspace_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Список всех коннекторов в workspace.
    """
    query = select(models.Connector).where(models.Connector.workspace_id == workspace_id)
    result = await db.execute(query)
    connectors = result.scalars().all()

    return connectors


@router.delete(
    "/{workspace_id}/connectors/{connector_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_connector(
        workspace_id: UUID,
        connector_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Удаление коннектора.
    """
    # (STUB) 1. Найти коннектор
    result = await db.execute(select(models.Connector).where(models.Connector.id == connector_id,
                                                             models.Connector.workspace_id == workspace_id))
    db_connector = result.scalar_one_or_none()

    if not db_connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    # (STUB) 2. Удалить все связанные KnowledgeSource (и их эмбеддинги)
    print(f"TODO: Delete all KnowledgeSources and embeddings for connector {connector_id}")

    # 3. Удалить сам коннектор
    await db.delete(db_connector)
    await db.commit()

    return None
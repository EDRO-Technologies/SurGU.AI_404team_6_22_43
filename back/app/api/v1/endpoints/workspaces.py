from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.core.database import get_db_session
from app.api.v1.dependencies import get_current_user, get_workspace_member, get_workspace_admin
from app import schemas, models

router = APIRouter()


#
# 1. CRUD для Workspaces
#

@router.post("/", response_model=schemas.WorkspacePublic, status_code=status.HTTP_201_CREATED)
async def create_workspace(
        workspace_in: schemas.WorkspaceCreate,
        db: AsyncSession = Depends(get_db_session),
        current_user: models.User = Depends(get_current_user)
):
    """
    Создание нового рабочего пространства (AI-ассистента).
    """
    # 1. Создать Workspace в БД, связав его с user.organization_id
    db_workspace = models.Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        organization_id=current_user.organization_id
    )
    db.add(db_workspace)
    await db.flush()  # Получаем ID воркспейса

    # 2. Добавить current_user в WorkspaceMembership с ролью "Admin"
    db_membership = models.WorkspaceMembership(
        user_id=current_user.id,
        workspace_id=db_workspace.id,
        role=models.UserRoleEnum.ADMIN
    )
    db.add(db_membership)

    await db.commit()
    await db.refresh(db_workspace)

    return db_workspace


@router.get("/", response_model=List[schemas.WorkspacePublic])
async def get_workspaces(
        db: AsyncSession = Depends(get_db_session),
        current_user: models.User = Depends(get_current_user)
):
    """
    Получение списка всех рабочих пространств, к которым у пользователя есть доступ.
    """
    # 1. Найти все WorkspaceMembership для этого user_id
    # 2. Загрузить связанные Workspace
    query = (
        select(models.Workspace)
        .join(models.WorkspaceMembership)
        .where(models.WorkspaceMembership.user_id == current_user.id)
    )
    result = await db.execute(query)
    workspaces = result.scalars().all()

    return workspaces


@router.get("/{workspace_id}", response_model=schemas.WorkspacePublic)
async def get_workspace(
        workspace_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что current_user имеет доступ к этому workspace_id
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
):
    """
    Получение детальной информации об одном рабочем пространстве.
    """
    # 2. Получить воркспейс (уже есть в membership.workspace, но лучше запросить)
    result = await db.execute(
        select(models.Workspace).where(models.Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    return workspace


@router.put("/{workspace_id}", response_model=schemas.WorkspacePublic)
async def update_workspace(
        workspace_id: UUID,
        workspace_in: schemas.WorkspaceUpdate,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что пользователь имеет роль Admin
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    Обновление информации о рабочем пространстве (только Admin).
    """
    result = await db.execute(
        select(models.Workspace).where(models.Workspace.id == workspace_id)
    )
    db_workspace = result.scalar_one_or_none()

    if not db_workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    # Обновляем поля, если они переданы
    update_data = workspace_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_workspace, key, value)

    db.add(db_workspace)
    await db.commit()
    await db.refresh(db_workspace)
    return db_workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
        workspace_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что пользователь имеет роль Admin
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    Удаление рабочего пространства (только Admin).
    """
    result = await db.execute(
        select(models.Workspace).where(models.Workspace.id == workspace_id)
    )
    db_workspace = result.scalar_one_or_none()

    if not db_workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    # (STUB) Здесь также должна быть логика очистки
    # - Удаление файлов из file_storage
    # - Удаление коллекции из ChromaDB
    print(f"TODO: Delete files and ChromaDB collection for workspace {workspace_id}")

    await db.delete(db_workspace)
    await db.commit()

    return None  # 204 No Content


#
# 2. Управление пользователями (членами) воркспейса
#

@router.get("/{workspace_id}/users", response_model=List[schemas.WorkspaceUser])
async def get_workspace_users(
        workspace_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что пользователь имеет доступ (любая роль)
        membership: models.WorkspaceMembership = Depends(get_workspace_member)
):
    """
    Получение списка пользователей, имеющих доступ к этому workspace.
    """
    query = (
        select(models.WorkspaceMembership)
        .options(selectinload(models.WorkspaceMembership.user))
        .where(models.WorkspaceMembership.workspace_id == workspace_id)
    )
    result = await db.execute(query)
    memberships = result.scalars().all()

    # Формируем ответ
    response = []
    for mem in memberships:
        if mem.user:  # Убедимся, что пользователь загружен
            response.append(schemas.WorkspaceUser(
                user_id=mem.user.id,
                full_name=mem.user.full_name,
                email=mem.user.email,
                role=mem.role
            ))
    return response


@router.post("/{workspace_id}/users", response_model=schemas.WorkspaceUser)
async def add_workspace_user(
        workspace_id: UUID,
        invite_in: schemas.WorkspaceUserInvite,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что текущий пользователь - Admin
        admin_membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    Приглашение/добавление нового пользователя в workspace (только Admin).
    """
    # 1. Найти пользователя по email в той же организации
    current_user_org_id = admin_membership.workspace.organization_id

    result = await db.execute(
        select(models.User)
        .where(
            models.User.email == invite_in.email,
            models.User.organization_id == current_user_org_id
        )
    )
    user_to_add = result.scalar_one_or_none()

    if not user_to_add:
        # В реальном приложении здесь могла бы быть логика "приглашения"
        # (отправка email), но по спеке мы добавляем существующих.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {invite_in.email} not found in this organization"
        )

    # 2. Проверить, не состоит ли он уже в воркспейсе
    result = await db.execute(
        select(models.WorkspaceMembership)
        .where(
            models.WorkspaceMembership.workspace_id == workspace_id,
            models.WorkspaceMembership.user_id == user_to_add.id
        )
    )
    existing_membership = result.scalar_one_or_none()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace"
        )

    # 3. Создать связь
    db_membership = models.WorkspaceMembership(
        user_id=user_to_add.id,
        workspace_id=workspace_id,
        role=invite_in.role
    )
    db.add(db_membership)
    await db.commit()

    return schemas.WorkspaceUser(
        user_id=user_to_add.id,
        full_name=user_to_add.full_name,
        email=user_to_add.email,
        role=db_membership.role
    )


@router.put("/{workspace_id}/users/{user_id}", response_model=schemas.WorkspaceUser)
async def update_workspace_user_role(
        workspace_id: UUID,
        user_id: UUID,
        role_in: schemas.WorkspaceUserUpdateRole,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что текущий пользователь - Admin
        admin_membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    Изменение роли пользователя в workspace (только Admin).
    """
    if user_id == admin_membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # 1. Найти членство пользователя, которого хотим изменить
    result = await db.execute(
        select(models.WorkspaceMembership)
        .options(selectinload(models.WorkspaceMembership.user))
        .where(
            models.WorkspaceMembership.workspace_id == workspace_id,
            models.WorkspaceMembership.user_id == user_id
        )
    )
    membership_to_update = result.scalar_one_or_none()

    if not membership_to_update or not membership_to_update.user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User membership not found in this workspace"
        )

    # 2. Обновить роль
    membership_to_update.role = role_in.role
    db.add(membership_to_update)
    await db.commit()

    return schemas.WorkspaceUser(
        user_id=membership_to_update.user.id,
        full_name=membership_to_update.user.full_name,
        email=membership_to_update.user.email,
        role=membership_to_update.role
    )


@router.delete("/{workspace_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_user(
        workspace_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        # 1. Проверяет, что текущий пользователь - Admin
        admin_membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    Удаление пользователя из workspace (только Admin).
    """
    if user_id == admin_membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the workspace"
        )

    # 1. Найти членство
    result = await db.execute(
        select(models.WorkspaceMembership)
        .where(
            models.WorkspaceMembership.workspace_id == workspace_id,
            models.WorkspaceMembership.user_id == user_id
        )
    )
    membership_to_delete = result.scalar_one_or_none()

    if not membership_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User membership not found in this workspace"
        )

    # 2. Удалить
    await db.delete(membership_to_delete)
    await db.commit()

    return None  # 204 No Content
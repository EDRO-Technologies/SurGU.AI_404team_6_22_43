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
    "/{workspace_id}/tools",
    response_model=schemas.ToolPublic,
    status_code=status.HTTP_201_CREATED
)
async def create_tool(
        workspace_id: UUID,
        tool_in: schemas.ToolCreate,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Создание определения "Инструмента" (Agent Tool).
    """
    print(f"Creating tool {tool_in.name} for workspace {workspace_id}")

    db_tool = models.Tool(
        workspace_id=workspace_id,
        name=tool_in.name,
        description=tool_in.description,
        api_endpoint=str(tool_in.api_endpoint),  # Pydantic v2 AnyHttpUrl -> str
        api_method=tool_in.api_method,
        parameters_schema=tool_in.parameters_schema.model_dump()
    )
    db.add(db_tool)
    await db.commit()
    await db.refresh(db_tool)

    # Возвращаем в формате ToolPublic, который наследует от ToolCreate
    return schemas.ToolPublic(id=db_tool.id, **tool_in.model_dump())


@router.get(
    "/{workspace_id}/tools",
    response_model=List[schemas.ToolPublic]
)
async def get_tools(
        workspace_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Получение списка всех инструментов в workspace.
    """
    query = select(models.Tool).where(models.Tool.workspace_id == workspace_id)
    result = await db.execute(query)
    tools = result.scalars().all()
    return tools


@router.delete(
    "/{workspace_id}/tools/{tool_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_tool(
        workspace_id: UUID,
        tool_id: UUID,
        db: AsyncSession = Depends(get_db_session),
        membership: models.WorkspaceMembership = Depends(get_workspace_admin)
):
    """
    (STUB) Удаление инструмента.
    """
    result = await db.execute(
        select(models.Tool).where(models.Tool.id == tool_id, models.Tool.workspace_id == workspace_id))
    db_tool = result.scalar_one_or_none()

    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    await db.delete(db_tool)
    await db.commit()

    return None
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_task_service
from app.core.exceptions import CategoryNotFoundError, TaskNotFoundError
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
async def get_tasks(
    service: TaskService = Depends(get_task_service),
    title_contains: str | None = Query(None, pattern=r"^[^\x00]*$"),
    completed: bool | None = Query(None),
    category_id: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0, le=2**63 - 1),
) -> list[TaskRead]:
    return await service.list_tasks(
        title_contains=title_contains,
        completed=completed,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    try:
        return await service.get(task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    try:
        return await service.create_task(payload)
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )


@router.patch("/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskRead:
    try:
        return await service.update_task(task_id, payload)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    except CategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> None:
    try:
        await service.delete_task(task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )

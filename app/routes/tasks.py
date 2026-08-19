from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import (
    TaskNotFoundError,
    create_task,
    delete_task,
    get_owned_task,
    list_tasks,
    update_task,
)


router = APIRouter(prefix="/tasks", tags=["Tarefas"])


@router.get("", response_model=list[TaskResponse])
async def get_tasks(
    session: DbSession, current_user: CurrentUser, completed: bool | None = None
) -> list[TaskResponse]:
    return await list_tasks(session, current_user, completed)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def post_task(
    data: TaskCreate, session: DbSession, current_user: CurrentUser
) -> TaskResponse:
    return await create_task(session, current_user, data)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int, session: DbSession, current_user: CurrentUser
) -> TaskResponse:
    try:
        return await get_owned_task(session, current_user, task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")


@router.patch("/{task_id}", response_model=TaskResponse)
async def patch_task(
    task_id: int,
    data: TaskUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> TaskResponse:
    try:
        return await update_task(session, current_user, task_id, data)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(
    task_id: int, session: DbSession, current_user: CurrentUser
) -> Response:
    try:
        await delete_task(session, current_user, task_id)
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
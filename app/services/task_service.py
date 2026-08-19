from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskNotFoundError(Exception):
    pass


async def list_tasks(
    session: AsyncSession, owner: User, completed: bool | None = None
) -> list[Task]:
    statement = select(Task).where(Task.owner_id == owner.id)
    if completed is not None:
        statement = statement.where(Task.is_completed == completed)
    result = await session.scalars(statement.order_by(Task.created_at.desc(), Task.id.desc()))
    return list(result.all())


async def get_owned_task(session: AsyncSession, owner: User, task_id: int) -> Task:
    result = await session.scalars(
        select(Task).where(Task.id == task_id, Task.owner_id == owner.id)
    )
    task = result.one_or_none()
    if task is None:
        raise TaskNotFoundError
    return task


async def create_task(
    session: AsyncSession, owner: User, data: TaskCreate
) -> Task:
    task = Task(
        owner_id=owner.id,
        title=data.title.strip(),
        description=data.description.strip() if data.description else None,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def update_task(
    session: AsyncSession, owner: User, task_id: int, data: TaskUpdate
) -> Task:
    task = await get_owned_task(session, owner, task_id)
    updates = data.model_dump(exclude_unset=True)
    if "title" in updates:
        updates["title"] = updates["title"].strip()
    if updates.get("description"):
        updates["description"] = updates["description"].strip()
    for field, value in updates.items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, owner: User, task_id: int) -> None:
    task = await get_owned_task(session, owner, task_id)
    await session.delete(task)
    await session.commit()
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.connection import async_session, engine
from app.main import app
from app.models.task import Task
from app.models.user import User


@pytest_asyncio.fixture(autouse=True)
async def clean_database() -> AsyncIterator[None]:
    async with async_session() as session:
        await session.execute(delete(Task))
        await session.execute(delete(User))
        await session.commit()
    await engine.dispose()
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
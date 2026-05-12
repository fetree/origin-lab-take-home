import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.database import Base
from app.api.deps import get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/sessions_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


SESSION_PAYLOAD = {
    "game_title": "CS:GO",
    "operator_name": "jake_m",
    "resolution": "2560x1440",
    "fps": 60,
    "has_depth": True,
    "streams": ["screen_video", "webcam_video", "audio", "input_log"],
    "system_metadata": {
        "hardware": {"cpu_model": "Intel Core i9-13900K", "gpu": "RTX 4080"},
        "encoder": "NVENC HEVC",
    },
}

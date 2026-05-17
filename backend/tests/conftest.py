import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db

# Use an in-memory SQLite database for tests (fast, no setup required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables before tests, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Provide a test DB session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient):
    # Sign up
    signup_resp = await client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "organization_name": "Test Org",
    })
    assert signup_resp.status_code == 201

    # Login to get token
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123",
    })
    token = login_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    return client

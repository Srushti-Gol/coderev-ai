import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.repository import Repository
from app.models.pull_request import PullRequest, PRStatus, AIStatus
from app.core.security import create_access_token

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Create all tables before tests and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_db dependency."""
    async def _get_db():
        yield db_session
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        github_id=12345,
        github_login="testuser",
        email="test@example.com",
        name="Test User",
        avatar_url="https://github.com/testuser.png",
        access_token="test_github_token",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_repo(db_session: AsyncSession, test_user: User) -> Repository:
    """Create a test repository."""
    repo = Repository(
        user_id=test_user.id,
        github_repo_id=67890,
        full_name="testuser/testrepo",
        name="testrepo",
        description="A test repository",
        language="Python",
        is_active=True,
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)
    return repo


@pytest.fixture
async def test_pr(db_session: AsyncSession, test_repo: Repository) -> PullRequest:
    """Create a test pull request."""
    pr = PullRequest(
        repo_id=test_repo.id,
        pr_number=1,
        title="Test PR",
        body="This is a test PR",
        author="testuser",
        base_branch="main",
        head_branch="feature/test",
        status=PRStatus.open,
        ai_status=AIStatus.pending,
        additions=50,
        deletions=10,
        changed_files=3,
    )
    db_session.add(pr)
    await db_session.commit()
    await db_session.refresh(pr)
    return pr


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get authentication headers for test user."""
    token = create_access_token(
        data={"sub": str(test_user.id), "github_login": test_user.github_login}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(override_get_db) -> TestClient:
    """Get a test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Get an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

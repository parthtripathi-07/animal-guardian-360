"""
Pytest configuration and async test fixtures.
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app, init_default_roles
from app.models.user import User, Role

# Use in-memory SQLite for rapid, isolated testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    future=True
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create fresh schema in in-memory DB for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Seed default roles
        for name, desc in [("user", "User role"), ("hospital", "Hospital role"), ("admin", "Admin role")]:
            session.add(Role(name=name, description=desc))
        await session.commit()
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async test HTTP client with dependency override for DB session."""
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def regular_user(test_db_session: AsyncSession) -> User:
    user = User(
        phone="+919876543210",
        email="user@test.org",
        full_name="Aarav Sharma",
        role_id=1,
        is_verified=True,
        is_active=True
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(regular_user: User) -> str:
    return create_access_token(subject=regular_user.id, role="user")


@pytest_asyncio.fixture
async def admin_user(test_db_session: AsyncSession) -> User:
    admin = User(
        phone="+919999999999",
        email="admin@test.org",
        full_name="Admin Officer",
        role_id=3,
        is_verified=True,
        is_active=True
    )
    test_db_session.add(admin)
    await test_db_session.commit()
    await test_db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    return create_access_token(subject=admin_user.id, role="admin")

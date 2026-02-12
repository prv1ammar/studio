from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings

# Use PostgreSQL URL from settings
# DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
DB_URL = getattr(settings, "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/studio")

engine = create_async_engine(
    DB_URL, 
    echo=False, 
    future=True,
    connect_args={"statement_cache_size": 0}
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        # Import models here to ensure they are registered
        from .models import User, Workflow, Credential, AuditLog, Workspace, WorkspaceMember, Comment
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

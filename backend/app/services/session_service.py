import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionStatus
from app.schemas.session import SessionCreate


async def create_session(db: AsyncSession, data: SessionCreate) -> Session:
    raise NotImplementedError


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Session | None:
    raise NotImplementedError


async def list_sessions(
    db: AsyncSession,
    status: SessionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Session]:
    raise NotImplementedError


async def update_status(db: AsyncSession, session_id: uuid.UUID, status: SessionStatus) -> Session:
    raise NotImplementedError


async def get_stats(db: AsyncSession) -> dict:
    raise NotImplementedError

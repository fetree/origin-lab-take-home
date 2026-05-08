import enum
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SessionStatus(str, enum.Enum):
    created = "created"
    uploading = "uploading"
    processing = "processing"
    review = "review"
    approved = "approved"
    rejected = "rejected"
    failed = "failed"
    paused = "paused"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_title: Mapped[str] = mapped_column(String(255), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    resolution: Mapped[str | None] = mapped_column(String(50))
    fps: Mapped[int | None] = mapped_column(Integer)
    has_depth: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"), default=SessionStatus.created, nullable=False
    )
    streams: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    system_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

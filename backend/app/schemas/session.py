import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.session import SessionStatus


class SessionCreate(BaseModel):
    game_title: str
    operator_name: str
    resolution: str | None = None
    fps: int | None = None
    has_depth: bool = False
    streams: list[str] = Field(default_factory=list)
    system_metadata: dict | None = None


class SessionStatusUpdate(BaseModel):
    status: SessionStatus


class StreamHealthOut(BaseModel):
    stream: str
    last_seen_at: datetime | None
    event_count: int
    error_count: int
    bytes_received: int

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: uuid.UUID
    game_title: str
    operator_name: str
    resolution: str | None
    fps: int | None
    has_depth: bool
    status: SessionStatus
    streams: list[str] | None
    system_metadata: dict | None
    created_at: datetime
    updated_at: datetime
    stream_health: list[StreamHealthOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SessionListOut(BaseModel):
    id: uuid.UUID
    game_title: str
    operator_name: str
    resolution: str | None
    fps: int | None
    status: SessionStatus
    streams: list[str] | None
    stream_health: list[StreamHealthOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    total_sessions: int
    by_status: dict[str, int]
    events_per_second: float
    error_rate: float

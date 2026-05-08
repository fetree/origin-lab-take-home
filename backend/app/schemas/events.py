import uuid
from datetime import datetime

from pydantic import BaseModel


class StreamEventOut(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    stream: str
    seq: int | None
    payload: dict
    received_at: datetime

    model_config = {"from_attributes": True}

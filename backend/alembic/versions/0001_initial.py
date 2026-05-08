"""initial

Revision ID: 0001
Revises:
Create Date: 2026-05-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("game_title", sa.String(255), nullable=False),
        sa.Column("operator_name", sa.String(255), nullable=False),
        sa.Column("resolution", sa.String(50)),
        sa.Column("fps", sa.Integer()),
        sa.Column("has_depth", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.Enum("created","uploading","processing","review","approved","rejected","failed","paused", name="session_status"), nullable=False, server_default="created"),
        sa.Column("streams", postgresql.ARRAY(sa.Text())),
        sa.Column("system_metadata", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "stream_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stream", sa.String(100), nullable=False),
        sa.Column("seq", sa.BigInteger()),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "stream", "seq", name="uq_stream_event_seq"),
    )
    op.create_index("ix_stream_events_session_stream_received", "stream_events", ["session_id", "stream", "received_at"])

    op.create_table(
        "stream_health",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("stream", sa.String(100), primary_key=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("event_count", sa.BigInteger(), server_default="0"),
        sa.Column("error_count", sa.Integer(), server_default="0"),
        sa.Column("bytes_received", sa.BigInteger(), server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("stream_health")
    op.drop_index("ix_stream_events_session_stream_received", "stream_events")
    op.drop_table("stream_events")
    op.drop_table("sessions")
    op.execute("DROP TYPE session_status")

import uuid

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint, Uuid, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from utils.datetime_utc import datetime, datetime_utc_now

from .base import Base
from .enums import ChatMessageStatus, ChatRoleType


class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_uid: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.uid", ondelete="CASCADE"), index=True
    )
    message_uid: Mapped[uuid.UUID] = mapped_column(
        Uuid, index=True
    )  # message id sent by client for each user's message
    role: Mapped[ChatRoleType] = mapped_column(
        Enum(ChatRoleType), default=ChatRoleType.USER
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    translation_id: Mapped[int | None] = mapped_column(
        ForeignKey("translations.id"), index=True
    )  # translations id for referencing translations phrase rows

    content: Mapped[str] = mapped_column(String(6000))
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR)

    status: Mapped[ChatMessageStatus | None] = mapped_column(
        Enum(ChatMessageStatus)
    )  # will be handle by hooks, if role is user then (PENDING|Failed|SUCESS) else for AI (Success|Failed)
    created_at: Mapped[datetime] = mapped_column(default=datetime_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime_utc_now, onupdate=datetime_utc_now
    )

    # Table-level unique constraint
    __table_args__ = (
        UniqueConstraint("chat_uid", "message_uid", name="unique_chat_message"),
    )


# Hook running BEFORE an INSERT operation
@event.listens_for(Messages, "before_insert")
def generate_sku_before_insert(mapper, connection, target: Messages):
    """Sets the status base on chat_role_type for user's inital pending then"""
    if target.role == ChatRoleType.USER:
        # Generate your value based on the other column
        target.status = ChatMessageStatus.PENDING
    else:
        target.status = ChatMessageStatus.SUCCESS
        target.message_uid = uuid.uuid4()


# Hook running BEFORE an UPDATE operation
@event.listens_for(Messages, "before_update")
def update_sku_before_update(mapper, connection, target: Messages):
    # Optional: Check if the column actually changed before modifying it
    state = event.orm.attributes.instance_state(target)
    status = state.get_history("status", passive=True)

    if status.has_changes():
        pass

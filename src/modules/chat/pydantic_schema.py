import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class UserChatsResponseSchema(BaseModel):
    uid: uuid.UUID
    title: str
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageSchema(BaseModel):
    translation_id: int | None = None
    message_uid: uuid.UUID
    content: str


class ChatMessageResponseSchema(BaseModel):
    id: int
    message_uid: uuid.UUID
    chat_uid: uuid.UUID
    role: Literal["user", "assistant"]
    status: Literal[
        "loading",
        "cached",
        "success",
        "error",
    ]
    user_id: int | None
    content: str
    translation_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatStreamingResponseSchema(BaseModel):
    message_uid: uuid.UUID
    content: str | None = None
    status: Literal[
        "loading",
        "cached",
        "success",
        "error",
    ]

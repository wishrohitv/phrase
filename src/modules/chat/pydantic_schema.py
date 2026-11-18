import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserChatsResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    uid: uuid.UUID
    title: str
    updated_at: datetime
    created_at: datetime


class ChatMessageSchema(BaseModel):
    translation_id: int | None = None
    message_uid: uuid.UUID
    content: str


class ChatMessageResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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


class ChatStreamingResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message_uid: uuid.UUID
    content: str | None = None
    status: Literal[
        "loading",
        "cached",
        "success",
        "error",
    ]

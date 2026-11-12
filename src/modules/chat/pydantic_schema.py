import uuid
from typing import Literal

from pydantic import BaseModel


class ChatMessageSchema(BaseModel):
    translation_id: int | None = None
    message_uid: uuid.UUID
    content: str


class NewChatSchema(BaseModel):
    title: str


class ChatResponseSchema(BaseModel):
    message_uid: uuid.UUID
    content: str | None = None
    status: Literal[
        "loading",
        "cached",
        "success",
        "error",
    ]

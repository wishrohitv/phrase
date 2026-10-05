import uuid

from pydantic import BaseModel


class ChatMessageSchema(BaseModel):
    translation_id: int | None = None
    message_uid: uuid.UUID
    content: str


class NewChatSchema(BaseModel):
    title: str

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Chats
from services.embeddings import get_embedding


def store_chat_embeddings(
    chat_id: int,
    message: str,
) -> None:
    db: Session = SessionLocal()
    try:
        embedding = get_embedding(text=message)
        chat = Chats(chat_id=chat_id, message=message, embedding=embedding)
        db.add(chat)
        db.commit()
    finally:
        db.close()

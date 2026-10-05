from sqlalchemy import update
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Messages
from services.embeddings import get_embedding


def store_chat_embeddings(
    chat_id: int,
    message: str,
) -> None:
    db: Session = SessionLocal()
    try:
        embedding = get_embedding(text=message)
        query = update(Messages).filter_by(id=chat_id).values(embedding=embedding)
        db.execute(query)
        db.commit()
    finally:
        db.close()

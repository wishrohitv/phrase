from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from settings import settings

engine = create_engine(
    settings.DATABASE_URL,  # echo=True
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Automatically create the extension if it doesn't exist
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

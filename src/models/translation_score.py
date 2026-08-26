from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TranslationScore(Base):
    __tablename__ = "translation_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    translation_id: Mapped[int] = mapped_column(ForeignKey("translations.id"))
    score: Mapped[float | None] = mapped_column(Float)  # Between 0 to 10
    like: Mapped[int | None] = mapped_column(Integer)  # 0 or 1

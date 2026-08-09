from .base import Base

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): ...


# class User(Base): ...


class Item(Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(UUID, nullable=True)
    prod_id: Mapped[str] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=True)
    link: Mapped[str] = mapped_column(String, nullable=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )
    # User-prod_id unique constraint

    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, user_id={self.user_id!r}, prod_id={self.prod_id!r}, name={self.name!r}, category={self.category!r}, price={self.price!r}, link={self.link!r}, time={self.time!r})"

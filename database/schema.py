from datetime import datetime

from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy import Integer
from sqlalchemy import DateTime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        "id", Integer(), primary_key=True, autoincrement=True
    )
    chat_id: Mapped[int] = mapped_column("chat_id", Integer())
    username: Mapped[str] = mapped_column("username", String())
    firstname: Mapped[str] = mapped_column("firstname", String())
    lastname: Mapped[str] = mapped_column("lastname", String())
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), insert_default=datetime.now()
    )

    def __repr__(self) -> str:
        return f"User(uuid={self.id!r}, chat_id={self.chat_id!r}, username={self.username!r}), firstname={self.firstname!r}, created_at={self.created_at!r}"


class Mastertable(Base):
    __tablename__ = "mastertable"

    id: Mapped[int] = mapped_column(
        "id", Integer(), nullable=False, autoincrement=True, primary_key=True
    )
    dates: Mapped[datetime] = mapped_column("date", DateTime(timezone=True))
    seat: Mapped[int] = mapped_column("seat", String(6))
    user_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE")
    )
    # is_free: Mapped[bool] = mapped_column('is_free', Boolean(), default=True)

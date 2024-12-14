from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import Integer, String, BigInteger

from sqlalchemy import Date, DateTime

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
    chat_id: Mapped[int] = mapped_column("chat_id", BigInteger())
    username: Mapped[str] = mapped_column("username", String())
    firstname: Mapped[str] = mapped_column("firstname", String(), nullable=True)
    lastname: Mapped[str] = mapped_column("lastname", String(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), insert_default=datetime.now()
    )


class Mastertable(Base):
    __tablename__ = "mastertable"

    id: Mapped[int] = mapped_column(
        "id", Integer(), nullable=False, autoincrement=True, primary_key=True
    )
    seats: Mapped[int] = mapped_column("seats", String(6))
    period_day: Mapped[datetime.date] = mapped_column("period_day", Date())
    is_weekend: Mapped[int] = mapped_column("is_weekend", Integer())
    week_day: Mapped[int] = mapped_column('week_day', Integer())
    user_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    #is_taken: Mapped[bool] = mapped_column('is_taken', Boolean(), default=False)


class SecureTable(Base):
    __tablename__ = "secure"
    id: Mapped[int] = mapped_column(
        "id", Integer(), nullable=False, autoincrement=True, primary_key=True
    )
    password: Mapped[str] = mapped_column("password", String(), nullable=True)

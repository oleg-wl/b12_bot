import uuid
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
        "id", String(36), default=lambda: str(uuid.uuid4()), primary_key=True
    )
    chat_id: Mapped[int] = mapped_column("chat_id", Integer())
    username: Mapped[str] = mapped_column("username", String())
    firstname: Mapped[str] = mapped_column("firstname", String())
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), insert_default=datetime.now()
    )

    def __repr__(self) -> str:
        return f"User(uuid={self.id!r}, chat_id={self.chat_id!r}, username={self.username!r}), firstname={self.firstname!r}, created_at={self.created_at!r}"
    
class Seats(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column('id', Integer(), primary_key=True, autoincrement=True, nullable=False, unique=True)
    seatno: Mapped[str] = mapped_column('seat_no', String(6), nullable=False)

class Timetable(Base):
    __tablename__ = 'timetable'

    id: Mapped[int] = mapped_column('id', Integer(), nullable=False, autoincrement=True)
    date: Mapped[datetime] = mapped_column('date', DateTime(timezone=True))
    user_id: Mapped[int] = mapped_column('user_id', ForeignKey('users.id'))
    seat_id: Mapped[int] = mapped_column('seat_id', ForeignKey('seats.id'))
    is_free: Mapped[bool] = mapped_column('is_free', Boolean(), default=True)

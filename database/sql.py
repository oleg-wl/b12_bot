import locale

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

import datetime
from typing import Sequence, Tuple
from loguru import logger

from sqlalchemy import Engine, Row, Select, select, update, create_engine, text
from sqlalchemy.orm import Session

from .schema import Users, Mastertable, SecureTable
from .masterdata import MasterTable as mt


FORMAT = "%d-%m-%Y %A"

logger.catch()
def check_connection(engine: Engine):
    stmt = select(text("'ok'"))
    with Session(engine) as session:
        r = session.execute(stmt)
    logger.success('Connection {}', r.first()[0])


def select_days(engine: Engine, d: int):

    today = datetime.date.today()

    with Session(engine) as session:
        stmt = (
            select(Mastertable.period_day)
            .order_by(Mastertable.period_day)
            .where(Mastertable.period_day >= today)
            .where(
                Mastertable.is_weekend == 0,
            )
            .distinct()
            .limit(d)
        )
        dates = session.scalars(stmt).all()
        logger.debug(dates)

    return [day.strftime(FORMAT) for day in dates]


def select_free_seats(engine: Engine, date: datetime) -> Sequence[int]:
    logger.debug("свободные места для даты {}".format(date))
    # d = datetime.datetime.strptime(date, FORMAT)

    with Session(engine) as session:
        stmt = (
            select(Mastertable.seats)
            .order_by(Mastertable.seats)
            .where(Mastertable.period_day == date)
            .where(Mastertable.user_id == None)
        )
        seats: Sequence[int] = session.scalars(stmt).all()
    for s in seats:
        logger.debug(s)
    return seats


def select_my_seats_to_unbook(engine: Engine, chat_id) -> Sequence[Row[Tuple[datetime.datetime | int]]]:
    today = datetime.date.today()

    with Session(engine) as session:

        userid_subquery = (
            select(Users.id).where(Users.chat_id == chat_id).scalar_subquery()
        )

        stmt: Select[Tuple[datetime.datetime, int]] = (
            select(Mastertable.period_day, Mastertable.seats)
            .order_by(Mastertable.period_day)
            .where(Mastertable.is_weekend == 0)
            .where(Mastertable.user_id == userid_subquery)
            .where(Mastertable.period_day >= today)
            .distinct()
            .limit(5)
        )
        dates: Sequence[Row[Tuple[datetime.datetime, int]]] = session.execute(stmt).all()

        logger.debug('dates to unbook', dates)
    return dates


def book_seat(engine: Engine, chat_id, selected_seat, selected_date) -> int:

    with Session(engine) as session:
        user_id_stmt = select(Users.id).where(Users.chat_id == chat_id)
        user_id = session.scalars(user_id_stmt).first()
        logger.debug(
            f"user_id - {user_id}, selected_date {selected_date}, selected_seat {selected_seat}"
        )

        # проверка - 0
        # место не было занято при одновременном букировании, пока сообщение с предложением занять место висит открытым у более чем одного человека
        check_stmt: Select[Tuple[int]] = (
            select(Mastertable.user_id)
            .where(Mastertable.period_day == selected_date)
            .where(Mastertable.seats == selected_seat)
        )

        check = session.scalars(check_stmt).first()

        # проверка - 1
        # ограничение 1 место на 1 день - сообщить что предыдущее место забронировано
        check_one_seat_per_day_stmt: Select[Tuple[int]] = (
            select(Mastertable.seats)
            .where(Mastertable.period_day == selected_date)
            .where(Mastertable.user_id == user_id)
        )

        prev_seat: int | None = session.scalars(check_one_seat_per_day_stmt).first()

        if check is not None:

            return 0

        elif prev_seat is not None:

            del_prev_seat_stmt = (
                update(Mastertable)
                .where(Mastertable.period_day == selected_date)
                .where(Mastertable.seats == prev_seat)
                .values(user_id=None)
            )
            session.execute(del_prev_seat_stmt)

            upd_stmt = (
                update(Mastertable)
                .where(Mastertable.period_day == selected_date)
                .where(Mastertable.seats == selected_seat)
                .values(user_id=user_id)
            )
            session.execute(upd_stmt)
            session.commit()

            return prev_seat

        else:

            upd_stmt = (
                update(Mastertable)
                .where(Mastertable.period_day == selected_date)
                .where(Mastertable.seats == selected_seat)
                .values(user_id=user_id)
            )
            session.execute(upd_stmt)

            session.commit()
            return 1


def unbook_seat(engine: Engine, selected_unbook_seat, selected_unbook_date):

    logger.debug("{} - {}".format(selected_unbook_date, selected_unbook_seat))
    with Session(engine) as session:
        unbook_stmt = (
            update(Mastertable)
            .where(Mastertable.period_day == selected_unbook_date)
            .where(Mastertable.seats == selected_unbook_seat)
            .values(user_id=None)
        )
        session.execute(unbook_stmt)

        session.commit()


def check_user_chat_id(engine: Engine, chat_id) -> Row[Tuple[Users]] | None:

    with Session(engine) as session:
        stmt = select(Users).filter_by(chat_id=chat_id)
        row = session.execute(stmt).first()

    return row


def check_user_username(engine: Engine, username):

    with Session(engine) as session:
        stmt = select(Users).filter_by(username=username)
        row = session.execute(stmt).first()

    return row


def insert_user(engine: Engine, **kwargs):

    with Session(engine) as session:

        user = Users(
            chat_id=kwargs.get("chat_id"),
            username=kwargs.get("username"),
            firstname=kwargs.get("firstname"),
            lastname=kwargs.get("lastname"),
            created_at=kwargs.get("created_at"),
        )
        session.add(user)
        session.commit()
    logger.debug(
        f"user - {kwargs.get('username')} | chat_id - {kwargs.get('chat_id')} added"
    )


def check_password(engine: Engine, password) -> bool:
    password = mt.make_password(passwd=password)
    logger.debug(password)

    with Session(engine) as session:
        stmt = select(SecureTable.password).where(SecureTable.password == password)
        access = session.execute(stmt).first()

        match access:
            case None:
                logger.debug("access denied")
                return False

            case _:
                logger.debug("access granted")
                return True

    logger.debug(access)

def show_who_booked(engine: Engine, date: datetime) -> str:

    with Session(engine) as session:
        stmt = (select(Users.username, Mastertable.seats)
                        .where(Mastertable.period_day == date)
                        .where(Users.id == Mastertable.user_id)
                        .where(Users.id != -1)
                        .order_by(Mastertable.seats)
        )
        usernames: Sequence[Row[Tuple[str | int]]] = session.execute(stmt).fetchall()
    
    s = ''
    for i in usernames:
        s += '{} - @{}\n'.format(i[1], i[0])
    
    return s

def show_chat_ids(engine: Engine):

    stmt = select(Users.chat_id).filter(Users.chat_id.notin_((-1, 123)))
    with Session(engine) as session:
        chat_ids = session.scalars(stmt).all()
    return chat_ids


if __name__ == "__main__":
    eng = create_engine("sqlite:///b12.db")
    days = select_days(engine=eng)
    seats = select_free_seats(engine=eng, date=days[0])
    my_seats_dates = select_my_seats_to_unbook(engine=eng, chat_id=123)

    print(days)
    print(seats)
    print(my_seats_dates)
    print(type(my_seats_dates[0]))

    # _check_password(engine=eng, password=2024)
    # _check_password(engine=eng, password=2025)

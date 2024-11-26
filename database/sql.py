import locale
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

import datetime
from datetime import timedelta
from typing import Sequence
from loguru import logger

from sqlalchemy import select, update, insert, create_engine
from sqlalchemy.orm import Session

from .schema import Users, Mastertable, SecureTable 
from .masterdata import MasterTable as mt


FORMAT = "%d-%m-%Y %A"


def select_days(engine):

    today = datetime.date.today()
    five_days = today + timedelta(days=5)

    with Session(engine) as session:
        stmt = (
            select(Mastertable.period_day)
            .order_by(Mastertable.id, Mastertable.period_day)
            .filter(
                Mastertable.period_day.between(today, five_days),
                Mastertable.is_weekend == 0,
            )
            .distinct()
        )
        dates = session.scalars(stmt).all()
        logger.debug(dates)

    return [day.strftime(FORMAT) for day in dates]

def select_free_seats(engine, date:datetime):
    logger.debug("свободные места для даты {}".format(date))
    # d = datetime.datetime.strptime(date, FORMAT)

    with Session(engine) as session:
        stmt = (
            select(Mastertable.seats)
            .order_by(Mastertable.seats)
            .filter(
                Mastertable.period_day == date, 
                Mastertable.user_id == None,
                ~Mastertable.is_taken == True
            )
        )
        seats: Sequence[int] = session.scalars(stmt).all()
    for s in seats:
        logger.debug(s)
    return seats


def select_my_seats_d(engine, chat_id):
    today = datetime.date.today()
    five_days = today + timedelta(days=5)

    with Session(engine) as session:

        userid_subquery = select(Users.id).where(Users.chat_id == chat_id).subquery()

        stmt = (
            select(Mastertable.period_day, Mastertable.seats)
            .order_by(Mastertable.id, Mastertable.period_day)
            .filter(
                Mastertable.period_day.between(today, five_days),
                Mastertable.is_weekend == 0,
                Mastertable.user_id == select(userid_subquery)
            )
            .distinct()
        )
        dates = session.execute(stmt).all()

        logger.debug(dates)
    return dates


def book_seat(engine, chat_id, selected_seat, selected_date):

    with Session(engine) as session:
        user_id_stmt = select(Users.id).where(Users.chat_id == chat_id)
        user_id = session.scalars(user_id_stmt).first()
        logger.debug(f'user_id - {user_id}, selected_date {selected_date}, selected_seat {selected_seat}')

        # проверка что место не занято при одновременном букировании, пока сообщение с предложением занять место висит открытым у более чем одного человека
        check_stmt = select(Mastertable.user_id).where(Mastertable.period_day == selected_date).where(Mastertable.seats == selected_seat)

        check = session.scalars(check_stmt).first()

        # проверка-ограничение 1 место на 1 день
        check_one_seat_per_day_stmt = select(Mastertable.user_id).where(Mastertable.period_day == selected_date).where(Mastertable.user_id == user_id)

        check2 = session.scalars(check_one_seat_per_day_stmt).first()

        if (check is not None) | (check2 is not None):
            return False
        
        else:

            upd_stmt = update(Mastertable).where(Mastertable.period_day == selected_date).where(Mastertable.seats == selected_seat).values(user_id=user_id, is_taken=1)
            session.execute(upd_stmt)
            

        session.commit()


def unbook_seat(engine, selected_unbook_seat, selected_unbook_date):

    logger.debug('{} - {}'.format(selected_unbook_date, selected_unbook_seat))
    with Session(engine) as session:
        unbook_stmt = update(Mastertable).where(Mastertable.period_day == selected_unbook_date).where(Mastertable.seats == selected_unbook_seat).values(is_taken=0, user_id=None)
        session.execute(unbook_stmt)
        
        session.commit()

def check_user(engine, chat_id):

    with Session(engine) as session:
        stmt = select(Users).filter_by(chat_id=chat_id)
        row = session.execute(stmt).first()

    return row

def insert_user(engine, **kwargs):
    
    with Session(engine) as session:
        
        user = Users(
                chat_id=kwargs.get('chat_id'),
                username=kwargs.get('username'),
                firstname=kwargs.get('firstname'),
                lastname=kwargs.get('lastname'),
                created_at=kwargs.get('created_at'),
            )
        session.add(user)
        session.commit()
    logger.debug(f'user - {kwargs.get('username')} | chat_id - {kwargs.get('chat_id')} added')

def check_password(engine, password):
    password = mt.make_password(passwd=password)
    logger.debug(password)

    with Session(engine) as session:
        stmt = select(SecureTable.password).where(SecureTable.password == password)
        access = session.execute(stmt).first()

        match access:
            case None:
                logger.debug("acces denied")
                return False

            case _:
                logger.debug("access granted")
                return True

    logger.debug(access)


if __name__ == "__main__":
    eng = create_engine("sqlite:///b12.db")
    days = select_days(engine=eng)
    seats = select_free_seats(engine=eng, date=days[0])
    my_seats_dates = select_my_seats_d(engine=eng)

    print(days)
    print(seats)
    print(my_seats_dates)

    # _check_password(engine=eng, password=2024)
    # _check_password(engine=eng, password=2025)

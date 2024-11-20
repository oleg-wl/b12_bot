import datetime
from datetime import timedelta
from loguru import logger

from sqlalchemy import select, update, insert, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from masterdata import MasterTable as mt
from schema import Users, Mastertable, SecureTable, BadUsers

FORMAT = "%d-%m-%Y"


def _select_days(engine):

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

    for day in dates:
        logger.debug(day.strftime(FORMAT))
    return dates


def _select_free_seats(engine, date):
    logger.debug("свободные места для даты {}".format(date))
    # d = datetime.datetime.strptime(date, FORMAT)

    with Session(engine) as session:
        stmt = (
            select(Mastertable.seats)
            .order_by(Mastertable.seats)
            .filter(
                Mastertable.period_day == date, 
                Mastertable.user_id == None
            )
        )
        seats = session.scalars(stmt).all()
    for s in seats:
        logger.debug(s)
    return seats


def _select_my_seats():
    pass


def _book_seat():
    pass


def _unbook_seat():
    pass


def _check_user(engine, chat_id):

    with Session(engine) as session:
        stmt = select(Users).filter_by(chat_id=chat_id)
        row = session.execute(stmt).first()

    return row

def _insert_user(engine, **kwargs):
    
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

def _check_password(engine, password):
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

def _bad_user(engine, **kwargs):
    # добавить в таблу юзеров которые перебирают пароль

    with Session(engine) as session:
        try:
            stmt = insert(BadUsers).values(
                chat_id = kwargs.get('chat_id'),
                username = kwargs.get('username')
            ).returning(BadUsers.attempt)
            attempt = session.scalars(stmt).first()
            session.commit()
            logger.debug('Bad User {} added'.format(kwargs.get['username']))
            return attempt
        
        except IntegrityError:
            stmt = select(BadUsers.attempt).where(BadUsers.chat_id == kwargs.get('chat_id'))
            attempt = session.scalars(stmt).first() + 1
            stmt = update(BadUsers).where(BadUsers.chat_id == kwargs.get('chat_id')).values(attempt=attempt)
            logger.debug('Attempt {}'.format(attempt))
            
            return attempt



if __name__ == "__main__":
    eng = create_engine("sqlite:///b12.db")
    days = _select_days(engine=eng)
    seats = _select_free_seats(engine=eng, date=days[0])

    print(days)
    print(seats)

    # _check_password(engine=eng, password=2024)
    # _check_password(engine=eng, password=2025)

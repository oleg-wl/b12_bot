import datetime
from datetime import timedelta
import hashlib
from loguru import logger

from sqlalchemy import select, func, create_engine, text, desc
from sqlalchemy.orm import Session

from masterdata import MasterTable as mt
from schema import Users, Mastertable, SecureTable

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
        logger.debug(day.strftime("%d-%m-%Y"))

def _select_free_seats():
    pass


def _select_my_seats():
    pass


def _book_seat():
    pass


def _unbook_seat():
    pass

def _check_password(engine, password):
    password = mt.make_password(passwd=password)
    logger.debug(password)
    
    with Session(engine) as session:
        stmt = select(SecureTable.password).where(SecureTable.password == password)
        access = session.execute(stmt).first()

        match access:
            case None:
                logger.debug('acces denied')
                return False
            
            case _:
                logger.debug('access granted')
                return True

    logger.debug(access)

if __name__ == "__main__":
    eng = create_engine("sqlite:///b12.db")
    #_select_days(engine=eng)
    _check_password(engine=eng, password=2024)
    _check_password(engine=eng, password=2025)

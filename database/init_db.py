from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session

from schema import Base, Users, SecureTable
from masterdata import MasterTable

import os
from dotenv import load_dotenv

from loguru import logger

load_dotenv("config.env")


class DBA_tools:

    def __init__(self):

        db_user = os.getenv("db_user")
        dbpass = os.getenv("db_pass")

        dbhost = os.getenv("db_host")
        dbport = os.getenv("db_port")
        dbname = os.getenv("db_name", "database")

        self.engine = create_engine(
            "sqlite:///{d}.db".format(d = dbname), echo=True
        )

        self.mt = MasterTable()

    @logger.catch
    def create_db(self):
        Base.metadata.create_all(self.engine)

    def insert_masterdata(self):
        
        self.mt.make_table(start_y=2024, end_y=2026)

        self.mt.master_table.to_sql(
            "mastertable", self.engine.connect(), if_exists="append", index=False
        )

    def change_passwd(self, passwd):
        with Session(bind=self.engine) as s:
            pwd = self.mt.make_password(passwd=passwd)
            result = s.query(SecureTable).all()
            print(pwd)
        
            if len(result) == 0:
                s.add(SecureTable(password=pwd))
                logger.debug(f'password added. hash {pwd}')
                s.commit()
            else: 
                for p in result:
                    s.delete(p)
                s.commit()
                s.add(SecureTable(password=pwd))
                logger.debug(f'password added. hash {pwd}')
                s.commit()

    def _check_user(self, **kwargs):

        username = kwargs.get("username", None)
        chat_id = kwargs.get("chat_id")
        created_at = kwargs.get("created_at")
        firstname = kwargs.get("firstname")

        with Session() as s:
            stmt = select(Users).filter_by(chat_id=chat_id)
            row = s.execute(stmt).first()

            # TODO: добавить проверку пароля
            if row is None:

                

                user = Users(
                    chat_id=chat_id,
                    username=username,
                    firstname=firstname,
                    created_at=created_at,
                )
                s.add(user)
                s.commit()


if __name__ == "__main__":
    db = DBA_tools()
    #db.create_db()
    logger.debug("database created")
    #db.insert_masterdata()
    logger.debug("masterdata inserted")
    db.change_passwd(2025)

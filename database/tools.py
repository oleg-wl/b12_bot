from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from schema import Base, Users, Mastertable

class DB_Admin:

    engine = create_engine("sqlite:///database.db", echo=True)

    def create_db(self):
        Base.metadata.create_all(self.engine)

    def insert_users(self):
        usernames = [
            'sunnytwelve88',
            'Bina_1987',
            'lordcrabov'
        ]
        with Session(self.engine) as session:
            session.add_all([Users(username=u) for u in usernames])
            session.commit()

if __name__ == '__main__':
    DB_Admin().insert_users()
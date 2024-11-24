import database

database.conf.create_db()
database.conf.change_passwd('2025')
database.conf.insert_masterdata()

days = database.select_days(engine=database.engine)

print(days)
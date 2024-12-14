import database
from loguru import logger

database.check_connection(database.engine)

database.conf.create_db()
logger.success('database created')
database.conf.change_passwd('2025')
logger.success('password set')
database.conf.insert_masterdata()
logger.success('masterdata inserted')
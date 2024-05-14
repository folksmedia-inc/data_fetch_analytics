import pymysql.cursors
from starlette.config import Config

config = Config(".env")

db_host = config("DB_HOST", cast=str)
db_user = config("DB_USER", cast=str)
db_password = config("DB_PASSWORD", cast=str)
db_database = config("DB_DATABASE", cast=str)

def tracker():
    connection = pymysql.connect(host=db_host,
                                 user=db_user,
                                 password=db_password,
                                 database=db_database,
                                 cursorclass=pymysql.cursors.DictCursor)
    cur = connection.cursor(pymysql.cursors.DictCursor)

    return connection, cur
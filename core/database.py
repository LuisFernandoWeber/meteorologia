from pony.orm import Database
from core.config import (
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME
)


db = Database()

db.bind(
    provider="mysql",
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    passwd=DB_PASSWORD,
    db=DB_NAME
)

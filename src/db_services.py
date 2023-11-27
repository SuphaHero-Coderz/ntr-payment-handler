import src.database as _database

from src.models import Payment
from src.database import engine
from sqlmodel import Session


"""
DATABASE ZONE
"""


def create_database() -> None:
    """
    Initializes the database engine
    """
    _database.init_db()


"""
PAYMENT ZONE
"""


def create_payment(payment: Payment):
    with Session(engine) as session:
        session.add(payment)
        session.commit()

import src.database as _database

from src.models import Payment
from src.database import engine
from sqlmodel import Session, select


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


def create_payment(payment: Payment) -> None:
    """
    Creates a payment in database

    Args:
        payment (Payment): the payment object
    """
    with Session(engine) as session:
        session.add(payment)
        session.commit()


def get_payment(order_id: int, user_id: int) -> Payment:
    """
    Gets a payment from order id and user id

    Args:
        order_id (int): order id
        user_id (int): user id

    Returns:
        Payment: result
    """
    with Session(engine) as session:
        query = select(Payment).where(
            Payment.order_id == order_id, Payment.user_id == user_id
        )
        result = session.exec(query).one()

        return result

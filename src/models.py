from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime


class Payment(SQLModel, table=True):
    __tablename__: str = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    order_id: int
    payment_amount: float
    timestamp: Optional[datetime] = Field(default=datetime.utcnow())

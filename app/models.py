from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Float

from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    model_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


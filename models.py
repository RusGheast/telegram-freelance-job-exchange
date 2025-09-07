from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True)
    username = Column(String)
    balance = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    payment_details = Column(Text, nullable=True)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    taken = Column(Boolean, default=False)
    taken_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed = Column(Boolean, default=False)

class WithdrawalRequest(Base):
    __tablename__ = "withdrawals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    processed = Column(Boolean, default=False)
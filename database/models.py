from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    address = Column(Text)
    date_of_birth = Column(DateTime)
    medical_history = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    doctor_id = Column(Integer)
    doctor_name = Column(String(100))
    appointment_type = Column(String(50))
    scheduled_time = Column(DateTime)
    status = Column(String(20), default="scheduled")
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())

class MedicineOrder(Base):
    __tablename__ = "medicine_orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pharmacy_id = Column(Integer)
    pharmacy_name = Column(String(100))
    medicines = Column(JSON)
    total_amount = Column(Integer)
    status = Column(String(20), default="pending")
    delivery_address = Column(Text)
    created_at = Column(DateTime, default=func.now())

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    response = Column(Text)
    intent = Column(String(50))
    timestamp = Column(DateTime, default=func.now())
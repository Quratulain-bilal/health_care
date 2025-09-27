from sqlalchemy.orm import Session
from .models import User, Appointment, MedicineOrder, ChatHistory
from typing import Dict, Any, List, Optional
import datetime

class CRUDManager:
    def __init__(self, db: Session):
        self.db = db
    
    # User Operations
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone_number == phone_number).first()
    
    def create_user(self, user_data: Dict[str, Any]) -> User:
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # Appointment Operations
    def create_appointment(self, appointment_data: Dict[str, Any]) -> Appointment:
        appointment = Appointment(**appointment_data)
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
    
    def get_user_appointments(self, user_id: int, status: str = None) -> List[Appointment]:
        query = self.db.query(Appointment).filter(Appointment.user_id == user_id)
        if status:
            query = query.filter(Appointment.status == status)
        return query.all()
    
    def cancel_appointment(self, appointment_id: int) -> bool:
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appointment:
            appointment.status = "cancelled"
            self.db.commit()
            return True
        return False
    
    def reschedule_appointment(self, appointment_id: int, new_time: datetime.datetime) -> bool:
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appointment:
            appointment.scheduled_time = new_time
            appointment.status = "rescheduled"
            self.db.commit()
            return True
        return False
    
    # Medicine Order Operations
    def create_medicine_order(self, order_data: Dict[str, Any]) -> MedicineOrder:
        order = MedicineOrder(**order_data)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
    
    # Chat History Operations
    def add_chat_message(self, chat_data: Dict[str, Any]) -> ChatHistory:
        chat = ChatHistory(**chat_data)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat
    
    def get_chat_history(self, user_id: int, limit: int = 10) -> List[ChatHistory]:
        return self.db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
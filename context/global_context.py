from pydantic import BaseModel
from typing import List, Optional
import datetime

class UserContext(BaseModel):
    id: Optional[int] = None
    phone_number: str
    name: Optional[str] = None
    address: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime.datetime

class ChatHistory(BaseModel):
    messages: List[ChatMessage] = []
    
    def add_message(self, role: str, content: str):
        self.messages.append(ChatMessage(role=role, content=content, timestamp=datetime.datetime.now()))
    
    def get_recent_messages(self, count: int = 5):
        return self.messages[-count:]

class GlobalContext(BaseModel):
    user: UserContext
    chat_history: ChatHistory
    current_appointment: Optional[dict] = None
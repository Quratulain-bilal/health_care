from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

from config.settings import settings
from database.session import SessionLocal, get_db
from database.models import Base, engine
from agents.main_agent import HealthcareAgent

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare AI Agent")

class ChatRequest(BaseModel):
    phone_number: str
    message: str

class ChatResponse(BaseModel):
    success: bool
    response: str
    intent: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        db = SessionLocal()
        agent = HealthcareAgent(db, settings.OPENAI_API_KEY)
        
        agent.initialize_context(request.phone_number)
        result = agent.process_message(request.message)
        
        db.close()
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Healthcare AI Agent API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
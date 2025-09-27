from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from config.settings import settings
from database.session import SessionLocal, get_db
from database.models import Base, engine
from agents.healthcare_agent import HealthcareAgent

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare AI Agent API")

class ChatRequest(BaseModel):
    phone_number: str
    message: str
    user_data: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    intent: str
    tool_used: bool

def get_healthcare_agent(db = Depends(get_db)):
    return HealthcareAgent(db, settings.OPENAI_API_KEY)

@app.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest, agent: HealthcareAgent = Depends(get_healthcare_agent)):
    try:
        # Initialize context with user data
        agent.initialize_context(request.phone_number, request.user_data)
        
        # Process message
        result = agent.process_message(request.message)
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Healthcare AI Agent API is running with OpenAI Agents SDK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

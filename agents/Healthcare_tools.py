from agents import Agent, Runner
from typing import Dict, Any, List
import json

from database.crud import CRUDManager
from context.global_context import GlobalContext
from agents.healthcare_tools import HealthcareTools

class HealthcareAgent:
    def __init__(self, db_session, openai_api_key: str, model: str = "gpt-4-1106-preview"):
        self.db = CRUDManager(db_session)
        self.context = None
        self.healthcare_tools = None
        
        # Create the OpenAI Agent
        self.agent = Agent(
            name="Healthcare Assistant",
            instructions=self._get_agent_instructions(),
            model=model,
            tools=[]  # Will be populated after context initialization
        )
    
    def _get_agent_instructions(self) -> str:
        """Get the agent's system instructions."""
        return """
        You are a professional Healthcare Assistant for a multi-specialty hospital. 
        Your role is to assist patients with medical appointments, medicine orders, 
        and preliminary symptom guidance.

        CORE RESPONSIBILITIES:
        1. APPOINTMENT MANAGEMENT: Schedule appointments with appropriate specialists
        2. MEDICINE SERVICES: Search and order medicines from partner pharmacies  
        3. SYMPTOM GUIDANCE: Provide preliminary symptom analysis (with disclaimers)
        4. DOCTOR INFORMATION: Help find suitable doctors based on specialization

        PROFESSIONAL GUIDELINES:
        - Always be empathetic, patient, and professional
        - Never provide medical diagnoses - only guidance and recommendations
        - For emergencies, direct to immediate medical care
        - Verify all details before confirming appointments or orders
        - Maintain patient confidentiality and privacy

        TOOL USAGE:
        - Use schedule_appointment for booking doctor appointments
        - Use search_medicines for medicine price comparison
        - Use order_medicine for placing medicine orders
        - Use symptom_checker for preliminary symptom analysis
        - Use find_doctors to search for specialists

        Always explain what you're doing before using tools and summarize results clearly.
        """
    
    def initialize_context(self, user_phone: str, user_data: Dict[str, Any] = None):
        """Initialize user context and bind tools to agent."""
        # Get or create user
        user = self.db.get_user_by_phone(user_phone)
        if not user:
            if not user_data:
                user_data = {"phone_number": user_phone}
            user = self.db.create_user(user_data)
        
        # Initialize context
        self.context = GlobalContext(
            user=UserContext(
                id=user.id,
                phone_number=user.phone_number,
                name=user.name,
                address=user.address
            ),
            chat_history=ChatHistory()
        )
        
        # Initialize tools with context
        self.healthcare_tools = HealthcareTools(self.db, self.context)
        
        # Bind tools to agent
        self.agent.tools = [
            self.healthcare_tools.schedule_appointment,
            self.healthcare_tools.search_medicines,
            self.healthcare_tools.order_medicine,
            self.healthcare_tools.symptom_checker,
            self.healthcare_tools.find_doctors
        ]
    
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process user message using OpenAI Agents SDK Runner."""
        try:
            if not self.context:
                return {"error": "Context not initialized. Call initialize_context() first."}
            
            # Add user message to chat history
            self.context.chat_history.add_message("user", user_message)
            
            # Run the agent using OpenAI Agents SDK Runner
            result = Runner.run(
                self.agent,
                input=user_message,
                additional_messages=self._get_chat_history_for_ai()
            )
            
            # Add AI response to chat history
            self.context.chat_history.add_message("assistant", result.final_output)
            
            # Save to database
            self.db.add_chat_message({
                "user_id": self.context.user.id,
                "message": user_message,
                "response": result.final_output,
                "intent": self._detect_intent_from_result(result)
            })
            
            return {
                "success": True,
                "response": result.final_output,
                "tool_used": self._has_tool_calls(result),
                "intent": self._detect_intent_from_result(result)
            }
            
        except Exception as e:
            error_msg = "I apologize, but I'm experiencing technical difficulties. Please try again."
            return {
                "success": False,
                "response": error_msg,
                "error": str(e)
            }
    
    def _get_chat_history_for_ai(self) -> List[Dict[str, str]]:
        """Convert chat history to format expected by OpenAI API."""
        messages = []
        for msg in self.context.chat_history.get_recent_messages(6):  # Last 6 messages
            messages.append({
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            })
        return messages
    
    def _has_tool_calls(self, result) -> bool:
        """Check if the result involved tool calls."""
        return hasattr(result, 'steps') and any(
            hasattr(step, 'tool_calls') and step.tool_calls 
            for step in result.steps
        )
    
    def _detect_intent_from_result(self, result) -> str:
        """Detect intent from the agent's tool usage."""
        if not self._has_tool_calls(result):
            return "general_inquiry"
        
        # Map tool names to intents
        tool_intent_map = {
            "schedule_appointment": "appointment_booking",
            "search_medicines": "medicine_search", 
            "order_medicine": "medicine_order",
            "symptom_checker": "symptom_analysis",
            "find_doctors": "doctor_search"
        }
        
        for step in result.steps:
            if hasattr(step, 'tool_calls') and step.tool_calls:
                tool_name = step.tool_calls[0].name
                return tool_intent_map.get(tool_name, "general_inquiry")
        
        return "general_inquiry"

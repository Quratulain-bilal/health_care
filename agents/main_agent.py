from openai import OpenAI
from typing import Dict, Any
import json
from database.crud import CRUDManager
from context.global_context import GlobalContext
from agents.healthcare_tools import HealthcareTools

class HealthcareAgent:
    def __init__(self, db_session, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.db = CRUDManager(db_session)
        self.healthcare_tools = HealthcareTools(self.client)
        self.context = None
    
    def initialize_context(self, phone_number: str):
        """Initialize user context"""
        user = self.db.get_user_by_phone(phone_number)
        if not user:
            user = self.db.create_user({"phone_number": phone_number})
        
        self.context = GlobalContext(
            user=UserContext(
                id=user.id,
                phone_number=user.phone_number,
                name=user.name,
                address=user.address
            ),
            chat_history=ChatHistory()
        )
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process user message with AI and tools"""
        try:
            # Add to chat history
            self.context.chat_history.add_message("user", message)
            
            # Get AI response with tool usage
            response = self._get_ai_response(message)
            
            # Save to database
            self.db.add_chat_message({
                "user_id": self.context.user.id,
                "message": message,
                "response": response["response"],
                "intent": response.get("intent", "general")
            })
            
            return response
            
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}", "error": str(e)}
    
    def _get_ai_response(self, message: str) -> Dict[str, Any]:
        """Get AI response with tool usage"""
        # Simple intent detection
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['appointment', 'schedule', 'book', 'doctor']):
            return self._handle_appointment_request(message)
        elif any(word in message_lower for word in ['medicine', 'drug', 'pill', 'tablet']):
            return self._handle_medicine_request(message)
        elif any(word in message_lower for word in ['symptom', 'fever', 'pain', 'headache']):
            return self._handle_symptom_request(message)
        else:
            return self._get_general_response(message)
    
    def _handle_appointment_request(self, message: str) -> Dict[str, Any]:
        """Handle appointment related requests"""
        # Extract date and time from message (simplified)
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', message)
        time_match = re.search(r'(\d{1,2}:\d{2})', message)
        
        date = date_match.group(1) if date_match else "2024-01-15"
        time = time_match.group(1) if time_match else "14:00"
        
        result = self.healthcare_tools.schedule_appointment(date, time)
        
        if "error" in result:
            response = f"I couldn't schedule the appointment. {result['error']}"
        else:
            response = f"✅ {result['message']}\n\nDoctor: {result['doctor_name']}\nSpecialization: {result['specialization']}\nFee: Rs. {result['fee']}"
        
        return {"success": True, "response": response, "intent": "appointment"}
    
    def _handle_medicine_request(self, message: str) -> Dict[str, Any]:
        """Handle medicine related requests"""
        # Extract medicine name
        medicine_keywords = ['panadol', 'ventolin', 'amoxil', 'brufen', 'medicine', 'tablet']
        medicine_name = next((word for word in message.lower().split() if word in medicine_keywords), "panadol")
        
        if 'order' in message.lower() or 'buy' in message.lower():
            result = self.healthcare_tools.order_medicine(medicine_name, 1)
            intent = "order"
        else:
            result = self.healthcare_tools.search_medicines(medicine_name)
            intent = "search"
        
        if "error" in result:
            response = f"Medicine search failed: {result['error']}"
        else:
            if intent == "search":
                best = result['best_option']
                response = f"💊 Found {len(result['medicines'])} medicines\nBest price: Rs. {best['price']} at {best['pharmacy']} ({best['delivery_time']})"
            else:
                response = f"✅ {result['message']}\nTotal: Rs. {result['total_amount']}\nDelivery: {result['delivery_time']}"
        
        return {"success": True, "response": response, "intent": intent}
    
    def _handle_symptom_request(self, message: str) -> Dict[str, Any]:
        """Handle symptom checking"""
        symptoms = [word for word in message.lower().split() if word in ['fever', 'headache', 'cough', 'pain', 'cold']]
        age = 30  # Default age
        
        result = self.healthcare_tools.symptom_checker(symptoms, age)
        
        if "error" in result:
            response = f"Symptom analysis failed: {result['error']}"
        else:
            response = f"🩺 Symptom Analysis:\n{result['analysis']}\n\nRecommendation: {result['recommendation']}\nUrgency: {result['urgency']}"
        
        return {"success": True, "response": response, "intent": "symptoms"}
    
    def _get_general_response(self, message: str) -> Dict[str, Any]:
        """Get general AI response"""
        prompt = f"""
        You are a healthcare assistant. Respond professionally to: "{message}"
        
        Available services:
        - Book appointments with specialists
        - Medicine search and delivery
        - Symptom checking
        - General health advice
        
        Keep response helpful and suggest relevant services.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        return {
            "success": True, 
            "response": response.choices[0].message.content,
            "intent": "general"
        }
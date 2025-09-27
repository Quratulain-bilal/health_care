from database.session import SessionLocal
from agents.healthcare_agent import HealthcareAgent
from config.settings import settings

def main():
    print("🏥 Healthcare AI Agent - OpenAI Agents SDK")
    print("=" * 50)
    
    db = SessionLocal()
    agent = HealthcareAgent(db, settings.OPENAI_API_KEY)
    
    # Get user phone number
    phone = input("Enter patient phone number: ")
    name = input("Enter patient name (optional): ")
    
    user_data = {"phone_number": phone}
    if name:
        user_data["name"] = name
    
    agent.initialize_context(phone, user_data)
    
    print("\n🤖 Agent: Hello! I'm your healthcare assistant. How can I help you today?")
    print("You can: Book appointments, Search medicines, Order drugs, Check symptoms")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("👤 Patient: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            if not user_input:
                continue
                
            # Process message
            result = agent.process_message(user_input)
            
            if result['success']:
                print(f"🤖 Agent: {result['response']}")
                if result['tool_used']:
                    print(f"   [Intent: {result['intent'].replace('_', ' ').title()}]")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ System error: {str(e)}")
    
    db.close()
    print("\nThank you for using Healthcare AI Agent! 👋")

if __name__ == "__main__":
    main()

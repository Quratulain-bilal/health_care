from database.session import SessionLocal
from agents.main_agent import HealthcareAgent
from config.settings import settings

def main():
    print("🏥 Healthcare AI Agent - Command Line Interface")
    print("Type 'quit' to exit\n")
    
    db = SessionLocal()
    agent = HealthcareAgent(db, settings.OPENAI_API_KEY)
    
    phone = input("Enter patient phone number: ")
    agent.initialize_context(phone)
    
    while True:
        message = input("\n👤 Patient: ")
        if message.lower() in ['quit', 'exit', 'bye']:
            break
        
        result = agent.process_message(message)
        print(f"🤖 Agent: {result['response']}")
    
    db.close()
    print("Goodbye! 👋")

if __name__ == "__main__":
    main()
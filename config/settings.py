import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

settings = Settings()
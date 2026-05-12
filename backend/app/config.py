import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")  # Specific folder ID
    MAX_RESULTS = 50
    
config = Config()
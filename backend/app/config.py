import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    DRIVE_SCOPES = os.getenv("DRIVE_SCOPES", "https://www.googleapis.com/auth/drive.readonly")
    
    # Search configurations
    MAX_RESULTS = 50
    DATE_FORMAT = "%Y-%m-%d"
    
config = Config()
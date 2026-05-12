import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
    MAX_RESULTS = 50
    
    @classmethod
    def validate(cls):
        """Check if all required configuration is present"""
        missing = []
        
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        
        if not cls.DRIVE_FOLDER_ID:
            missing.append("DRIVE_FOLDER_ID")
        
        # Check for credentials (either file or env var)
        has_creds = bool(os.getenv("GOOGLE_CREDENTIALS_JSON")) or bool(cls.SERVICE_ACCOUNT_FILE)
        if not has_creds:
            missing.append("GOOGLE_CREDENTIALS_JSON or SERVICE_ACCOUNT_FILE")
        
        return missing
    
config = Config()
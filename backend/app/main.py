from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import config
from .drive_service import GoogleDriveService
from .agent import DriveConversationalAgent
from .schemas import SearchRequest, SearchResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Google Drive AI Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
drive_service = GoogleDriveService(
    credentials_path=config.GOOGLE_APPLICATION_CREDENTIALS,
    scopes=[config.DRIVE_SCOPES]
)

# Authenticate Drive service
try:
    drive_service.authenticate()
    logger.info("Google Drive authentication successful")
except Exception as e:
    logger.error(f"Google Drive authentication failed: {e}")

# Initialize conversational agent
agent = DriveConversationalAgent(drive_service)

@app.get("/")
async def root():
    return {"message": "Google Drive AI Agent API", "status": "running"}

@app.post("/search", response_model=SearchResponse)
async def search_drive(request: SearchRequest):
    """Search Google Drive using natural language"""
    try:
        result = await agent.process_query(request.query, request.user_id)
        
        return SearchResponse(
            success=result["success"],
            message=result["response"],
            results=[],  # Would populate with actual file objects
            total_results=result.get("files_found", 0)
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: SearchRequest):
    """Chat with the Drive assistant"""
    try:
        result = await agent.process_query(request.query, request.user_id)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear_memory")
async def clear_memory(user_id: str = None):
    """Clear conversation memory"""
    agent.clear_memory()
    return {"message": "Memory cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

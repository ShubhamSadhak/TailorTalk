from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import config
from .drive_service import GoogleDriveService
from .agent import DriveConversationalAgent
from .schemas import SearchRequest, SearchResponse
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Google Drive AI Agent with Service Account", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate configuration
missing_vars = config.validate()
if missing_vars:
    logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    logger.error("Please add these to your Render environment settings")
    drive_service = None
    agent = None
else:
    # Initialize Drive Service with Service Account
    try:
        drive_service = GoogleDriveService(
            service_account_file=getattr(config, 'SERVICE_ACCOUNT_FILE', None),
            folder_id=config.DRIVE_FOLDER_ID
        )
        
        # Authenticate Drive service
        drive_service.authenticate()
        logger.info(f"✅ Google Drive Service Account authentication successful")
        logger.info(f"📁 Searching within folder ID: {config.DRIVE_FOLDER_ID}")
        
        # Initialize conversational agent
        agent = DriveConversationalAgent(drive_service)
        logger.info(f"✅ Conversational agent initialized with Gemini")
        
    except Exception as e:
        logger.error(f"❌ Google Drive authentication failed: {e}")
        drive_service = None
        agent = None

@app.get("/")
async def root():
    """Health check endpoint"""
    status = {
        "message": "Google Drive AI Agent with Service Account",
        "status": "running",
        "authentication": "✅ Service Account" if drive_service else "❌ Failed",
        "folder_id": config.DRIVE_FOLDER_ID if drive_service else None,
        "env_vars_set": {
            "GEMINI_API_KEY": bool(config.GEMINI_API_KEY),
            "DRIVE_FOLDER_ID": bool(config.DRIVE_FOLDER_ID),
            "GOOGLE_CREDENTIALS_JSON": bool(os.getenv("GOOGLE_CREDENTIALS_JSON")),
        }
    }
    return status

@app.get("/debug")
async def debug():
    """Debug endpoint to check configuration"""
    return {
        "has_gemini_key": bool(config.GEMINI_API_KEY),
        "has_drive_folder_id": bool(config.DRIVE_FOLDER_ID),
        "folder_id_value": config.DRIVE_FOLDER_ID,
        "has_service_account_file": bool(config.SERVICE_ACCOUNT_FILE),
        "has_google_creds_json": bool(os.getenv("GOOGLE_CREDENTIALS_JSON")),
        "drive_service_initialized": drive_service is not None,
        "agent_initialized": agent is not None,
        "missing_vars": config.validate()
    }

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    if not drive_service:
        return {
            "status": "unhealthy",
            "error": "Drive service not initialized",
            "folder_id": config.DRIVE_FOLDER_ID,
            "missing_config": config.validate()
        }
    
    # Test if folder is accessible
    try:
        test_search = drive_service.search_files(max_results=1)
        return {
            "status": "healthy",
            "folder_accessible": True,
            "folder_id": config.DRIVE_FOLDER_ID,
            "message": "Service account can access the folder",
            "files_found": len(test_search)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "folder_accessible": False,
            "error": str(e),
            "folder_id": config.DRIVE_FOLDER_ID
        }

@app.post("/search", response_model=SearchResponse)
async def search_drive(request: SearchRequest):
    """Search Google Drive using natural language"""
    if not drive_service or not agent:
        raise HTTPException(status_code=503, detail="Drive service not initialized. Check /debug endpoint.")
    
    try:
        result = await agent.process_query(request.query, request.user_id)
        
        return SearchResponse(
            success=result["success"],
            message=result["response"],
            results=[],
            total_results=result.get("files_found", 0)
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: SearchRequest):
    """Chat with the Drive assistant"""
    if not drive_service or not agent:
        raise HTTPException(status_code=503, detail="Drive service not initialized")
    
    try:
        result = await agent.process_query(request.query, request.user_id)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear_memory")
async def clear_memory(user_id: str = None):
    """Clear conversation memory"""
    if agent:
        agent.clear_memory()
        return {"message": "Memory cleared successfully"}
    return {"message": "Agent not available"}

@app.get("/folder-info")
async def get_folder_info():
    """Get information about the configured folder"""
    if not drive_service:
        raise HTTPException(status_code=503, detail="Drive service not initialized")
    
    try:
        # Get folder metadata
        folder = drive_service.service.files().get(
            fileId=config.DRIVE_FOLDER_ID,
            fields='id, name, mimeType, createdTime, modifiedTime'
        ).execute()
        
        # Count files in folder
        files = drive_service.search_files(max_results=100)
        
        return {
            "folder_id": folder.get('id'),
            "folder_name": folder.get('name'),
            "created_time": folder.get('createdTime'),
            "file_count": len(files),
            "message": f"Folder contains {len(files)} files"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
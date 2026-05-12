from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None

class SearchResponse(BaseModel):
    success: bool
    message: str
    results: List[dict]
    total_results: int

class FileInfo(BaseModel):
    id: str
    name: str
    mime_type: str
    created_time: Optional[datetime]
    modified_time: Optional[datetime]
    size: Optional[str]
    web_view_link: Optional[str]

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime

class ChatHistory(BaseModel):
    user_id: str
    messages: List[ChatMessage]
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class FileUploadRequest(BaseModel):
    filename: str
    content_type: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ToolResponse(BaseModel):
    tool_name: str
    result: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    response: str
    data: Optional[Any] = None
    visualization: Optional[Dict[str, Any]] = None
    tool_used: Optional[str] = None
    column_order: Optional[List[str]] = None

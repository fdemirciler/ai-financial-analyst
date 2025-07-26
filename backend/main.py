from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any
import uuid

from .config import settings
from .models import ChatRequest, AnalysisResponse
from .session import session_manager
from .orchestrator import orchestrator
from .logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(
        "Analysis Agent starting up",
        extra={
            "llm_model": settings.LLM_MODEL,
            "max_file_size": settings.MAX_FILE_SIZE,
        },
    )
    yield
    # Shutdown
    logger.info("Analysis Agent shutting down")


app = FastAPI(title="Analysis Agent", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload")
async def upload_file(session_id: str = Form(...), file: UploadFile = File(...)):
    """Handle file upload and initial processing"""
    logger.info(
        "File upload request",
        extra={"session_id": session_id, "file_name": file.filename},
    )

    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        logger.warning(
            "File size exceeded",
            extra={
                "session_id": session_id,
                "filename": file.filename,
                "file_size": len(content),
                "max_size": settings.MAX_FILE_SIZE,
            },
        )
        raise HTTPException(status_code=413, detail="File too large")

    # Reset file pointer
    await file.seek(0)

    # Create session if it doesn't exist
    if not session_manager.get_session(session_id):
        session_manager.create_session(session_id)

    try:
        result = await orchestrator.process_file_upload(
            session_id, content, file.filename
        )
        logger.info(
            "File uploaded successfully",
            extra={
                "session_id": session_id,
                "file_name": file.filename,
                "success": result.get("success"),
                "data_shape": result.get("data_shape"),
                "columns_count": len(result.get("columns", [])),
            },
        )
        return result
    except Exception as e:
        logger.error(
            "File upload failed",
            extra={
                "session_id": session_id,
                "file_name": file.filename,
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="An internal error occurred during file processing."
        )


@app.post("/api/chat", response_model=AnalysisResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat messages and analysis requests"""
    logger.info(
        "Chat request received",
        extra={"session_id": request.session_id, "user_message": request.message},
    )

    # Create session if it doesn't exist
    if not session_manager.get_session(request.session_id):
        session_manager.create_session(request.session_id)

    try:
        result = await orchestrator.process_chat_message(
            request.session_id, request.message
        )
        logger.info(
            "Chat response generated",
            extra={"session_id": request.session_id, **result},
        )
        return AnalysisResponse(
            response=result["response"],
            data=result.get("data"),
            tool_used=result.get("tool_used"),
        )
    except Exception as e:
        logger.error(
            "Chat processing failed",
            extra={"session_id": request.session_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred during chat processing.",
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Analysis Agent is running"}


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    session = session_manager.get_session(session_id)
    if session:
        return {
            "session_id": session_id,
            "has_data": session["data"] is not None,
            "has_metadata": session["metadata"] is not None,
            "conversation_length": len(session["conversation_history"]),
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

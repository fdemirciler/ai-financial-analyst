from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Dict, Any
import uuid
import os
from pathlib import Path

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

# Mount static files for production
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve the React frontend"""
        return FileResponse(static_dir / "index.html")

    @app.get("/{full_path:path}")
    async def serve_frontend_routes(full_path: str):
        """Serve frontend for all non-API routes (SPA routing)"""
        # Check if it's an API route
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Check if the file exists in static directory
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Default to index.html for SPA routing
        return FileResponse(static_dir / "index.html")


@app.post("/api/upload")
async def upload_file(session_id: str = Form(...), file: UploadFile = File(...)):
    """Handle file upload and initial processing with enhanced pipeline"""
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

        # Enhanced logging with pipeline information
        enhanced_info = result.get("enhanced_info", {})
        logger.info(
            "File uploaded successfully with enhanced pipeline",
            extra={
                "session_id": session_id,
                "file_name": file.filename,
                "success": result.get("success"),
                "data_shape": result.get("data_shape"),
                "columns_count": len(result.get("columns", [])),
                "quality_score": enhanced_info.get("quality_score", 0),
                "sheets_processed": enhanced_info.get("sheets_processed", 1),
                "layout_detected": enhanced_info.get("layout_detected", {}),
                "fallback_used": result.get("fallback_used", False),
            },
        )

        # Return enhanced response
        return {
            "success": result.get("success"),
            "message": result.get("message"),
            "data_shape": result.get("data_shape"),
            "columns": result.get("columns"),
            "enhanced_info": enhanced_info,
            "fallback_used": result.get("fallback_used", False),
        }

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
            column_order=result.get("column_order"),
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
    """Get enhanced session information including pipeline data"""
    session = session_manager.get_session(session_id)
    if session:
        pipeline_results = session_manager.get_pipeline_results(session_id)
        processing_summary = session_manager.get_processing_summary(session_id)
        quality_report = session_manager.get_data_quality_report(session_id)

        return {
            "session_id": session_id,
            "has_data": session["data"] is not None,
            "has_metadata": session["metadata"] is not None,
            "conversation_length": len(session["conversation_history"]),
            "enhanced_info": {
                "pipeline_results_count": len(pipeline_results),
                "current_sheet": session.get("current_sheet"),
                "processing_summary": processing_summary,
                "data_quality_score": (
                    quality_report.get("overall_quality_score", 0)
                    if quality_report
                    else 0
                ),
                "available_sheets": (
                    [
                        result.sheet
                        for result in pipeline_results
                        if hasattr(result, "sheet")
                    ]
                    if pipeline_results
                    else []
                ),
                "enhanced_features_available": len(pipeline_results) > 0,
            },
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/api/session/{session_id}/switch_sheet")
async def switch_sheet(session_id: str, sheet_name: str = Form(...)):
    """Switch to a different sheet for analysis"""
    success = session_manager.set_current_sheet(session_id, sheet_name)
    if success:
        return {
            "success": True,
            "message": f"Switched to sheet: {sheet_name}",
            "current_sheet": sheet_name,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Could not switch to sheet '{sheet_name}'. Sheet not found or session invalid.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

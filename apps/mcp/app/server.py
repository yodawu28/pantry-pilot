"""MCP Server API."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.types import HealthCheckResponse, GetContextRequest, GetImageRequest, ValidateRequest
from app.tools.get_image import get_image
from app.tools.validate_extraction import validate_extraction
from app.tools.get_receipt_context import get_receipt_context
from app.tools.ocr_text import ocr_extract_text
from packages.shared.shared.types import ImageData, ValidationResult, ReceiptContext


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # --- startup ---
    print("🚀 Starting Pantry Pilot MCP Server...")
    print(f"✅ MinIO Endpoint: {settings.minio_endpoint}")
    print(f"✅ Database URL: {settings.database_url}")
    print(f"✅ MCP Tools registered")
    
    yield  # app runs while we're yielded here
    
    # --- shutdown ---
    print("🛑 MCP Server shutdown complete")


app = FastAPI(
    title="Pantry Pilot MCP Server",
    description="Model Context Protocol tools for receipt extraction and validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pantry Pilot MCP Server",
        "version": "1.0.0",
        "tools": [
            "get-image",
            "validate",
            "get-context",
            "ocr-text",
        ],
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthCheckResponse)
def health():
    """Health check."""
    return HealthCheckResponse(
        status="ok",
        service="mcp-server",
        version="1.0.0"
    )


@app.post("/tools/get-image", response_model=ImageData)
async def tool_get_image(request: GetImageRequest):
    """
    MCP Tool: Fetch image from MinIO storage.

    Returns image bytes and metadata for agent processing.
    """
    try:
        return await get_image(request.image_path)
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to get image: {str(e)}")


@app.post("/tools/validate", response_model=ValidationResult)
async def tool_validate(request: ValidateRequest):
    """
    MCP Tool: Validate extraction results.
    
    Checks business rules and data quality.
    """
    try:
        return await validate_extraction(request.metadata, request.items)
    except Exception as e:
        raise HTTPException(500, detail=f"Validation failed: {str(e)}")


@app.post("/tools/get-context", response_model=ReceiptContext)
async def tool_get_context(request: GetContextRequest):
    """
    MCP Tool: Get receipt context from database.
    
    Provides historical data for agent reasoning.
    """
    try:
        return await get_receipt_context(request.receipt_id, request.user_id)
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to get context: {str(e)}")


@app.post("/tools/ocr-text")
async def tool_ocr_text(request: GetImageRequest):
    """
    MCP Tool: Extract raw text from receipt using EasyOCR.
    
    Returns raw text and line-by-line OCR results with confidence scores.
    """
    try:
        return await ocr_extract_text(request.image_path)
    except Exception as e:
        raise HTTPException(500, detail=f"OCR extraction failed: {str(e)}")
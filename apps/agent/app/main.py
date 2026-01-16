"""Agent API server - Main entry point."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.receipt_agent import ReceiptAgent
from app.schemas import ExtractionRequest, ExtractionResponse, OCRStatusResponse
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # --- startup ---
    print("🚀 Starting Pantry Pilot Agent...")
    print(f"✅ Agent initialized with model: {settings.openai_model}")
    print(f"✅ MCP Server URL: {settings.mcp_url}")
    
    # Verify OpenAI API key is set
    if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
        print("⚠️  WARNING: OPENAI_API_KEY is not set or using placeholder value!")
        print("   Please set OPENAI_API_KEY in your .env file")
    else:
        print(f"✅ OpenAI API Key loaded: {settings.openai_api_key[:10]}...")

    yield  # app runs while we're yielded here

    # --- shutdown ---
    print("🛑 Agent shutdown complete")


app = FastAPI(
    title="Pantry Pilot Agent",
    description="LLM agent for receipt extraction using Gemma-3n vision model",
    version="0.2.0",
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

# Initialize agent
agent = ReceiptAgent()

# In-memory status tracking (TODO: Move to Redis for production)
extraction_status = {}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pantry Pilot Agent",
        "version": "0.2.0",
        "model": settings.ollama_model,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """Health check."""
    return {
        "status": "ok",
        "service": "agent",
        "version": "0.2.0",
        "model": settings.ollama_model,
    }


@app.post("/extract", response_model=ExtractionResponse)
async def extract_receipt(request: ExtractionRequest):
    """
    Extract receipt data from image using Gemma-3n vision model.

    Returns JSON only - caller (API) handles database save.
    """
    try:
        # Mark as processing
        extraction_status[request.receipt_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting extraction...",
        }

        # Run extraction
        result = await agent.extract_from_receipt(request)

        # Update status
        extraction_status[request.receipt_id] = {
            "status": "completed" if result.success else "failed",
            "progress": 100,
            "message": "Extraction complete" if result.success else result.error_message,
        }

        return result

    except Exception as e:
        extraction_status[request.receipt_id] = {
            "status": "failed",
            "progress": 0,
            "message": str(e),
        }
        raise HTTPException(500, detail=f"Extraction failed: {str(e)}")


@app.get("/extract/{receipt_id}/status", response_model=OCRStatusResponse)
async def get_extraction_status(receipt_id: int):
    """
    Get OCR/extraction processing status.

    Useful for long-running extractions.
    """
    status = extraction_status.get(
        receipt_id, {"status": "unknown", "progress": 0, "message": "No extraction found"}
    )

    return OCRStatusResponse(
        receipt_id=receipt_id,
        status=status["status"],
        progress_percent=status["progress"],
        message=status["message"],
    )


@app.post("/extract/{receipt_id}/retry", response_model=ExtractionResponse)
async def retry_extraction(receipt_id: int, request: ExtractionRequest):
    """
    Retry failed extraction.

    Useful when first attempt fails due to timeout or bad image quality.
    """
    if request.receipt_id != receipt_id:
        raise HTTPException(400, "Receipt ID mismatch")

    return await extract_receipt(request)


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.agent_host,
        port=settings.agent_port,
        reload=True,
    )
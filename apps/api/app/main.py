from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import health_router, receipt_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

    yield  # app runs while we're yielded here

    # --- shutdown ---
    # (optional) close resources, flush queues, etc.
    # await engine.dispose()  # if you want to dispose engine on shutdown
    print("🛑 Shutdown complete")

app = FastAPI(
    title="Pantry Pilot API",
    description="Smart Pantry Pilot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], # TODO : need change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(receipt_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pantry Pilot API",
        "version": "1.0.0",
        "docs": "/docs",
    }

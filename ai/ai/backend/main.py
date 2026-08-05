import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

from ai.pipeline import ArkanaPipeline, PipelineConfig
from ai.backend.api.exceptions import register_exception_handlers
from ai.backend.api.routes import chat, visual, sites

logger = logging.getLogger(__name__)

# Load from environment variables / .env
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL not configured")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle.
    - Startup: Initialize ML models, DB pool, and global pipeline.
    - Shutdown: Await background tasks, close DB pool.
    """
    logger.info("Initializing Echolore Backend...")
    
    # Initialize DB pool
    try:
        db_pool = await asyncpg.create_pool(DB_URL)
        logger.info("Connected to PostgreSQL pool.")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        db_pool = None

    # Instantiate and warm up the AI Pipeline
    pipeline = ArkanaPipeline(config=PipelineConfig(), db_pool=db_pool)
    await pipeline.initialize()
    
    # Store in app state for dependency injection
    app.state.pipeline = pipeline
    logger.info("ArkanaPipeline warmed up and ready.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Echolore Backend...")
    
    # Await any pending background evaluation tasks
    pending_tasks = list(pipeline._background_tasks)
    if pending_tasks:
        logger.info(f"Waiting for {len(pending_tasks)} background evaluation tasks to complete...")
        await asyncio.gather(*pending_tasks, return_exceptions=True)
        
    if db_pool:
        await db_pool.close()
        logger.info("PostgreSQL pool closed.")

app = FastAPI(
    title="Echolore AI Backend",
    description="Arkana RAG Pipeline and Data API",
    version="1.0.0",
    lifespan=lifespan
)

# Allow CORS for the Node API Gateway and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend / gateway URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(visual.router, prefix="/api", tags=["visual"])
app.include_router(sites.router, prefix="/api", tags=["sites"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai.backend.main:app", host="0.0.0.0", port=8000, reload=True)

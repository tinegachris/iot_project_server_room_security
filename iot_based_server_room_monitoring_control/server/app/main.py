from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sys
from typing import Dict, Any
from contextlib import asynccontextmanager
import os

from .database import init_db, check_db_connection
from .routes import router
from .rate_limit import rate_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Use environment variable for log file path with a default
        logging.FileHandler(os.getenv('SERVER_LOG_FILE', os.path.join(os.getcwd(), 'logs/server.log')))
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    logger.info("Starting up...")
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")

        # Check database connection
        if not check_db_connection():
            logger.error("Failed to connect to database")
            # Optionally raise an error or handle differently if DB is critical
            # raise Exception("Database connection failed during startup")
        else:
            logger.info("Database connection successful")

    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Depending on the severity, you might want to prevent the app from starting
        # raise

    yield
    # Code to run on shutdown (if any)
    logger.info("Shutting down...")

# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Server Room Monitoring System",
    description="API for monitoring and controlling server room security",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limiter.rate_limit_middleware)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if check_db_connection() else "disconnected",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

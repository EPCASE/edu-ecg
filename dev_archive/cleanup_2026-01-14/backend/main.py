# main.py - FastAPI Backend Entry Point
"""
Edu-ECG Backend API
FastAPI application for ECG learning platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Edu-ECG API",
    description="API Backend pour plateforme pédagogique ECG avec correction LLM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://frontend:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Edu-ECG Backend API...")
    logger.info("📊 FastAPI version: 0.109.0+")
    logger.info("🔧 Environment: Development")
    # TODO: Initialize database connection
    # TODO: Initialize Redis connection
    # TODO: Load ontology cache


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Edu-ECG Backend API...")
    # TODO: Close database connections
    # TODO: Close Redis connections


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Edu-ECG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {
        "status": "healthy",
        "service": "edu-ecg-backend"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    # TODO: Implement Prometheus metrics
    return {
        "total_requests": 0,
        "total_corrections": 0,
        "llm_accuracy": 0.0
    }


# TODO: Import and include API routers
# from api.routes import auth, users, ecg_cases, sessions, responses
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(ecg_cases.router, prefix="/api/ecg-cases", tags=["ECG Cases"])
# app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
# app.include_router(responses.router, prefix="/api/responses", tags=["Responses"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

"""
MarketMoves API - Main FastAPI Application
Interactive Market Anomaly & Risk Intelligence Dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting MarketMoves API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Initializing database connections...")

    # Initialize databases (will be implemented in later phases)
    # await init_sqlite()
    # await init_duckdb()
    # await init_neo4j()

    yield

    # Shutdown
    logger.info("Shutting down MarketMoves API...")
    # Close database connections
    # await close_sqlite()
    # await close_duckdb()
    # await close_neo4j()


# Initialize FastAPI app
app = FastAPI(
    title="MarketMoves API",
    description="Interactive Market Anomaly & Risk Intelligence Dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "MarketMoves API",
        "version": "1.0.0",
        "status": "operational",
        "description": "Interactive Market Anomaly & Risk Intelligence Dashboard"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "operational",
            "database": "pending",  # Will update when databases are connected
            "neo4j": "pending",
            "llm": "pending"
        }
    }


@app.get("/api/v1/status")
async def api_status():
    """Detailed API status endpoint"""
    return {
        "api_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "market_data": "in_development",
            "risk_analysis": "in_development",
            "entity_graph": "in_development",
            "llm_insights": "in_development"
        }
    }


# API Routes
from app.api.routes import market_data, risk_analysis, insights, entity_graph

app.include_router(market_data.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(risk_analysis.router, prefix="/api/v1/risk", tags=["Risk Analysis"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["LLM Insights"])
app.include_router(entity_graph.router, prefix="/api/v1/entity", tags=["Entity Graph"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

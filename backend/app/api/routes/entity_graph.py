"""
Entity Graph API Routes
Provides endpoints for entity relationship visualization
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
import logging

from app.database.neo4j_manager import neo4j_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/graph/{ticker}")
async def get_company_graph(
    ticker: str,
    depth: int = Query(default=1, ge=1, le=3, description="Graph depth (1-3)")
) -> Dict[str, Any]:
    """
    Get entity relationship graph for a company

    Returns nodes and edges for visualization in frontend
    """
    try:
        # Check if Neo4j is connected
        if not neo4j_manager.driver:
            try:
                await neo4j_manager.connect()
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Neo4j service unavailable: {str(e)}"
                )

        # Get graph data
        graph_data = await neo4j_manager.get_company_graph(ticker, depth=depth)

        if not graph_data or len(graph_data.get('nodes', [])) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No graph data found for ticker: {ticker}"
            )

        return {
            "ticker": ticker,
            "graph": graph_data,
            "legend": {
                "Company": {"color": "#4A90E2", "description": "Public Company"},
                "Lawsuit": {"color": "#E74C3C", "description": "Legal Action"},
                "Executive": {"color": "#F39C12", "description": "Company Executive"},
                "Subsidiary": {"color": "#27AE60", "description": "Subsidiary Entity"},
                "RegulatoryAction": {"color": "#8E44AD", "description": "Regulatory Action"}
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching graph for {ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/entities/{ticker}")
async def get_company_entities(ticker: str) -> Dict[str, Any]:
    """
    Get all entities related to a company (without graph structure)

    Returns lists of subsidiaries, executives, lawsuits, and regulatory actions
    """
    try:
        if not neo4j_manager.driver:
            try:
                await neo4j_manager.connect()
            except Exception as e:
                raise HTTPException(
                    status_code=503,
                    detail="Neo4j service unavailable"
                )

        entities = await neo4j_manager.get_company_entities(ticker)

        return {
            "ticker": ticker,
            "entities": entities,
            "summary": {
                "subsidiaries_count": len(entities.get('subsidiaries', [])),
                "executives_count": len(entities.get('executives', [])),
                "lawsuits_count": len(entities.get('lawsuits', [])),
                "regulatory_actions_count": len(entities.get('regulatory_actions', []))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching entities for {ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/lawsuits/{ticker}")
async def get_company_lawsuits(ticker: str) -> Dict[str, Any]:
    """
    Get lawsuit information for risk analysis
    """
    try:
        if not neo4j_manager.driver:
            try:
                await neo4j_manager.connect()
            except Exception as e:
                return {
                    "ticker": ticker,
                    "available": False,
                    "message": "Neo4j service unavailable",
                    "data": {
                        "lawsuit_count": 0,
                        "avg_impact": 0.0,
                        "high_severity_count": 0,
                        "total_impact": 0.0
                    }
                }

        lawsuit_data = await neo4j_manager.get_lawsuits_for_risk(ticker)

        return {
            "ticker": ticker,
            "available": True,
            "data": lawsuit_data
        }

    except Exception as e:
        logger.error(f"Error fetching lawsuits for {ticker}: {e}")
        return {
            "ticker": ticker,
            "available": False,
            "message": str(e),
            "data": {
                "lawsuit_count": 0,
                "avg_impact": 0.0,
                "high_severity_count": 0,
                "total_impact": 0.0
            }
        }


@router.get("/health")
async def graph_health_check() -> Dict[str, Any]:
    """
    Check Neo4j connection health
    """
    try:
        if neo4j_manager.driver:
            neo4j_manager.driver.verify_connectivity()
            return {
                "status": "healthy",
                "neo4j": "connected",
                "features": ["entity_graph", "lawsuit_tracking", "executive_mapping"]
            }
        else:
            return {
                "status": "degraded",
                "neo4j": "disconnected",
                "message": "Graph features unavailable"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "neo4j": "error",
            "error": str(e)
        }

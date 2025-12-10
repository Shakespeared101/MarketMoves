"""LLM Insights API Routes"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.llm_client import llm_client
from app.services.rag_service import rag_service
from app.services.risk_engine import risk_engine

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    ticker: str = None


class RiskStoryRequest(BaseModel):
    ticker: str


@router.post("/query")
async def query_documents(request: QueryRequest):
    """Query documents using RAG"""
    result = await rag_service.answer_question(request.question, request.ticker)
    return result


@router.post("/risk-story")
async def generate_risk_story(request: RiskStoryRequest):
    """Generate risk narrative for a company"""
    # Get risk data
    risk_data = await risk_engine.calculate_overall_risk(request.ticker)

    # Get company info
    from app.database.sqlite_manager import db_manager
    company = await db_manager.get_company(request.ticker)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get recent news for context
    news = await db_manager.get_recent_news(request.ticker, limit=5)
    recent_events = [article['headline'] for article in news]

    # Generate story
    story = await llm_client.generate_risk_story(
        company_name=company['name'],
        ticker=request.ticker,
        risk_score=risk_data['overall_risk_score'],
        risk_factors=risk_data['components'],
        recent_events=recent_events
    )

    return {
        "ticker": request.ticker,
        "company_name": company['name'],
        "story": story,
        "risk_data": risk_data
    }

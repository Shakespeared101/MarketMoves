"""
LLM Client for Ollama Integration
Handles all LLM inference requests
"""

import ollama
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for LLM inference using Ollama"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text completion

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })

            messages.append({
                'role': 'user',
                'content': prompt
            })

            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=messages,
                options={
                    'temperature': temperature or self.temperature,
                    'num_predict': max_tokens or self.max_tokens
                }
            )

            return response['message']['content']

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"Error: Unable to generate response. {str(e)}"

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text completion"""
        try:
            messages = []

            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})

            messages.append({'role': 'user', 'content': prompt})

            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={'temperature': self.temperature}
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"Error: {str(e)}"

    async def analyze_risk_factors(self, risk_text: str, company: str) -> str:
        """Analyze risk factors from 10-K filing"""
        system_prompt = """You are a financial risk analyst. Analyze the provided risk factors
        and summarize the top 3-5 most significant risks in a concise, professional manner."""

        prompt = f"""Analyze the following risk factors for {company}:

{risk_text[:4000]}

Provide a concise summary of the top risks and their potential impact."""

        return await self.generate(prompt, system_prompt=system_prompt)

    async def generate_risk_story(
        self,
        company_name: str,
        ticker: str,
        risk_score: float,
        risk_factors: Dict[str, float],
        recent_events: List[str]
    ) -> str:
        """Generate a narrative risk story"""
        system_prompt = """You are a financial analyst creating risk narratives.
        Synthesize the provided data into a clear, concise risk assessment story."""

        prompt = f"""Create a risk narrative for {company_name} ({ticker}):

Overall Risk Score: {risk_score}/10

Risk Factor Breakdown:
- Volatility: {risk_factors.get('volatility', 0)}/10
- Litigation: {risk_factors.get('litigation', 0)}/10
- Sentiment: {risk_factors.get('sentiment', 0)}/10
- Financial Anomalies: {risk_factors.get('financial_anomaly', 0)}/10

Recent Events:
{chr(10).join(f"- {event}" for event in recent_events[:5])}

Provide a 2-3 paragraph risk assessment story."""

        return await self.generate(prompt, system_prompt=system_prompt, temperature=0.7)

    async def answer_query(self, query: str, context: str) -> str:
        """Answer user query based on context (RAG)"""
        system_prompt = """You are a financial data assistant. Answer questions accurately
        based on the provided context. If you don't know, say so."""

        prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        return await self.generate(prompt, system_prompt=system_prompt)

    async def is_model_available(self) -> bool:
        """Check if Ollama model is available"""
        try:
            models = await asyncio.to_thread(ollama.list)
            available_models = [m['name'] for m in models.get('models', [])]
            return self.model in available_models
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False


# Global instance
llm_client = LLMClient()

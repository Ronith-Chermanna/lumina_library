"""Ollama (local Llama 3) LLM adapter."""

from __future__ import annotations

import logging

import httpx

from app.domain.interfaces.llm import LLMInterface
from app.infrastructure.llm.prompts import (
    BOOK_SUMMARY_PROMPT,
    REVIEW_ANALYSIS_PROMPT,
    SENTIMENT_PROMPT,
)

logger = logging.getLogger(__name__)


class OllamaLLM(LLMInterface):
    """Communicates with a locally-hosted Ollama instance running Llama 3/phi3."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def _generate(self, prompt: str) -> str:
        """Send a prompt to the Ollama generate endpoint."""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate", json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    async def summarize_book(self, text: str) -> str:
        prompt = BOOK_SUMMARY_PROMPT.format(text=text[:2000])  # Truncate for context window
        return await self._generate(prompt)

    async def analyze_reviews(self, reviews: list[str]) -> str:
        combined = "\n---\n".join(reviews[-20:])  # Last 20 reviews
        prompt = REVIEW_ANALYSIS_PROMPT.format(reviews=combined)
        return await self._generate(prompt)

    async def classify_sentiment(self, text: str) -> str:
        prompt = SENTIMENT_PROMPT.format(text=text[:2000])
        result = await self._generate(prompt)
        # Normalise to one of the expected labels
        lower = result.lower().strip()
        if "positive" in lower:
            return "positive"
        if "negative" in lower:
            return "negative"
        return "neutral"

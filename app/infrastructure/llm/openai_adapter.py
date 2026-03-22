"""OpenAI LLM adapter — drop-in replacement for Ollama.

Switch by setting ``LLM_PROVIDER=openai`` in `.env`.
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from app.domain.interfaces.llm import LLMInterface
from app.infrastructure.llm.prompts import (
    BOOK_SUMMARY_PROMPT,
    REVIEW_ANALYSIS_PROMPT,
    SENTIMENT_PROMPT,
)

logger = logging.getLogger(__name__)


class OpenAILLM(LLMInterface):
    """Uses the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _chat(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.5,
            max_tokens=1024,
        )
        return (response.choices[0].message.content or "").strip()

    async def summarize_book(self, text: str) -> str:
        return await self._chat(
            system="You are a professional book summariser.",
            user=BOOK_SUMMARY_PROMPT.format(text=text[:2000]),
        )

    async def analyze_reviews(self, reviews: list[str]) -> str:
        combined = "\n---\n".join(reviews[-20:])
        return await self._chat(
            system="You are a literary critic AI.",
            user=REVIEW_ANALYSIS_PROMPT.format(reviews=combined),
        )

    async def classify_sentiment(self, text: str) -> str:
        result = await self._chat(
            system="Classify sentiment. Reply with one word only.",
            user=SENTIMENT_PROMPT.format(text=text[:2000]),
        )
        lower = result.lower().strip()
        if "positive" in lower:
            return "positive"
        if "negative" in lower:
            return "negative"
        return "neutral"

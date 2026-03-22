"""LLM interface — abstracts generative-AI interactions.

Implementations can target Ollama (Llama 3), OpenAI, or any other provider
without changing business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMInterface(ABC):
    """Contract that every LLM adapter must fulfil."""

    @abstractmethod
    async def summarize_book(self, text: str) -> str:
        """Generate a concise summary of the given book text."""

    @abstractmethod
    async def analyze_reviews(self, reviews: list[str]) -> str:
        """Produce a rolling consensus from a list of review texts."""

    @abstractmethod
    async def classify_sentiment(self, text: str) -> str:
        """Return a sentiment label: positive / neutral / negative."""

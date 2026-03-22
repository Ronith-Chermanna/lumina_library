"""Structured prompt templates for LLM interactions.

Keeping prompts in one place makes them reusable and testable.
"""

from __future__ import annotations

BOOK_SUMMARY_PROMPT = """You are a professional book summariser.
Given the following book text, produce a clear, concise summary (150-250 words)
highlighting the main themes, plot points, and key takeaways.

Book text:
\"\"\"
{text}
\"\"\"

Summary:"""

REVIEW_ANALYSIS_PROMPT = """You are a literary critic AI.
Below are reader reviews for a book.  Synthesize them into a single "rolling
consensus" paragraph (100-200 words) that captures the dominant sentiment,
recurring praise, and common criticisms.

Reviews:
{reviews}

Consensus:"""

SENTIMENT_PROMPT = """Classify the sentiment of the following book review.
Reply with EXACTLY one word: positive, neutral, or negative.

Review:
\"\"\"
{text}
\"\"\"

Sentiment:"""

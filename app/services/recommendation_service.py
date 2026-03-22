"""Recommendation service — ML-based content filtering engine.

Strategy
--------
We use **Content-Based Filtering** via TF-IDF on book genre/tag strings
combined with a user-preference weight vector.

1.  Build a "feature string" for each book: ``genre + " " + description_snippet``.
2.  Vectorise with TF-IDF.
3.  Build a user-profile vector from their weighted preference tags.
4.  Compute cosine similarity between the user vector and every book vector.
5.  Rank and return the top-N books the user hasn't already borrowed.
"""

from __future__ import annotations

import logging
import uuid

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.domain.interfaces.book_repository import BookRepositoryInterface
from app.domain.interfaces.preference_repository import PreferenceRepositoryInterface
from app.domain.schemas.recommendation import RecommendationItem, RecommendationResponse

logger = logging.getLogger(__name__)


class RecommendationService:
    """Content-based recommendation engine."""

    def __init__(
        self,
        book_repo: BookRepositoryInterface,
        pref_repo: PreferenceRepositoryInterface,
        top_n: int = 10,
    ) -> None:
        self._book_repo = book_repo
        self._pref_repo = pref_repo
        self._top_n = top_n

    @staticmethod
    def _book_feature_string(genre: str | None, description: str | None) -> str:
        """Concatenate genre and truncated description into a feature string."""
        parts: list[str] = []
        if genre:
            parts.append(genre)
        if description:
            parts.append(description[:300])
        return " ".join(parts) if parts else "general"

    async def recommend(
        self, user_id: uuid.UUID
    ) -> RecommendationResponse:
        """Return personalised book recommendations for the given user."""
        # 1. Fetch all books and user preferences
        all_books = await self._book_repo.get_all_books()
        user_prefs = await self._pref_repo.get_user_preferences(user_id)
        user_borrows = await self._book_repo.get_user_borrows(user_id)

        if not all_books:
            return RecommendationResponse(user_id=user_id, recommendations=[])

        # 2. Build feature strings and user profile
        borrowed_ids = {b.book_id for b in user_borrows}
        book_features = [
            self._book_feature_string(b.genre, b.description) for b in all_books
        ]

        # Build a synthetic user-profile document from preference tags
        if user_prefs:
            user_profile = " ".join(
                f"{p.tag} " * max(1, int(p.weight)) for p in user_prefs
            )
        elif user_borrows:
            # Fall back to genres of borrowed books
            borrowed_genres = [
                b.genre for b in all_books if b.id in borrowed_ids and b.genre
            ]
            user_profile = " ".join(borrowed_genres) if borrowed_genres else "general"
        else:
            user_profile = "general"

        # 3. TF-IDF vectorisation
        corpus = book_features + [user_profile]
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)

        user_vector = tfidf_matrix[-1]
        book_vectors = tfidf_matrix[:-1]

        # 4. Cosine similarity
        similarities = cosine_similarity(user_vector, book_vectors).flatten()

        # 5. Rank — exclude already-borrowed books
        scored = []
        for idx, book in enumerate(all_books):
            if book.id not in borrowed_ids:
                scored.append((book, float(similarities[idx])))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[: self._top_n]

        recommendations = [
            RecommendationItem(
                book_id=book.id,
                title=book.title,
                author=book.author,
                genre=book.genre,
                score=round(score, 4),
            )
            for book, score in top
        ]

        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
        )

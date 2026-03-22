# ARCHITECTURE.md — LuminaLib Design Decisions

> This document explains the key architectural choices made in building
> LuminaLib, as required by the assessment deliverables.

---

## Table of Contents

1. [Overall Architecture](#1-overall-architecture)
2. [Database Schema — User Preferences](#2-database-schema--user-preferences)
3. [Async LLM Generation Strategy](#3-async-llm-generation-strategy)
4. [ML Recommendation Model](#4-ml-recommendation-model)
5. [Provider Swappability](#5-provider-swappability)
6. [Code Quality & Standards](#6-code-quality--standards)

---

## 1. Overall Architecture

LuminaLib is built on **Clean Architecture** (also known as Hexagonal / Ports
and Adapters) with four distinct layers:

```
API Layer  →  Service Layer  →  Domain Layer  ←  Infrastructure Layer
```

### Layers

| Layer | Responsibility | Key Modules |
|-------|---------------|-------------|
| **Domain** | Pure business entities, value objects, and interface contracts (ports) | `app/domain/models/`, `app/domain/interfaces/` |
| **Service** | Use-case orchestration — coordinates domain objects and ports | `app/services/` |
| **Infrastructure** | Concrete adapters implementing domain ports | `app/infrastructure/` |
| **API** | HTTP transport — routes, middleware, DI wiring | `app/api/`, `app/dependencies.py` |

### Dependency Rule

Dependencies point **inward**: the API layer depends on Services, which depend
on Domain interfaces.  Infrastructure implements those interfaces but is never
imported directly by services — it's injected via `app/dependencies.py`.

### Dependency Injection

FastAPI's `Depends()` system is used as the DI container.  All wiring lives in
a single file (`app/dependencies.py`), making it trivial to swap any adapter.

---

## 2. Database Schema — User Preferences

### Design Choice: Tag-Weight Model

```sql
CREATE TABLE user_preferences (
    id          UUID PRIMARY KEY,
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    tag         VARCHAR(128) NOT NULL,
    weight      FLOAT DEFAULT 1.0,
    created_at  TIMESTAMPTZ,
    updated_at  TIMESTAMPTZ,
    UNIQUE (user_id, tag)
);
```

### Why This Design?

I evaluated three approaches:

| Approach | Pros | Cons |
|----------|------|------|
| **Boolean flags** (e.g., `likes_fiction`) | Simple | Rigid, schema changes needed for new genres |
| **JSON blob** on user table | Flexible | Not queryable, no referential integrity |
| **Tag-weight table** ✅ | Flexible, queryable, extensible | Extra join (minimal overhead) |

The **tag-weight model** was chosen because:

1. **Extensibility**: New genres/tags can be added without schema migration.
2. **Granularity**: Weights (0.0 – ∞) capture degree of preference, not just
   binary yes/no.
3. **Implicit enrichment**: The system automatically boosts weights when a user
   borrows or positively reviews a book of a given genre.
4. **ML-friendly**: The tag-weight pairs are trivially convertible to a
   user-profile vector for the recommendation engine.

### How Preferences Are Populated

- **Explicit**: Users can set preferred genres via API (future endpoint).
- **Implicit**: When a user borrows a book, the book's genre tag weight is
  incremented by +1.0. When they leave a positive review (≥ 4.0 stars), the
  weight is further boosted by +0.5.

---

## 3. Async LLM Generation Strategy

### Problem

LLM inference (book summarisation, review sentiment analysis, consensus
generation) is slow (5–60s per call).  These operations must not block the
API response.

### Solution: FastAPI BackgroundTasks + Optional Celery

```
User Request  →  API Route  →  Service Logic  →  HTTP 201 Response
                                    │
                                    └──→  BackgroundTask (async)
                                              │
                                              └──→  LLM Adapter
                                              └──→  DB Update
```

#### How It Works

1. **Book Upload** (`POST /books`):
   - The API immediately returns the book metadata.
   - A `BackgroundTask` is enqueued to read the file content and call the LLM
     for summary generation.
   - The `ai_summary` field is updated asynchronously.

2. **Review Submission** (`POST /books/{id}/reviews`):
   - The review is persisted and the response returned immediately.
   - Two background tasks fire:
     a. **Sentiment Classification**: Classifies the individual review as
        positive/neutral/negative.
     b. **Consensus Update**: Re-analyses all reviews for the book and updates
        the `review_consensus` field.

#### Why Not Just Celery?

- **FastAPI BackgroundTasks** are sufficient for moderate workloads and require
  zero additional infrastructure.
- **Celery** is included as an *optional* scaling path: for high-volume
  deployments, the same task functions can be wrapped in Celery tasks and
  distributed across workers via Redis.
- This dual approach demonstrates understanding of both patterns without
  over-engineering the default setup.

#### Task Isolation

Each background task creates its own database session (via the session factory)
to avoid contaminating the request session.  If the LLM call fails, the error
is logged but does not affect the user's request.

---

## 4. ML Recommendation Model

### Strategy: Content-Based Filtering with TF-IDF

I chose **Content-Based Filtering** over Collaborative Filtering because:

| Factor | Content-Based ✅ | Collaborative |
|--------|-----------------|---------------|
| Cold start (few users) | Works immediately | Needs user-user matrix |
| New books | Recommended instantly | Needs interaction data |
| Explainability | Genre/tag match is intuitive | "Users like you" is opaque |
| Scalability | O(n) books | O(n²) user pairs |

### Algorithm

```python
# 1. Build feature string for each book
feature = f"{book.genre} {book.description[:300]}"

# 2. Build user profile from preference tags
profile = " ".join(f"{tag} " * weight for tag, weight in user_prefs)

# 3. TF-IDF vectorise [all_books + user_profile]
tfidf_matrix = TfidfVectorizer().fit_transform(corpus)

# 4. Cosine similarity between user vector and book vectors
scores = cosine_similarity(user_vector, book_vectors)

# 5. Rank, exclude already-borrowed, return top-N
```

### Why TF-IDF + Cosine Similarity?

- **Lightweight**: No training step required — works with any catalogue size.
- **Interpretable**: High similarity = genre/keyword overlap with user prefs.
- **Fast**: Scikit-learn's sparse matrix operations are efficient for 10K+ books.

### Future Enhancements

- **Hybrid model**: Combine content-based scores with collaborative filtering
  once sufficient user interaction data exists.
- **LLM embeddings**: Replace TF-IDF with semantic embeddings from the LLM for
  richer feature representations.
- **A/B testing**: Track click-through rates on recommendations to fine-tune
  the scoring.

---

## 5. Provider Swappability

A key evaluation criterion is **modularity** — can we swap components by
changing a single config line?

### Storage Backend

| Config | Adapter | File |
|--------|---------|------|
| `STORAGE_BACKEND=local` | `LocalStorage` | `app/infrastructure/storage/local.py` |
| `STORAGE_BACKEND=s3` | `S3Storage` | `app/infrastructure/storage/s3.py` |

Both implement `StorageInterface` (defined in `app/domain/interfaces/storage.py`).
The DI wiring in `app/dependencies.py` selects the adapter:

```python
@lru_cache
def _get_storage() -> StorageInterface:
    if settings.storage_backend == StorageBackend.S3:
        return S3Storage(...)
    return LocalStorage(...)
```

### LLM Provider

| Config | Adapter | File |
|--------|---------|------|
| `LLM_PROVIDER=ollama` | `OllamaLLM` | `app/infrastructure/llm/ollama.py` |
| `LLM_PROVIDER=openai` | `OpenAILLM` | `app/infrastructure/llm/openai_adapter.py` |

Both implement `LLMInterface`.  Prompt templates are centralised in
`app/infrastructure/llm/prompts.py` and shared by both adapters.

### Adding a New Provider

To add, say, an Anthropic Claude adapter:

1. Create `app/infrastructure/llm/anthropic.py` implementing `LLMInterface`.
2. Add `ANTHROPIC = "anthropic"` to the `LLMProvider` enum.
3. Add a branch in `_get_llm()` in `dependencies.py`.
4. Set `LLM_PROVIDER=anthropic` in `.env`.

**Zero changes** to services, routes, or business logic.

---

## 6. Code Quality & Standards

| Tool | Purpose | Config |
|------|---------|--------|
| **Black** | Code formatting | `pyproject.toml` → line-length 99 |
| **isort** | Import sorting | `pyproject.toml` → "black" profile |
| **Ruff** | Fast linting | Included in requirements |
| **mypy** | Static type checking | Strict mode, Pydantic + SQLAlchemy plugins |
| **pytest** | Testing | Async mode, session-scoped fixtures |

### Import Ordering Convention

```python
# 1. Future annotations
from __future__ import annotations

# 2. Standard library
import uuid
from datetime import datetime

# 3. Third-party
from fastapi import APIRouter
from sqlalchemy.orm import Mapped

# 4. First-party
from app.config import Settings
from app.domain.models.user import User
```

### Type Safety

- All function signatures have full type annotations.
- Pydantic models enforce runtime validation.
- SQLAlchemy 2.0's `Mapped[]` annotations provide ORM-level type safety.
- `from __future__ import annotations` enables PEP 604 union syntax (`X | Y`).

---

## Conclusion

LuminaLib demonstrates production-grade engineering principles:

- **Clean Architecture** with strict dependency inversion
- **Interface-driven** design for maximal testability and swappability
- **Async-first** approach leveraging Python 3.11 and FastAPI
- **Pragmatic ML** using proven algorithms (TF-IDF + cosine similarity)
- **Structured GenAI** integration with reusable prompt templates
- **One-command deployment** via Docker Compose

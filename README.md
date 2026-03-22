# LuminaLib — Intelligent Library System

> **Stack**: Python 3.11 · FastAPI · PostgreSQL · Ollama (Llama 3) · Docker  
> **Role**: Senior Backend & GenAI Engineer — Technical Assessment

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Architecture Overview](#architecture-overview)
4. [API Endpoints](#api-endpoints)
5. [Configuration](#configuration)
6. [Running Tests](#running-tests)
7. [Swapping Providers](#swapping-providers)

---

## Quick Start

### Prerequisites

- **Docker** ≥ 24.x and **Docker Compose** ≥ 2.x
- 8 GB RAM recommended (for Ollama / Llama 3)

### One-Command Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd lumina_library

# 2. Copy and adjust environment variables
cp .env.example .env

# 3. Launch all services
docker-compose up --build
```

This single command spins up:

| Service | Container | Port |
|---------|-----------|------|
| **API** | `luminalib-api` | `8000` |
| **PostgreSQL** | `luminalib-db` | `5432` |
| **Redis** | `luminalib-redis` | `6379` |
| **Ollama (Llama 3)** | `luminalib-ollama` | `11434` |
| **Celery Worker** | `luminalib-worker` | — |

### Verify

```bash
curl http://localhost:8000/health
# → {"status":"healthy","version":"1.0.0"}
```

### Interactive API Docs

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Project Structure

```
lumina_library/
├── app/
│   ├── __init__.py
│   ├── config.py                   # Centralised settings (Pydantic)
│   ├── main.py                     # FastAPI app factory
│   ├── dependencies.py             # DI wiring — swap providers here
│   ├── domain/
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── base.py             # Declarative base, mixins
│   │   │   ├── user.py
│   │   │   ├── book.py
│   │   │   ├── borrow.py
│   │   │   ├── review.py
│   │   │   └── preference.py       # Tag-weight user preferences
│   │   ├── schemas/                # Pydantic request / response models
│   │   │   ├── auth.py
│   │   │   ├── book.py
│   │   │   ├── review.py
│   │   │   └── recommendation.py
│   │   └── interfaces/             # Abstract contracts (ports)
│   │       ├── storage.py          # StorageInterface
│   │       ├── llm.py              # LLMInterface
│   │       ├── user_repository.py
│   │       ├── book_repository.py
│   │       ├── review_repository.py
│   │       └── preference_repository.py
│   ├── infrastructure/
│   │   ├── database.py             # Async engine & session factory
│   │   ├── storage/
│   │   │   ├── local.py            # LocalStorage adapter
│   │   │   └── s3.py               # S3Storage adapter (MinIO / AWS)
│   │   ├── llm/
│   │   │   ├── prompts.py          # Structured prompt templates
│   │   │   ├── ollama.py           # OllamaLLM adapter
│   │   │   └── openai_adapter.py   # OpenAILLM adapter
│   │   └── repositories/           # SQLAlchemy repo implementations
│   ├── services/                   # Business logic layer
│   │   ├── auth_service.py
│   │   ├── book_service.py
│   │   ├── review_service.py
│   │   └── recommendation_service.py
│   ├── api/
│   │   ├── middleware/auth.py      # JWT bearer dependency
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── books.py
│   │       ├── reviews.py
│   │       └── recommendations.py
│   └── tasks/
│       ├── background.py           # Async LLM jobs
│       └── celery_app.py           # Celery config (optional)
├── alembic/                        # Database migrations
├── tests/                          # Pytest test suite
├── docker-compose.yml              # Full orchestration
├── Dockerfile                      # Multi-stage build
├── requirements.txt
├── pyproject.toml                  # Tooling config
├── .env.example
├── ARCHITECTURE.md                 # Design decisions document
└── README.md                       # ← You are here
```

---

## Architecture Overview

LuminaLib follows **Clean Architecture** / **Hexagonal Architecture** principles:

```
┌─────────────────────────────────────────────┐
│                 API Layer                    │
│  (FastAPI Routes, Middleware, Dependencies)  │
├─────────────────────────────────────────────┤
│              Service Layer                   │
│    (AuthService, BookService, ReviewService, │
│     RecommendationService)                   │
├─────────────────────────────────────────────┤
│              Domain Layer                    │
│  (Models, Schemas, Interfaces / Ports)       │
├─────────────────────────────────────────────┤
│           Infrastructure Layer               │
│  (PostgreSQL Repos, Storage Adapters,        │
│   LLM Adapters, Celery)                      │
└─────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design decisions.

---

## API Endpoints

| Domain | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| **Auth** | `POST` | `/auth/signup` | Register a new user |
| | `POST` | `/auth/login` | Return JWT access token |
| | `GET` | `/auth/profile` | Get current user profile |
| | `PUT` | `/auth/profile` | Update user profile |
| | `POST` | `/auth/signout` | Sign out (discard token) |
| **Books** | `POST` | `/books` | Upload book file & metadata (triggers async summary) |
| | `GET` | `/books` | List books with pagination |
| | `GET` | `/books/{id}` | Get single book details |
| | `PUT` | `/books/{id}` | Update book metadata |
| | `DELETE` | `/books/{id}` | Remove book and file |
| | `POST` | `/books/{id}/borrow` | Borrow a book |
| | `POST` | `/books/{id}/return` | Return a book |
| **Reviews** | `POST` | `/books/{id}/reviews` | Submit review (triggers async sentiment) |
| **Intel** | `GET` | `/books/{id}/analysis` | AI-aggregated review summary |
| | `GET` | `/recommendations` | ML-based suggestions for current user |

---

## Configuration

All settings are managed via environment variables (`.env` file).

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL connection string |
| `JWT_SECRET_KEY` | `change-me...` | Secret for JWT signing |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | Model name for Ollama |

See `.env.example` for the complete list.

---

## Running Tests

```bash
# Inside the container
docker-compose exec api pytest tests/ -v

# Or locally (with dependencies installed)
pytest tests/ -v
```

---

## Swapping Providers

### Storage: Local → S3

```env
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=luminalib-books
```

### LLM: Ollama → OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini
```

**No code changes required** — only `.env` updates and a restart.

---

## License

This project was built as a technical assessment deliverable.

"""Dependency injection wiring for FastAPI.

This module is the single place where infrastructure adapters are chosen based
on configuration.  Swapping a storage backend or LLM provider is a one-line
config change — no business-logic files need modification.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import LLMProvider, Settings, StorageBackend, get_settings
from app.domain.interfaces.book_repository import BookRepositoryInterface
from app.domain.interfaces.llm import LLMInterface
from app.domain.interfaces.preference_repository import PreferenceRepositoryInterface
from app.domain.interfaces.review_repository import ReviewRepositoryInterface
from app.domain.interfaces.storage import StorageInterface
from app.domain.interfaces.user_repository import UserRepositoryInterface
from app.infrastructure.database import build_session_factory
from app.infrastructure.llm.ollama import OllamaLLM
from app.infrastructure.llm.openai_adapter import OpenAILLM
from app.infrastructure.repositories.book_repository import BookRepository
from app.infrastructure.repositories.preference_repository import PreferenceRepository
from app.infrastructure.repositories.review_repository import ReviewRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.storage.local import LocalStorage
from app.infrastructure.storage.s3 import S3Storage
from app.services.auth_service import AuthService
from app.services.book_service import BookService
from app.services.recommendation_service import RecommendationService
from app.services.review_service import ReviewService


#Singletons (created once)
@lru_cache
def _get_settings() -> Settings:
    return get_settings()


@lru_cache
def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    return build_session_factory(_get_settings())


@lru_cache
def _get_storage() -> StorageInterface:
    settings = _get_settings()
    if settings.storage_backend == StorageBackend.S3:
        return S3Storage(
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket_name=settings.s3_bucket_name,
            region=settings.s3_region,
        )
    return LocalStorage(root_path=settings.local_storage_path)


@lru_cache
def _get_llm() -> LLMInterface:
    settings = _get_settings()
    if settings.llm_provider == LLMProvider.OPENAI:
        return OpenAILLM(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    return OllamaLLM(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )


# Request-scoped dependencies
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return _get_session_factory()


def get_storage() -> StorageInterface:
    return _get_storage()


def get_llm() -> LLMInterface:
    return _get_llm()


# Repository factories


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepositoryInterface:
    return UserRepository(session)


async def get_book_repo(
    session: AsyncSession = Depends(get_session),
) -> BookRepositoryInterface:
    return BookRepository(session)


async def get_review_repo(
    session: AsyncSession = Depends(get_session),
) -> ReviewRepositoryInterface:
    return ReviewRepository(session)


async def get_preference_repo(
    session: AsyncSession = Depends(get_session),
) -> PreferenceRepositoryInterface:
    return PreferenceRepository(session)


# Service factories


async def get_auth_service(
    user_repo: UserRepositoryInterface = Depends(get_user_repo),
    settings: Settings = Depends(_get_settings),
) -> AuthService:
    return AuthService(user_repo=user_repo, settings=settings)


async def get_book_service(
    book_repo: BookRepositoryInterface = Depends(get_book_repo),
    storage: StorageInterface = Depends(get_storage),
) -> BookService:
    return BookService(book_repo=book_repo, storage=storage)


async def get_review_service(
    review_repo: ReviewRepositoryInterface = Depends(get_review_repo),
    book_repo: BookRepositoryInterface = Depends(get_book_repo),
) -> ReviewService:
    return ReviewService(review_repo=review_repo, book_repo=book_repo)


async def get_recommendation_service(
    book_repo: BookRepositoryInterface = Depends(get_book_repo),
    pref_repo: PreferenceRepositoryInterface = Depends(get_preference_repo),
    settings: Settings = Depends(_get_settings),
) -> RecommendationService:
    return RecommendationService(
        book_repo=book_repo,
        pref_repo=pref_repo,
        top_n=settings.recommendation_top_n,
    )

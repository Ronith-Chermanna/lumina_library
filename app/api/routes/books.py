"""Book routes — CRUD, upload, borrow, return."""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
    Response,
)

from app.api.middleware.auth import get_current_user_id
from app.dependencies import (
    get_book_service,
    get_llm,
    get_session_factory,
    get_storage,
)
from app.domain.interfaces.llm import LLMInterface
from app.domain.interfaces.storage import StorageInterface
from app.domain.schemas.book import (
    BookCreateRequest,
    BookListResponse,
    BookResponse,
    BookUpdateRequest,
    BorrowResponse,
)
from app.services.book_service import BookService
from app.tasks.background import generate_book_summary

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(path="", response_model=BookResponse, status_code=status.HTTP_201_CREATED,
             summary="Upload book file & metadata. Triggers async summary.",
             )
async def create_book(
        background_tasks: BackgroundTasks,
        title: str = Form(...),
        author: str = Form(...),
        isbn: str = Form(..., min_length=10, max_length=20),
        genre: str | None = Form(default=None),
        description: str | None = Form(default=None),
        language: str = Form(default="English"),
        page_count: int | None = Form(default=None),
        file: UploadFile = File(...),
        _user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
        session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
        llm: LLMInterface = Depends(get_llm),
        storage: StorageInterface = Depends(get_storage),
) -> BookResponse:
    data = BookCreateRequest(
        title=title,
        author=author,
        isbn=isbn,
        genre=genre,
        description=description,
        language=language,
        page_count=page_count,
    )

    file_bytes: bytes | None = None
    content_type = "application/octet-stream"
    if file:
        file_bytes = await file.read()
        content_type = file.content_type or content_type

    try:
        result = await book_service.create_book(data, file_bytes, content_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    # Trigger async summary generation
    if file_bytes:
        background_tasks.add_task(
            generate_book_summary, result.id, session_factory, llm, storage
        )

    return result


@router.get(path="", response_model=BookListResponse, summary="List books (pagination required)")
async def list_books(
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        _user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
) -> BookListResponse:
    return await book_service.list_books(page=page, page_size=page_size)


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get book details",
)
async def get_book(
        book_id: uuid.UUID,
        _user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
) -> BookResponse:
    try:
        return await book_service.get_book(book_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update book details",
)
async def update_book(
        book_id: uuid.UUID,
        data: BookUpdateRequest,
        _user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
) -> BookResponse:
    try:
        return await book_service.update_book(book_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove book and associated file",
)
async def delete_book(
        book_id: uuid.UUID,
        _user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
) -> Response:
    try:
        await book_service.delete_book(book_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/{book_id}/borrow",
    response_model=BorrowResponse,
    summary="User borrows a book",
)
async def borrow_book(
        book_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
) -> BorrowResponse:
    try:
        return await book_service.borrow_book(user_id, book_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post(
    "/{book_id}/return",
    response_model=BorrowResponse,
    summary="User returns a book",
)
async def return_book(
        book_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        book_service: BookService = Depends(get_book_service),
) -> BorrowResponse:
    try:
        return await book_service.return_book(user_id, book_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

"""Celery application configuration (optional — for heavy-duty async jobs).

For lighter workloads, LuminaLib uses FastAPI's BackgroundTasks by default.
This module enables horizontal scaling via Celery workers when needed.
"""

from __future__ import annotations

import os

from celery import Celery

celery_app = Celery(
    "luminalib",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

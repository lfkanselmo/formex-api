from celery import Celery

from src.infrastructure.config import settings
from src.infrastructure.windows_event_loop import ensure_windows_selector_event_loop

ensure_windows_selector_event_loop()

celery_app = Celery(
    "formex",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.infrastructure.tasks.jobs"],
)

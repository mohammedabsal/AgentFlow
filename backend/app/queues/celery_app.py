from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "agentflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.queues.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
    task_always_eager=settings.celery_eager_mode,  # For dev without Redis
    task_eager_propagates=True,  # Propagate exceptions in eager mode
)

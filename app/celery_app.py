try:
    from celery import Celery
except ImportError:  # pragma: no cover
    class Celery:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            pass

        def task(self, *args, **kwargs):
            def decorator(func):
                func.delay = func
                return func

            return decorator

from app.settings import settings


celery_app = Celery(
    "trading_app",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

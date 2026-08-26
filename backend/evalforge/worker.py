import dramatiq
from dramatiq.brokers.redis import RedisBroker

from evalforge.config import get_settings
from evalforge.database import SessionLocal
from evalforge.services.runs import execute_run

settings = get_settings()
dramatiq.set_broker(RedisBroker(url=settings.redis_url))


@dramatiq.actor(max_retries=2, min_backoff=1000)
def execute_evaluation(run_id: str) -> None:
    with SessionLocal() as session:
        execute_run(session, run_id)

from celery import Celery
from pathlib import Path
from app.config import settings
from app.ingest import ingest
celery=Celery('research',broker=settings.redis_url,backend=settings.redis_url)
@celery.task(name='research.ingest',autoretry_for=(ConnectionError,),retry_backoff=True,retry_kwargs={'max_retries':3})
def ingest_task(path:str):return ingest(Path(path))

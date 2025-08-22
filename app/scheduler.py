import asyncio
import logging
import os
from typing import Optional
from .ingestion import ingest_all
from .database import SessionLocal

logger = logging.getLogger(__name__)

class IngestionScheduler:
    """Scheduler that runs ingestion + NLP every interval (seconds)."""

    def __init__(self, interval_seconds: Optional[int] = None):
        self.interval = int(interval_seconds or os.getenv("INGEST_INTERVAL_SECONDS", 300))  # default 300s (5m)
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def _runner(self):
        logger.info("Scheduler started; interval=%ss", self.interval)
        while not self._stop_event.is_set():
            try:
                # create a DB session and run ingest_all
                db = SessionLocal()
                try:
                    counts = ingest_all(db)
                    logger.info("Ingestion run counts: %s", counts)
                finally:
                    db.close()
            except Exception as e:
                logger.exception("Error during scheduled ingestion: %s", e)
            # wait for interval or stop event
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                continue
        logger.info("Scheduler stopped")

    def start(self):
        if self._task is None or self._task.done():
            self._stop_event.clear()
            # schedule background task in event loop
            self._task = asyncio.create_task(self._runner())

    async def stop(self):
        self._stop_event.set()
        if self._task:
            await self._task

scheduler = IngestionScheduler()

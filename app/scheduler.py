import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class IngestionScheduler:
    """Minimal async scheduler that logs every X seconds (Day-1 heartbeat)."""

    def __init__(self, interval_seconds: Optional[int] = None):
        self.interval = int(interval_seconds or os.getenv("INGEST_INTERVAL_SECONDS", 10))
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def _runner(self):
        logger.info("Scheduler started; interval=%ss", self.interval)
        while not self._stop_event.is_set():
            logger.info("ingestion job running")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
            except asyncio.TimeoutError:
                continue
        logger.info("Scheduler stopped")

    def start(self):
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._runner())

    async def stop(self):
        self._stop_event.set()
        if self._task:
            await self._task

scheduler = IngestionScheduler()

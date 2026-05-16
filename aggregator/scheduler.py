import logging
import threading
import time

import schedule

from .config import SCHEDULE_INTERVAL_MINUTES
from .pipeline import run_backfill, run_pipeline

logger = logging.getLogger(__name__)

_running = threading.Lock()


def _run_in_thread() -> None:
    """Acquire the lock and run the pipeline in a background thread.
    If a run is already in progress, wait for it to finish before starting."""
    def _worker():
        with _running:
            try:
                run_pipeline()
            except Exception as e:
                logger.error(f"Pipeline crashed — will retry next cycle: {e}", exc_info=True)
            try:
                run_backfill(batch_size=50)
            except Exception as e:
                logger.error(f"Backfill crashed: {e}", exc_info=True)

    threading.Thread(target=_worker, daemon=True).start()


def start() -> None:
    schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(_run_in_thread)
    logger.info(f"Scheduler started — pipeline runs every {SCHEDULE_INTERVAL_MINUTES} minutes")

    _run_in_thread()  # run immediately on startup

    while True:
        schedule.run_pending()
        time.sleep(30)

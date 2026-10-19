"""
Dead Man's Switch Scheduler

Runs as a separate process (or container) to periodically check for
overdue switches and advance their state through the escalation cascade.

In production, this would be a Celery beat worker or similar.
For now, it's a simple loop that runs every hour.
"""

import logging
import time

from app.database import SessionLocal
from app.services.dead_mans_switch import DeadMansSwitchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 3600  # Run every hour


def run_scheduler():
    """Main scheduler loop."""
    logger.info("Dead Man's Switch scheduler started")

    while True:
        try:
            db = SessionLocal()
            service = DeadMansSwitchService(db)
            changed = service.process_overdue_switches()

            if changed:
                logger.info(f"Processed {len(changed)} state changes")
                for switch in changed:
                    logger.info(
                        f"  Switch {switch.id}: {switch.status.value} "
                        f"(user {switch.user_id})"
                    )
            else:
                logger.debug("No overdue switches to process")

        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
        finally:
            db.close()

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_scheduler()

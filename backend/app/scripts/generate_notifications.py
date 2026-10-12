"""Generate resource and recurring-rule notifications. Idempotent."""

from __future__ import annotations

import json
import logging

from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.services.notification_service import generate_notifications

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        created = generate_notifications(db)
        payload = {"created": created}
        print(json.dumps(payload, ensure_ascii=False))
        logger.info("Notification generate complete: created=%s", created)
    finally:
        db.close()


if __name__ == "__main__":
    main()

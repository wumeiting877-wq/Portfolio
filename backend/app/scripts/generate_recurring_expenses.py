"""Generate due recurring expenses. Safe to run repeatedly."""

from __future__ import annotations

import json
import logging

from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.services.expense_service import generate_recurring_expenses

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        result = generate_recurring_expenses(db, operator_user_id=None, ip_address=None)
        print(json.dumps(result.model_dump(), ensure_ascii=False))
        logger.info(
            "Recurring generate complete: created=%s skipped=%s",
            result.generated_count,
            result.skipped_count,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

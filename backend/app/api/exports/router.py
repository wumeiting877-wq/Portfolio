from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, get_current_user
from app.services.export_service import build_export

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("/{export_type}")
def export_data(
    export_type: str,
    date_from: date | None = None,
    date_to: date | None = None,
    project_id: int | None = None,
    currency: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    content, filename = build_export(
        db,
        current_user,
        export_type,
        date_from=date_from,
        date_to=date_to,
        project_id=project_id,
        currency=currency,
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

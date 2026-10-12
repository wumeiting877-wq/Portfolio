from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import CurrentUser, require_admin
from app.schemas.enterprise import ImportCommitResponse, ImportPreviewResponse
from app.services.excel_io import (
    MAX_IMPORT_BYTES,
    build_template,
    ensure_import_type,
    validate_upload,
)
from app.services.import_service import commit_import, preview_import

router = APIRouter(prefix="/api/imports", tags=["imports"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def _read_upload(file: UploadFile) -> bytes:
    validate_upload(file.filename, None)
    content = await file.read()
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件超过 10 MB")
    validate_upload(file.filename, len(content))
    return content


@router.get("/templates/{import_type}")
def download_template(
    import_type: str,
    current_user: CurrentUser = Depends(require_admin),
) -> Response:
    ensure_import_type(import_type)
    content = build_template(import_type)
    filename = f"{import_type}_template.xlsx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{import_type}/preview", response_model=ImportPreviewResponse)
async def preview(
    import_type: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ImportPreviewResponse:
    ensure_import_type(import_type)
    content = await _read_upload(file)
    return ImportPreviewResponse.model_validate(preview_import(db, import_type, content))


@router.post("/{import_type}/commit", response_model=ImportCommitResponse)
async def commit(
    import_type: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ImportCommitResponse:
    ensure_import_type(import_type)
    content = await _read_upload(file)
    result = commit_import(
        db,
        import_type,
        content,
        current_user=current_user,
        ip_address=_client_ip(request),
    )
    if not result.get("committed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
    return ImportCommitResponse.model_validate(result)

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import CredentialStatus, CredentialType
from app.permissions.dependencies import CurrentUser, get_current_user, require_admin
from app.schemas.resource_credential import (
    ResourceCredentialCreate,
    ResourceCredentialListResponse,
    ResourceCredentialPublic,
    ResourceCredentialRotate,
    ResourceCredentialStatusUpdate,
    ResourceCredentialUpdate,
)
from app.security.credential_encryption import CredentialEncryptionService
from app.security.sensitive_validation import sanitize_request_validation_errors
from app.services.resource_credential_service import (
    create_credential,
    get_credential_encryption_service,
    get_readable_credential,
    list_credentials,
    rotate_credential,
    set_credential_status,
    update_credential,
)


class SensitiveValidationRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request):
            try:
                return await original(request)
            except RequestValidationError as exc:
                return JSONResponse(
                    status_code=422,
                    content={"detail": sanitize_request_validation_errors(exc.errors())},
                )

        return handler


router = APIRouter(
    prefix="/api/resource-credentials",
    tags=["resource-credentials"],
    route_class=SensitiveValidationRoute,
)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _public(credential) -> ResourceCredentialPublic:
    return ResourceCredentialPublic.model_validate(credential)


@router.get("", response_model=ResourceCredentialListResponse)
def get_credentials(
    resource_account_id: int | None = Query(default=None, gt=0),
    credential_type: CredentialType | None = None,
    status_filter: CredentialStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    _: CredentialEncryptionService = Depends(get_credential_encryption_service),
    db: Session = Depends(get_db),
) -> ResourceCredentialListResponse:
    items, total = list_credentials(
        db,
        current_user,
        resource_account_id=resource_account_id,
        credential_type=credential_type.value if credential_type else None,
        status_filter=status_filter.value if status_filter else None,
        page=page,
        page_size=page_size,
    )
    return ResourceCredentialListResponse(
        items=[_public(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ResourceCredentialPublic)
def post_credential(
    payload: ResourceCredentialCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    encryption: CredentialEncryptionService = Depends(get_credential_encryption_service),
    db: Session = Depends(get_db),
) -> ResourceCredentialPublic:
    return _public(
        create_credential(
            db,
            current_user,
            payload,
            encryption,
            ip_address=_client_ip(request),
        )
    )


@router.get("/{credential_id}", response_model=ResourceCredentialPublic)
def get_credential(
    credential_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    _: CredentialEncryptionService = Depends(get_credential_encryption_service),
    db: Session = Depends(get_db),
) -> ResourceCredentialPublic:
    return _public(get_readable_credential(db, current_user, credential_id))


@router.put("/{credential_id}", response_model=ResourceCredentialPublic)
def put_credential(
    credential_id: int,
    payload: ResourceCredentialUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    _: CredentialEncryptionService = Depends(get_credential_encryption_service),
    db: Session = Depends(get_db),
) -> ResourceCredentialPublic:
    return _public(
        update_credential(
            db,
            current_user,
            credential_id,
            payload,
            ip_address=_client_ip(request),
        )
    )


@router.post("/{credential_id}/rotate", response_model=ResourceCredentialPublic)
def post_rotate_credential(
    credential_id: int,
    payload: ResourceCredentialRotate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    encryption: CredentialEncryptionService = Depends(get_credential_encryption_service),
    db: Session = Depends(get_db),
) -> ResourceCredentialPublic:
    return _public(
        rotate_credential(
            db,
            current_user,
            credential_id,
            payload.secret,
            encryption,
            ip_address=_client_ip(request),
        )
    )


@router.patch("/{credential_id}/status", response_model=ResourceCredentialPublic)
def patch_credential_status(
    credential_id: int,
    payload: ResourceCredentialStatusUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    _: CredentialEncryptionService = Depends(get_credential_encryption_service),
    db: Session = Depends(get_db),
) -> ResourceCredentialPublic:
    return _public(
        set_credential_status(
            db,
            current_user,
            credential_id,
            payload.status.value,
            ip_address=_client_ip(request),
        )
    )

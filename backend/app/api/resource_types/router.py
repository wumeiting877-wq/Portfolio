from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.enums import RoleCode
from app.permissions.dependencies import CurrentUser, get_current_user, require_admin
from app.schemas.stable_identifier import IdentifierImpact
from app.schemas.resource import (
    ResourceTypeCodeChange,
    ResourceTypeCodeChangeResult,
    ResourceTypeCreate,
    ResourceTypePublic,
    ResourceTypeUpdate,
)
from app.services.stable_identifier_service import resource_type_identifier_impact
from app.services.resource_service import (
    correct_resource_type_code,
    create_resource_type,
    get_resource_type,
    list_resource_types,
    serialize_resource_type,
    set_resource_type_active,
    update_resource_type,
)

router = APIRouter(prefix="/api/resource-types", tags=["resource-types"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _require_code_correction_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != RoleCode.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限修正资源类型编码")
    return current_user


@router.get("", response_model=list[ResourceTypePublic])
def get_resource_types(
    include_inactive: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ResourceTypePublic]:
    return [
        serialize_resource_type(item)
        for item in list_resource_types(db, current_user, include_inactive=include_inactive)
    ]


@router.post("", response_model=ResourceTypePublic)
def post_resource_type(
    payload: ResourceTypeCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceTypePublic:
    resource_type = create_resource_type(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource_type(resource_type)


@router.get("/{type_id}", response_model=ResourceTypePublic)
def get_resource_type_by_id(
    type_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceTypePublic:
    _ = current_user
    return serialize_resource_type(get_resource_type(db, type_id))


@router.put("/{type_id}", response_model=ResourceTypePublic)
def put_resource_type(
    type_id: int,
    payload: ResourceTypeUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceTypePublic:
    resource_type = update_resource_type(
        db,
        type_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource_type(resource_type)


@router.get("/{type_id}/code/impact", response_model=IdentifierImpact)
def get_resource_type_code_impact(
    type_id: int,
    current_user: CurrentUser = Depends(_require_code_correction_admin),
    db: Session = Depends(get_db),
) -> IdentifierImpact:
    _ = current_user
    return resource_type_identifier_impact(db, type_id)


@router.patch("/{type_id}/code", response_model=ResourceTypeCodeChangeResult)
def patch_resource_type_code(
    type_id: int,
    payload: ResourceTypeCodeChange,
    request: Request,
    current_user: CurrentUser = Depends(_require_code_correction_admin),
    db: Session = Depends(get_db),
) -> ResourceTypeCodeChangeResult:
    resource_type, related_account_count = correct_resource_type_code(
        db,
        type_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    body = serialize_resource_type(resource_type).model_dump()
    body["related_account_count"] = related_account_count
    return ResourceTypeCodeChangeResult(**body)


@router.post("/{type_id}/disable", response_model=ResourceTypePublic)
def post_disable_resource_type(
    type_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceTypePublic:
    resource_type = set_resource_type_active(
        db,
        type_id,
        is_active=False,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource_type(resource_type)


@router.post("/{type_id}/enable", response_model=ResourceTypePublic)
def post_enable_resource_type(
    type_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceTypePublic:
    resource_type = set_resource_type_active(
        db,
        type_id,
        is_active=True,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource_type(resource_type)

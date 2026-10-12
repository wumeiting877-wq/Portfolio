from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import (
    CurrentUser,
    get_current_user,
    require_admin,
    require_admin_or_boss,
    require_stable_identifier_admin,
)
from app.schemas.stable_identifier import IdentifierImpact
from app.schemas.resource import (
    ResourceAllocationCreate,
    ResourceNameChange,
    ResourceAllocationListResponse,
    ResourceAllocationPublic,
    ResourceCreate,
    ResourceListResponse,
    ResourcePublic,
    ResourceUpdate,
)
from app.services.stable_identifier_service import resource_name_identifier_impact
from app.services.resource_service import (
    add_or_restore_allocation,
    correct_resource_name,
    create_resource,
    get_readable_resource,
    list_resource_allocations,
    list_resources,
    release_allocation,
    restore_allocation,
    search_allocations,
    serialize_allocation,
    serialize_resource,
    set_resource_active,
    update_resource,
)

router = APIRouter(prefix="/api/resources", tags=["resources"])
allocation_search_router = APIRouter(prefix="/api/resource-allocations", tags=["resource-allocations"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=ResourceListResponse)
def get_resources(
    keyword: str | None = None,
    resource_type_id: int | None = None,
    category: str | None = None,
    status: str | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    expiring_soon: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourceListResponse:
    items, total, page, page_size = list_resources(
        db,
        current_user,
        keyword=keyword,
        resource_type_id=resource_type_id,
        category=category,
        status_filter=status,
        project_id=project_id,
        employee_id=employee_id,
        expiring_soon=expiring_soon,
        page=page,
        page_size=page_size,
    )
    return ResourceListResponse(
        items=[serialize_resource(db, current_user, item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ResourcePublic)
def post_resource(
    payload: ResourceCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourcePublic:
    account = create_resource(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource(db, current_user, account)


@router.get("/{resource_id}", response_model=ResourcePublic)
def get_resource(
    resource_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResourcePublic:
    account = get_readable_resource(db, current_user, resource_id)
    return serialize_resource(db, current_user, account)


@router.put("/{resource_id}", response_model=ResourcePublic)
def put_resource(
    resource_id: int,
    payload: ResourceUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourcePublic:
    account = update_resource(
        db,
        resource_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource(db, current_user, account)


@router.get("/{resource_id}/resource-name/impact", response_model=IdentifierImpact)
def get_resource_name_impact(
    resource_id: int,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正资源名称")),
    db: Session = Depends(get_db),
) -> IdentifierImpact:
    _ = current_user
    return resource_name_identifier_impact(db, resource_id)


@router.patch("/{resource_id}/resource-name", response_model=ResourcePublic)
def patch_resource_name(
    resource_id: int,
    payload: ResourceNameChange,
    request: Request,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正资源名称")),
    db: Session = Depends(get_db),
) -> ResourcePublic:
    account = correct_resource_name(
        db,
        resource_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource(db, current_user, account)


@router.post("/{resource_id}/disable", response_model=ResourcePublic)
def post_disable_resource(
    resource_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourcePublic:
    account = set_resource_active(
        db,
        resource_id,
        enabled=False,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource(db, current_user, account)


@router.post("/{resource_id}/enable", response_model=ResourcePublic)
def post_enable_resource(
    resource_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourcePublic:
    account = set_resource_active(
        db,
        resource_id,
        enabled=True,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_resource(db, current_user, account)


@router.get("/{resource_id}/allocations", response_model=list[ResourceAllocationPublic])
def get_resource_allocations(
    resource_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ResourceAllocationPublic]:
    return [
        serialize_allocation(item)
        for item in list_resource_allocations(db, current_user, resource_id)
    ]


@router.post("/{resource_id}/allocations", response_model=ResourceAllocationPublic)
def post_resource_allocation(
    resource_id: int,
    payload: ResourceAllocationCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceAllocationPublic:
    allocation = add_or_restore_allocation(
        db,
        resource_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_allocation(allocation)


@router.delete("/{resource_id}/allocations/{allocation_id}", response_model=ResourceAllocationPublic)
def delete_resource_allocation(
    resource_id: int,
    allocation_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceAllocationPublic:
    allocation = release_allocation(
        db,
        resource_id,
        allocation_id,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_allocation(allocation)


@router.post(
    "/{resource_id}/allocations/{allocation_id}/restore",
    response_model=ResourceAllocationPublic,
)
def post_restore_resource_allocation(
    resource_id: int,
    allocation_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ResourceAllocationPublic:
    allocation = restore_allocation(
        db,
        resource_id,
        allocation_id,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_allocation(allocation)


@allocation_search_router.get("", response_model=ResourceAllocationListResponse)
def get_allocation_search(
    resource_id: int | None = None,
    project_id: int | None = None,
    employee_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> ResourceAllocationListResponse:
    items, total, page, page_size = search_allocations(
        db,
        current_user,
        resource_id=resource_id,
        project_id=project_id,
        employee_id=employee_id,
        page=page,
        page_size=page_size,
    )
    return ResourceAllocationListResponse(
        items=[serialize_allocation(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )

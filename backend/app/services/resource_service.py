from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import ResourceStatus, ResourceTypeCategory
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.models.resource_type import ResourceType
from app.permissions.dependencies import CurrentUser
from app.permissions.resource_scope import (
    can_read_allocation,
    can_read_resource,
    readable_allocations,
    readable_resources,
)
from app.repositories.project_repository import ProjectRepository
from app.repositories.resource_repository import EXPIRING_SOON_DAYS, ResourceRepository
from app.services.settings_service import business_today, get_expiring_days
from app.services.stable_identifier_service import normalize_stable_identifier, reject_same
from app.schemas.resource import (
    ResourceAllocationCreate,
    ResourceAllocationPublic,
    ResourceCreate,
    ResourceNameChange,
    ResourcePublic,
    ResourceTypeBrief,
    ResourceTypeCodeChange,
    ResourceTypeCreate,
    ResourceTypePublic,
    ResourceTypeUpdate,
    ResourceUpdate,
    ResourceUsageProject,
)
from app.services.audit_service import write_audit
from app.services.employee_service import get_employee


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_expiring_soon(
    expires_at: date | None,
    today: date | None = None,
    *,
    days: int = EXPIRING_SOON_DAYS,
) -> bool:
    if expires_at is None:
        return False
    today = today or date.today()
    delta = (expires_at - today).days
    return 0 < delta <= days


def _validate_category(value: str) -> str:
    try:
        return ResourceTypeCategory(value).value
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的资源类别") from exc


def _validate_resource_status(value: str) -> str:
    try:
        return ResourceStatus(value).value
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的资源状态") from exc


def _normalize_resource_type_code(value: str) -> str:
    """Same rule as create: strip, keep case, length matches resource_types.code."""
    text = value.strip()
    if not text or len(text) > 50:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="编码格式不合法")
    return text


def _type_snapshot(resource_type: ResourceType) -> dict:
    return {
        "id": resource_type.id,
        "code": resource_type.code,
        "name": resource_type.name,
        "category": resource_type.category,
        "description": resource_type.description,
        "is_active": resource_type.is_active,
    }


def _account_snapshot(account: ResourceAccount) -> dict:
    return {
        "id": account.id,
        "resource_type_id": account.resource_type_id,
        "resource_name": account.resource_name,
        "provider": account.provider,
        "account_identifier": account.account_identifier,
        "plan_name": account.plan_name,
        "status": account.status,
        "purchased_at": account.purchased_at.isoformat() if account.purchased_at else None,
        "activated_at": account.activated_at.isoformat() if account.activated_at else None,
        "expires_at": account.expires_at.isoformat() if account.expires_at else None,
        "remark": account.remark,
    }


def _allocation_snapshot(allocation: ResourceAllocation) -> dict:
    return {
        "id": allocation.id,
        "resource_account_id": allocation.resource_account_id,
        "project_id": allocation.project_id,
        "employee_id": allocation.employee_id,
        "is_active": allocation.is_active,
        "allocated_at": allocation.allocated_at.isoformat() if allocation.allocated_at else None,
        "released_at": allocation.released_at.isoformat() if allocation.released_at else None,
        "remark": allocation.remark,
    }


def serialize_resource_type(resource_type: ResourceType) -> ResourceTypePublic:
    return ResourceTypePublic.model_validate(resource_type)


def serialize_resource(
    db: Session,
    current_user: CurrentUser,
    account: ResourceAccount,
    *,
    stats: dict[str, int] | None = None,
    usage_projects: list[tuple[int, str, str]] | None = None,
) -> ResourcePublic:
    repo = ResourceRepository(db)
    if stats is None:
        stats = repo.active_allocation_stats([account.id]).get(
            account.id,
            {"active_count": 0, "active_user_count": 0, "active_project_count": 0},
        )
    if usage_projects is None:
        usage_map = repo.usage_projects_by_resource(
            readable_allocations(db, current_user),
            [account.id],
        )
        usage_projects = usage_map.get(account.id, [])
    resource_type = account.resource_type
    return ResourcePublic(
        id=account.id,
        resource_name=account.resource_name,
        resource_type=ResourceTypeBrief(
            id=resource_type.id,
            code=resource_type.code,
            name=resource_type.name,
            category=resource_type.category,
        ),
        provider=account.provider,
        account_identifier=account.account_identifier,
        plan_name=account.plan_name,
        status=account.status,
        purchased_at=account.purchased_at,
        activated_at=account.activated_at,
        expires_at=account.expires_at,
        remark=account.remark,
        is_expiring_soon=is_expiring_soon(
            account.expires_at,
            today=business_today(db),
            days=get_expiring_days(db),
        ),
        is_shared=stats["active_count"] > 1,
        active_user_count=stats["active_user_count"],
        active_project_count=stats["active_project_count"],
        usage_projects=[
            ResourceUsageProject(id=item[0], name=item[1], project_code=item[2])
            for item in usage_projects
        ],
        created_by=account.created_by,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def serialize_allocation(allocation: ResourceAllocation) -> ResourceAllocationPublic:
    project = allocation.project
    employee = allocation.employee
    return ResourceAllocationPublic(
        id=allocation.id,
        resource_account_id=allocation.resource_account_id,
        project_id=allocation.project_id,
        project_name=project.name if project else None,
        project_code=project.project_code if project else None,
        employee_id=allocation.employee_id,
        employee_name=employee.name if employee else None,
        employee_no=employee.employee_no if employee else None,
        allocated_at=allocation.allocated_at,
        released_at=allocation.released_at,
        is_active=allocation.is_active,
        remark=allocation.remark,
        created_by=allocation.created_by,
        created_at=allocation.created_at,
        updated_at=allocation.updated_at,
    )


def list_resource_types(db: Session, current_user: CurrentUser, *, include_inactive: bool = False) -> list[ResourceType]:
    show_inactive = include_inactive and current_user.role == "ADMIN"
    return ResourceRepository(db).list_types(include_inactive=show_inactive)


def get_resource_type(db: Session, type_id: int) -> ResourceType:
    resource_type = ResourceRepository(db).get_type_by_id(type_id)
    if resource_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源类型不存在")
    return resource_type


def create_resource_type(
    db: Session,
    payload: ResourceTypeCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceType:
    repo = ResourceRepository(db)
    if repo.get_type_by_code(payload.code.strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源类型编码已存在")
    resource_type = ResourceType(
        code=payload.code.strip(),
        name=payload.name.strip(),
        category=_validate_category(payload.category),
        description=payload.description,
        is_active=True,
    )
    repo.add_type(resource_type)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_TYPE_CREATE",
        module="resources",
        target_type="resource_type",
        target_id=resource_type.id,
        after_data=_type_snapshot(resource_type),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(resource_type)
    return resource_type


def update_resource_type(
    db: Session,
    type_id: int,
    payload: ResourceTypeUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceType:
    resource_type = get_resource_type(db, type_id)
    before = _type_snapshot(resource_type)
    data = payload.model_dump(exclude_unset=True)
    data.pop("code", None)
    if "name" in data and data["name"] is not None:
        resource_type.name = data["name"].strip()
    if "category" in data and data["category"] is not None:
        resource_type.category = _validate_category(data["category"])
    if "description" in data:
        resource_type.description = data["description"]
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_TYPE_UPDATE",
        module="resources",
        target_type="resource_type",
        target_id=resource_type.id,
        before_data=before,
        after_data=_type_snapshot(resource_type),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(resource_type)
    return resource_type


def correct_resource_type_code(
    db: Session,
    type_id: int,
    payload: ResourceTypeCodeChange,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> tuple[ResourceType, int]:
    repo = ResourceRepository(db)
    resource_type = get_resource_type(db, type_id)
    new_code = _normalize_resource_type_code(payload.new_code)
    if new_code == resource_type.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新编码与当前编码一致")
    taken = repo.get_type_by_code(new_code)
    if taken is not None and taken.id != resource_type.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源类型编码已存在")

    related_account_count = repo.count_accounts_for_type(resource_type.id)
    previous_code = resource_type.code
    resource_type.code = new_code
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_TYPE_CODE_CHANGE",
        module="resources",
        target_type="resource_type",
        target_id=resource_type.id,
        before_data={"code": previous_code},
        after_data={"code": new_code},
        ip_address=ip_address,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint = str(getattr(exc, "orig", exc))
        if "ix_resource_types_code" in constraint or "resource_types_code_key" in constraint:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源类型编码已存在") from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源类型编码修正失败") from exc
    db.refresh(resource_type)
    return resource_type, related_account_count


def set_resource_type_active(
    db: Session,
    type_id: int,
    *,
    is_active: bool,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceType:
    resource_type = get_resource_type(db, type_id)
    before = _type_snapshot(resource_type)
    resource_type.is_active = is_active
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_TYPE_ENABLE" if is_active else "RESOURCE_TYPE_DISABLE",
        module="resources",
        target_type="resource_type",
        target_id=resource_type.id,
        before_data=before,
        after_data=_type_snapshot(resource_type),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(resource_type)
    return resource_type


def _require_usable_type(db: Session, type_id: int) -> ResourceType:
    resource_type = ResourceRepository(db).get_type_by_id(type_id)
    if resource_type is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的资源类型")
    if not resource_type.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源类型已停用")
    return resource_type


def list_resources(
    db: Session,
    current_user: CurrentUser,
    *,
    keyword: str | None,
    resource_type_id: int | None,
    category: str | None,
    status_filter: str | None,
    project_id: int | None,
    employee_id: int | None,
    expiring_soon: bool,
    page: int,
    page_size: int,
) -> tuple[list[ResourceAccount], int, int, int]:
    repo = ResourceRepository(db)
    query = readable_resources(db, current_user)
    query = repo.list_accounts_filtered(
        query,
        keyword=keyword,
        resource_type_id=resource_type_id,
        category=category,
        status=status_filter,
        project_id=project_id,
        employee_id=employee_id,
        expiring_soon=expiring_soon,
        today=business_today(db),
        days=get_expiring_days(db),
    )
    items, total = repo.paginate_accounts(query, page=page, page_size=page_size)
    return items, total, page, page_size


def get_readable_resource(db: Session, current_user: CurrentUser, resource_id: int) -> ResourceAccount:
    if not can_read_resource(db, current_user, resource_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    account = ResourceRepository(db).get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return account


def _require_unique_resource_name(
    db: Session,
    resource_name: str,
    *,
    exclude_id: int | None = None,
) -> str:
    cleaned = resource_name.strip()
    existing = ResourceRepository(db).get_account_by_name(cleaned)
    if existing is not None and existing.id != exclude_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源名称已存在")
    return cleaned


def _commit_resource(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "uq_resource_accounts_resource_name" in str(getattr(exc, "orig", exc)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资源名称已存在") from exc
        raise


def create_resource(
    db: Session,
    payload: ResourceCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAccount:
    resource_type = _require_usable_type(db, payload.resource_type_id)
    resource_name = _require_unique_resource_name(db, payload.resource_name)
    account = ResourceAccount(
        resource_type_id=resource_type.id,
        resource_name=resource_name,
        provider=payload.provider,
        account_identifier=payload.account_identifier,
        plan_name=payload.plan_name,
        status=_validate_resource_status(payload.status),
        purchased_at=payload.purchased_at,
        activated_at=payload.activated_at,
        expires_at=payload.expires_at,
        remark=payload.remark,
        created_by=operator_user_id,
    )
    ResourceRepository(db).add_account(account)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_CREATE",
        module="resources",
        target_type="resource_account",
        target_id=account.id,
        after_data=_account_snapshot(account),
        ip_address=ip_address,
    )
    _commit_resource(db)
    db.refresh(account)
    return ResourceRepository(db).get_account_by_id(account.id) or account


def update_resource(
    db: Session,
    resource_id: int,
    payload: ResourceUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAccount:
    repo = ResourceRepository(db)
    account = repo.get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    before = _account_snapshot(account)
    data = payload.model_dump(exclude_unset=True)
    data.pop("resource_name", None)
    if "resource_type_id" in data and data["resource_type_id"] is not None:
        resource_type = _require_usable_type(db, data["resource_type_id"])
        account.resource_type_id = resource_type.id
    for field in ("provider", "account_identifier", "plan_name", "remark", "purchased_at", "activated_at", "expires_at"):
        if field in data:
            setattr(account, field, data[field])
    if "status" in data and data["status"] is not None:
        account.status = _validate_resource_status(data["status"])
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_UPDATE",
        module="resources",
        target_type="resource_account",
        target_id=account.id,
        before_data=before,
        after_data=_account_snapshot(account),
        ip_address=ip_address,
    )
    _commit_resource(db)
    db.refresh(account)
    return repo.get_account_by_id(account.id) or account


def correct_resource_name(
    db: Session,
    resource_id: int,
    payload: ResourceNameChange,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAccount:
    repo = ResourceRepository(db)
    account = repo.get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    new_value = normalize_stable_identifier(
        payload.new_resource_name,
        max_length=200,
        invalid_detail="资源名称格式不合法",
    )
    reject_same(new_value, account.resource_name, "新资源名称与当前资源名称一致")
    previous = account.resource_name
    account.resource_name = _require_unique_resource_name(db, new_value, exclude_id=account.id)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_NAME_CHANGE",
        module="resources",
        target_type="resource_account",
        target_id=account.id,
        before_data={"resource_name": previous},
        after_data={"resource_name": new_value},
        ip_address=ip_address,
    )
    _commit_resource(db)
    db.refresh(account)
    return repo.get_account_by_id(account.id) or account


def set_resource_active(
    db: Session,
    resource_id: int,
    *,
    enabled: bool,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAccount:
    repo = ResourceRepository(db)
    account = repo.get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    before = _account_snapshot(account)
    account.status = ResourceStatus.ACTIVE.value if enabled else ResourceStatus.DISABLED.value
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_ENABLE" if enabled else "RESOURCE_DISABLE",
        module="resources",
        target_type="resource_account",
        target_id=account.id,
        before_data=before,
        after_data=_account_snapshot(account),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(account)
    return repo.get_account_by_id(account.id) or account


def _require_project_member(db: Session, project_id: int, employee_id: int) -> None:
    member = ProjectRepository(db).get_member(project_id, employee_id)
    if member is None or not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该成员不属于此项目",
        )


def _validate_allocation_targets(db: Session, project_id: int | None, employee_id: int | None) -> None:
    if project_id is None and employee_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目与成员至少选择一项")
    if project_id is not None:
        project = ProjectRepository(db).get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if employee_id is not None:
        get_employee(db, employee_id)
    if project_id is not None and employee_id is not None:
        _require_project_member(db, project_id, employee_id)


def list_resource_allocations(
    db: Session,
    current_user: CurrentUser,
    resource_id: int,
) -> list[ResourceAllocation]:
    get_readable_resource(db, current_user, resource_id)
    return ResourceRepository(db).list_allocations(
        readable_allocations(db, current_user, resource_id=resource_id)
    )


def search_allocations(
    db: Session,
    current_user: CurrentUser,
    *,
    resource_id: int | None,
    project_id: int | None,
    employee_id: int | None,
    page: int,
    page_size: int,
) -> tuple[list[ResourceAllocation], int, int, int]:
    repo = ResourceRepository(db)
    query = readable_allocations(db, current_user, resource_id=resource_id)
    if project_id is not None:
        query = query.filter(ResourceAllocation.project_id == project_id)
    if employee_id is not None:
        query = query.filter(ResourceAllocation.employee_id == employee_id)
    items, total = repo.paginate_allocations(query, page=page, page_size=page_size)
    return items, total, page, page_size


def add_or_restore_allocation(
    db: Session,
    resource_id: int,
    payload: ResourceAllocationCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAllocation:
    repo = ResourceRepository(db)
    account = repo.get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    _validate_allocation_targets(db, payload.project_id, payload.employee_id)
    existing = repo.find_allocation(resource_id, payload.project_id, payload.employee_id)
    allocated_at = payload.allocated_at or _now()
    if existing and existing.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该分配关系已存在")
    if existing:
        before = _allocation_snapshot(existing)
        existing.is_active = True
        existing.allocated_at = allocated_at
        existing.released_at = None
        if payload.remark is not None:
            existing.remark = payload.remark
        write_audit(
            db,
            operator_user_id=operator_user_id,
            action="RESOURCE_ALLOCATION_RESTORE",
            module="resources",
            target_type="resource_allocation",
            target_id=existing.id,
            before_data=before,
            after_data=_allocation_snapshot(existing),
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(existing)
        return repo.get_allocation_by_id(existing.id) or existing

    allocation = ResourceAllocation(
        resource_account_id=resource_id,
        project_id=payload.project_id,
        employee_id=payload.employee_id,
        allocated_at=allocated_at,
        is_active=True,
        remark=payload.remark,
        created_by=operator_user_id,
    )
    repo.add_allocation(allocation)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_ALLOCATION_ADD",
        module="resources",
        target_type="resource_allocation",
        target_id=allocation.id,
        after_data=_allocation_snapshot(allocation),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(allocation)
    return repo.get_allocation_by_id(allocation.id) or allocation


def release_allocation(
    db: Session,
    resource_id: int,
    allocation_id: int,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAllocation:
    repo = ResourceRepository(db)
    account = repo.get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    allocation = repo.get_allocation_by_id(allocation_id)
    if allocation is None or allocation.resource_account_id != resource_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分配记录不存在")
    if not allocation.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分配已释放")
    before = _allocation_snapshot(allocation)
    allocation.is_active = False
    allocation.released_at = _now()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_ALLOCATION_RELEASE",
        module="resources",
        target_type="resource_allocation",
        target_id=allocation.id,
        before_data=before,
        after_data=_allocation_snapshot(allocation),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(allocation)
    return repo.get_allocation_by_id(allocation.id) or allocation


def restore_allocation(
    db: Session,
    resource_id: int,
    allocation_id: int,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ResourceAllocation:
    repo = ResourceRepository(db)
    account = repo.get_account_by_id(resource_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    allocation = repo.get_allocation_by_id(allocation_id)
    if allocation is None or allocation.resource_account_id != resource_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分配记录不存在")
    if allocation.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分配已是使用中")
    _validate_allocation_targets(db, allocation.project_id, allocation.employee_id)
    before = _allocation_snapshot(allocation)
    allocation.is_active = True
    allocation.allocated_at = _now()
    allocation.released_at = None
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="RESOURCE_ALLOCATION_RESTORE",
        module="resources",
        target_type="resource_allocation",
        target_id=allocation.id,
        before_data=before,
        after_data=_allocation_snapshot(allocation),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(allocation)
    return repo.get_allocation_by_id(allocation.id) or allocation


def get_readable_allocation(
    db: Session, current_user: CurrentUser, allocation_id: int
) -> ResourceAllocation:
    if not can_read_allocation(db, current_user, allocation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分配记录不存在")
    allocation = ResourceRepository(db).get_allocation_by_id(allocation_id)
    if allocation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="分配记录不存在")
    return allocation

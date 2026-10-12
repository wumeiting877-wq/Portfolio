from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import (
    CurrentUser,
    get_current_user,
    require_admin,
    require_stable_identifier_admin,
)
from app.schemas.stable_identifier import IdentifierImpact
from app.schemas.project import (
    ProjectCodeChange,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberPublic,
    ProjectMemberUpdate,
    ProjectPublic,
    ProjectUpdate,
)
from app.services.stable_identifier_service import project_identifier_impact
from app.services.project_service import (
    add_or_restore_member,
    archive_project,
    correct_project_code,
    create_project,
    get_readable_project,
    list_project_members,
    list_projects,
    remove_member,
    serialize_member,
    serialize_project,
    update_member,
    update_project,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=ProjectListResponse)
def get_projects(
    keyword: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    items, total, page, page_size = list_projects(
        db,
        current_user,
        keyword=keyword,
        status_filter=status,
        page=page,
        page_size=page_size,
    )
    return ProjectListResponse(
        items=[serialize_project(db, item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProjectPublic)
def post_project(
    payload: ProjectCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProjectPublic:
    project = create_project(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_project(db, project)


@router.get("/{project_id}", response_model=ProjectPublic)
def get_project(
    project_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectPublic:
    project = get_readable_project(db, current_user, project_id)
    return serialize_project(db, project)


@router.put("/{project_id}", response_model=ProjectPublic)
def put_project(
    project_id: int,
    payload: ProjectUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProjectPublic:
    project = update_project(
        db,
        project_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_project(db, project)


@router.get("/{project_id}/project-code/impact", response_model=IdentifierImpact)
def get_project_code_impact(
    project_id: int,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正项目编码")),
    db: Session = Depends(get_db),
) -> IdentifierImpact:
    _ = current_user
    return project_identifier_impact(db, project_id)


@router.patch("/{project_id}/project-code", response_model=ProjectPublic)
def patch_project_code(
    project_id: int,
    payload: ProjectCodeChange,
    request: Request,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正项目编码")),
    db: Session = Depends(get_db),
) -> ProjectPublic:
    project = correct_project_code(
        db,
        project_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_project(db, project)


@router.post("/{project_id}/archive", response_model=ProjectPublic)
def post_archive_project(
    project_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProjectPublic:
    project = archive_project(
        db,
        project_id,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_project(db, project)


@router.get("/{project_id}/members", response_model=list[ProjectMemberPublic])
def get_project_members(
    project_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProjectMemberPublic]:
    return [serialize_member(item) for item in list_project_members(db, current_user, project_id)]


@router.post("/{project_id}/members", response_model=ProjectMemberPublic)
def post_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProjectMemberPublic:
    member = add_or_restore_member(
        db,
        project_id,
        payload.employee_id,
        payload.member_role,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_member(member)


@router.put("/{project_id}/members/{employee_id}", response_model=ProjectMemberPublic)
def put_project_member(
    project_id: int,
    employee_id: int,
    payload: ProjectMemberUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProjectMemberPublic:
    member = update_member(
        db,
        project_id,
        employee_id,
        payload.member_role,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_member(member)


@router.delete("/{project_id}/members/{employee_id}", response_model=ProjectMemberPublic)
def delete_project_member(
    project_id: int,
    employee_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ProjectMemberPublic:
    member = remove_member(
        db,
        project_id,
        employee_id,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_member(member)

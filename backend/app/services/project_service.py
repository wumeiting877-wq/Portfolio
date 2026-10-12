from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.enums import EmploymentStatus, ProjectMemberRole, ProjectStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.permissions.dependencies import CurrentUser
from app.permissions.project_scope import can_read_project, readable_projects
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    ProjectCodeChange,
    ProjectCreate,
    ProjectMemberPublic,
    ProjectPublic,
    ProjectUpdate,
)
from app.services.audit_service import write_audit
from app.services.stable_identifier_service import (
    commit_stable_identifier,
    normalize_stable_identifier,
    reject_same,
    reject_taken,
)
from app.services.employee_service import get_employee

WRITABLE_STATUSES = {
    ProjectStatus.PLANNING.value,
    ProjectStatus.ACTIVE.value,
    ProjectStatus.PAUSED.value,
    ProjectStatus.COMPLETED.value,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_status(value: str, *, allow_archived: bool = False) -> str:
    try:
        status_value = ProjectStatus(value).value
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的项目状态") from exc
    if not allow_archived and status_value == ProjectStatus.ARCHIVED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请使用归档接口")
    if not allow_archived and status_value not in WRITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的项目状态")
    return status_value


def _validate_dates(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="结束日期不能早于开始日期")


def _require_active_employee(db: Session, employee_id: int) -> Employee:
    employee = get_employee(db, employee_id)
    if employee.employment_status != EmploymentStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人必须是在职人员")
    return employee


def _validate_member_role(value: str | None) -> str:
    role = value or ProjectMemberRole.MEMBER.value
    try:
        return ProjectMemberRole(role).value
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的成员角色") from exc


def _project_snapshot(project: Project) -> dict:
    return {
        "id": project.id,
        "project_code": project.project_code,
        "name": project.name,
        "description": project.description,
        "manager_employee_id": project.manager_employee_id,
        "status": project.status,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
    }


def _member_snapshot(member: ProjectMember) -> dict:
    return {
        "id": member.id,
        "project_id": member.project_id,
        "employee_id": member.employee_id,
        "member_role": member.member_role,
        "is_active": member.is_active,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "left_at": member.left_at.isoformat() if member.left_at else None,
    }


def serialize_project(db: Session, project: Project) -> ProjectPublic:
    repo = ProjectRepository(db)
    manager = project.manager
    return ProjectPublic(
        id=project.id,
        project_code=project.project_code,
        name=project.name,
        description=project.description,
        manager_employee_id=project.manager_employee_id,
        manager_name=manager.name if manager else None,
        manager_employee_no=manager.employee_no if manager else None,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        member_count=repo.active_member_count(project.id),
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def serialize_member(member: ProjectMember) -> ProjectMemberPublic:
    employee = member.employee
    return ProjectMemberPublic(
        id=member.id,
        project_id=member.project_id,
        employee_id=member.employee_id,
        employee_no=employee.employee_no if employee else None,
        name=employee.name if employee else None,
        department=employee.department if employee else None,
        position=employee.position if employee else None,
        member_role=member.member_role,
        joined_at=member.joined_at,
        left_at=member.left_at,
        is_active=member.is_active,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def _ensure_manager_membership(
    repo: ProjectRepository,
    project: Project,
    manager_employee_id: int,
) -> tuple[ProjectMember, str]:
    member = repo.get_member(project.id, manager_employee_id)
    now = _now()
    if member is None:
        member = repo.add_member(
            ProjectMember(
                project_id=project.id,
                employee_id=manager_employee_id,
                member_role=ProjectMemberRole.PROJECT_MANAGER.value,
                is_active=True,
                joined_at=now,
                left_at=None,
            )
        )
        return member, "add"
    if not member.is_active:
        member.is_active = True
        member.joined_at = now
        member.left_at = None
        member.member_role = ProjectMemberRole.PROJECT_MANAGER.value
        repo.db.add(member)
        repo.db.flush()
        return member, "restore"
    if member.member_role != ProjectMemberRole.PROJECT_MANAGER.value:
        member.member_role = ProjectMemberRole.PROJECT_MANAGER.value
        repo.db.add(member)
        repo.db.flush()
    return member, "exists"


def get_readable_project(db: Session, current_user: CurrentUser, project_id: int) -> Project:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None or not can_read_project(db, current_user, project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    return project


def list_projects(
    db: Session,
    current_user: CurrentUser,
    *,
    keyword: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Project], int, int, int]:
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="页码无效")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分页大小无效")
    if status_filter:
        try:
            ProjectStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的项目状态") from exc

    repo = ProjectRepository(db)
    query = repo.list_filtered(
        readable_projects(db, current_user),
        keyword=keyword,
        status=status_filter,
    )
    items, total = repo.paginate(query, page=page, page_size=page_size)
    return items, total, page, page_size


def create_project(
    db: Session,
    payload: ProjectCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Project:
    repo = ProjectRepository(db)
    if repo.get_by_code(payload.project_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目编码已存在")
    _require_active_employee(db, payload.manager_employee_id)
    status_value = _validate_status(payload.status)
    _validate_dates(payload.start_date, payload.end_date)

    project = repo.add(
        Project(
            project_code=payload.project_code,
            name=payload.name,
            description=payload.description,
            manager_employee_id=payload.manager_employee_id,
            status=status_value,
            start_date=payload.start_date,
            end_date=payload.end_date,
            created_by=operator_user_id,
        )
    )
    member, member_action = _ensure_manager_membership(repo, project, payload.manager_employee_id)
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_CREATE",
        module="projects",
        target_type="project",
        target_id=project.id,
        after_data=_project_snapshot(project),
        ip_address=ip_address,
    )
    if member_action == "add":
        write_audit(
            db,
            operator_user_id=operator_user_id,
            action="PROJECT_MEMBER_ADD",
            module="projects",
            target_type="project_member",
            target_id=member.id,
            after_data=_member_snapshot(member),
            ip_address=ip_address,
        )
    db.commit()
    db.refresh(project)
    return repo.get_by_id(project.id) or project


def update_project(
    db: Session,
    project_id: int,
    payload: ProjectUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Project:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    before = _project_snapshot(project)
    data = payload.model_dump(exclude_unset=True)
    data.pop("project_code", None)
    old_manager_id = project.manager_employee_id
    manager_changed = False

    if "status" in data and data["status"] is not None:
        data["status"] = _validate_status(data["status"])
    if "manager_employee_id" in data and data["manager_employee_id"] is not None:
        _require_active_employee(db, data["manager_employee_id"])
        manager_changed = data["manager_employee_id"] != old_manager_id

    start_date = data["start_date"] if "start_date" in data else project.start_date
    end_date = data["end_date"] if "end_date" in data else project.end_date
    _validate_dates(start_date, end_date)

    for key, value in data.items():
        setattr(project, key, value)
    db.add(project)
    db.flush()

    if manager_changed:
        if old_manager_id != project.manager_employee_id:
            previous = repo.get_member(project.id, old_manager_id)
            if previous and previous.is_active:
                previous.member_role = ProjectMemberRole.MEMBER.value
                db.add(previous)
        member, member_action = _ensure_manager_membership(
            repo, project, project.manager_employee_id
        )
        write_audit(
            db,
            operator_user_id=operator_user_id,
            action="PROJECT_MANAGER_CHANGE",
            module="projects",
            target_type="project",
            target_id=project.id,
            before_data={"manager_employee_id": old_manager_id},
            after_data={"manager_employee_id": project.manager_employee_id},
            ip_address=ip_address,
        )
        if member_action == "add":
            write_audit(
                db,
                operator_user_id=operator_user_id,
                action="PROJECT_MEMBER_ADD",
                module="projects",
                target_type="project_member",
                target_id=member.id,
                after_data=_member_snapshot(member),
                ip_address=ip_address,
            )
        elif member_action == "restore":
            write_audit(
                db,
                operator_user_id=operator_user_id,
                action="PROJECT_MEMBER_RESTORE",
                module="projects",
                target_type="project_member",
                target_id=member.id,
                after_data=_member_snapshot(member),
                ip_address=ip_address,
            )

    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_UPDATE",
        module="projects",
        target_type="project",
        target_id=project.id,
        before_data=before,
        after_data=_project_snapshot(project),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(project)
    return repo.get_by_id(project.id) or project


def correct_project_code(
    db: Session,
    project_id: int,
    payload: ProjectCodeChange,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Project:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    new_value = normalize_stable_identifier(
        payload.new_project_code,
        max_length=50,
        invalid_detail="项目编码格式不合法",
    )
    reject_same(new_value, project.project_code, "新项目编码与当前项目编码一致")
    taken = repo.get_by_code(new_value)
    reject_taken(taken.id if taken else None, project.id, "项目编码已存在")
    previous = project.project_code
    project.project_code = new_value
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_CODE_CHANGE",
        module="projects",
        target_type="project",
        target_id=project.id,
        before_data={"project_code": previous},
        after_data={"project_code": new_value},
        ip_address=ip_address,
    )
    commit_stable_identifier(
        db,
        constraint_names=("ix_projects_project_code", "projects_project_code_key"),
        duplicate_detail="项目编码已存在",
        failure_detail="项目编码修正失败",
    )
    db.refresh(project)
    return repo.get_by_id(project.id) or project


def archive_project(
    db: Session,
    project_id: int,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Project:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    before = _project_snapshot(project)
    project.status = ProjectStatus.ARCHIVED.value
    db.add(project)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_ARCHIVE",
        module="projects",
        target_type="project",
        target_id=project.id,
        before_data=before,
        after_data=_project_snapshot(project),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(project)
    return repo.get_by_id(project.id) or project


def list_project_members(db: Session, current_user: CurrentUser, project_id: int) -> list[ProjectMember]:
    get_readable_project(db, current_user, project_id)
    return ProjectRepository(db).list_members(project_id)


def add_or_restore_member(
    db: Session,
    project_id: int,
    employee_id: int,
    member_role: str | None,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ProjectMember:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    employee = get_employee(db, employee_id)
    if employee.employment_status != EmploymentStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成员必须是在职人员")
    role = _validate_member_role(member_role)
    if role == ProjectMemberRole.PROJECT_MANAGER.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人请通过修改项目设置")

    existing = repo.get_member(project_id, employee_id)
    if existing and existing.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该成员已在项目中")

    now = _now()
    if existing:
        before = _member_snapshot(existing)
        existing.is_active = True
        existing.joined_at = now
        existing.left_at = None
        existing.member_role = role
        db.add(existing)
        db.flush()
        write_audit(
            db,
            operator_user_id=operator_user_id,
            action="PROJECT_MEMBER_RESTORE",
            module="projects",
            target_type="project_member",
            target_id=existing.id,
            before_data=before,
            after_data=_member_snapshot(existing),
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(existing)
        return repo.get_member(project_id, employee_id) or existing

    member = repo.add_member(
        ProjectMember(
            project_id=project_id,
            employee_id=employee_id,
            member_role=role,
            is_active=True,
            joined_at=now,
            left_at=None,
        )
    )
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_MEMBER_ADD",
        module="projects",
        target_type="project_member",
        target_id=member.id,
        after_data=_member_snapshot(member),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(member)
    return repo.get_member(project_id, employee_id) or member


def update_member(
    db: Session,
    project_id: int,
    employee_id: int,
    member_role: str | None,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ProjectMember:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    member = repo.get_member(project_id, employee_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目成员不存在")
    if employee_id == project.manager_employee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请通过修改项目变更负责人")
    if not member.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="成员已移除")
    if member_role is None:
        return member
    role = _validate_member_role(member_role)
    if role == ProjectMemberRole.PROJECT_MANAGER.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="负责人请通过修改项目设置")
    before = _member_snapshot(member)
    member.member_role = role
    db.add(member)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_UPDATE",
        module="projects",
        target_type="project_member",
        target_id=member.id,
        before_data=before,
        after_data=_member_snapshot(member),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(member)
    return repo.get_member(project_id, employee_id) or member


def remove_member(
    db: Session,
    project_id: int,
    employee_id: int,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> ProjectMember:
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    if employee_id == project.manager_employee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除项目负责人，请先变更负责人")
    member = repo.get_member(project_id, employee_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目成员不存在")
    if not member.is_active:
        return member
    before = _member_snapshot(member)
    member.is_active = False
    member.left_at = _now()
    db.add(member)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="PROJECT_MEMBER_REMOVE",
        module="projects",
        target_type="project_member",
        target_id=member.id,
        before_data=before,
        after_data=_member_snapshot(member),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(member)
    return repo.get_member(project_id, employee_id) or member

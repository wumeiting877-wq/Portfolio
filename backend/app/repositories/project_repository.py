from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.models.project import Project
from app.models.project_member import ProjectMember


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, project_id: int) -> Project | None:
        return (
            self.db.query(Project)
            .options(joinedload(Project.manager), joinedload(Project.members))
            .filter(Project.id == project_id)
            .first()
        )

    def get_by_code(self, project_code: str) -> Project | None:
        return self.db.query(Project).filter(Project.project_code == project_code).first()

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def list_filtered(self, query: Query, *, keyword: str | None, status: str | None) -> Query:
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(Project.name.ilike(like), Project.project_code.ilike(like)))
        if status:
            query = query.filter(Project.status == status)
        return query

    def paginate(self, query: Query, *, page: int, page_size: int) -> tuple[list[Project], int]:
        total = query.order_by(None).count()
        items = (
            query.options(joinedload(Project.manager))
            .order_by(Project.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def active_member_count(self, project_id: int) -> int:
        return (
            self.db.query(func.count(ProjectMember.id))
            .filter(ProjectMember.project_id == project_id, ProjectMember.is_active.is_(True))
            .scalar()
            or 0
        )

    def get_member(self, project_id: int, employee_id: int) -> ProjectMember | None:
        return (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.employee))
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.employee_id == employee_id,
            )
            .first()
        )

    def list_members(self, project_id: int) -> list[ProjectMember]:
        return (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.employee))
            .filter(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.id.asc())
            .all()
        )

    def add_member(self, member: ProjectMember) -> ProjectMember:
        self.db.add(member)
        self.db.flush()
        return member

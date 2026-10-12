from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.role import Role
from app.permissions.dependencies import CurrentUser, require_admin
from app.schemas.user import RolePublic

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=list[RolePublic])
def get_roles(
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Role]:
    _ = current_user
    return db.query(Role).order_by(Role.id.asc()).all()

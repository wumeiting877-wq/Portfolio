from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.permissions.dependencies import (
    CurrentUser,
    require_admin,
    require_admin_or_boss,
    require_stable_identifier_admin,
)
from app.schemas.employee import EmployeeCreate, EmployeeNoChange, EmployeePublic, EmployeeUpdate
from app.schemas.stable_identifier import IdentifierImpact
from app.services.employee_service import (
    correct_employee_no,
    create_employee,
    disable_employee,
    get_employee,
    list_employees,
    serialize_employee,
    update_employee,
)
from app.services.stable_identifier_service import employee_identifier_impact

router = APIRouter(prefix="/api/employees", tags=["employees"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[EmployeePublic])
def get_employees(
    q: str | None = None,
    employment_status: str | None = None,
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> list[EmployeePublic]:
    _ = current_user
    return [serialize_employee(item) for item in list_employees(db, q=q, employment_status=employment_status)]


@router.post("", response_model=EmployeePublic)
def post_employee(
    payload: EmployeeCreate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EmployeePublic:
    employee = create_employee(
        db,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_employee(employee)


@router.get("/{employee_id}", response_model=EmployeePublic)
def get_employee_by_id(
    employee_id: int,
    current_user: CurrentUser = Depends(require_admin_or_boss),
    db: Session = Depends(get_db),
) -> EmployeePublic:
    _ = current_user
    return serialize_employee(get_employee(db, employee_id))


@router.put("/{employee_id}", response_model=EmployeePublic)
def put_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EmployeePublic:
    employee = update_employee(
        db,
        employee_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_employee(employee)


@router.get("/{employee_id}/employee-no/impact", response_model=IdentifierImpact)
def get_employee_no_impact(
    employee_id: int,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正工号")),
    db: Session = Depends(get_db),
) -> IdentifierImpact:
    _ = current_user
    return employee_identifier_impact(db, employee_id)


@router.patch("/{employee_id}/employee-no", response_model=EmployeePublic)
def patch_employee_no(
    employee_id: int,
    payload: EmployeeNoChange,
    request: Request,
    current_user: CurrentUser = Depends(require_stable_identifier_admin("无权限修正工号")),
    db: Session = Depends(get_db),
) -> EmployeePublic:
    employee = correct_employee_no(
        db,
        employee_id,
        payload,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_employee(employee)


@router.delete("/{employee_id}", response_model=EmployeePublic)
def delete_employee(
    employee_id: int,
    request: Request,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EmployeePublic:
    employee = disable_employee(
        db,
        employee_id,
        operator_user_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return serialize_employee(employee)

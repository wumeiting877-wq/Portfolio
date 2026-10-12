from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.employee import Employee
from app.models.enums import EmploymentStatus
from app.schemas.employee import EmployeeCreate, EmployeeNoChange, EmployeePublic, EmployeeUpdate
from app.services.audit_service import write_audit
from app.services.stable_identifier_service import (
    commit_stable_identifier,
    normalize_stable_identifier,
    reject_same,
    reject_taken,
)


def _to_public(employee: Employee) -> EmployeePublic:
    data = EmployeePublic.model_validate(employee)
    return data.model_copy(update={"has_account": employee.user is not None})


def _snapshot(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "employee_no": employee.employee_no,
        "name": employee.name,
        "department": employee.department,
        "position": employee.position,
        "email": employee.email,
        "phone": employee.phone,
        "employment_status": employee.employment_status,
        "remark": employee.remark,
    }


def list_employees(
    db: Session,
    *,
    q: str | None = None,
    employment_status: str | None = None,
) -> list[Employee]:
    query = db.query(Employee).options(joinedload(Employee.user))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Employee.name.ilike(like), Employee.employee_no.ilike(like)))
    if employment_status:
        query = query.filter(Employee.employment_status == employment_status)
    return query.order_by(Employee.id.asc()).all()


def get_employee(db: Session, employee_id: int) -> Employee:
    employee = (
        db.query(Employee)
        .options(joinedload(Employee.user))
        .filter(Employee.id == employee_id)
        .first()
    )
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="人员不存在")
    return employee


def create_employee(
    db: Session,
    payload: EmployeeCreate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Employee:
    exists = db.query(Employee).filter(Employee.employee_no == payload.employee_no).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="工号已存在")
    employee = Employee(
        employee_no=payload.employee_no,
        name=payload.name,
        department=payload.department,
        position=payload.position,
        email=payload.email,
        phone=payload.phone,
        remark=payload.remark,
        employment_status=EmploymentStatus.ACTIVE.value,
    )
    db.add(employee)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="create_employee",
        module="employees",
        target_type="employee",
        target_id=employee.id,
        after_data=_snapshot(employee),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(
    db: Session,
    employee_id: int,
    payload: EmployeeUpdate,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Employee:
    employee = get_employee(db, employee_id)
    before = _snapshot(employee)
    data = payload.model_dump(exclude_unset=True)
    data.pop("employee_no", None)
    if "employment_status" in data and data["employment_status"] is not None:
        try:
            EmploymentStatus(data["employment_status"])
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无效的人员状态"
            ) from exc
    for key, value in data.items():
        setattr(employee, key, value)
    db.add(employee)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="update_employee",
        module="employees",
        target_type="employee",
        target_id=employee.id,
        before_data=before,
        after_data=_snapshot(employee),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(employee)
    return employee


def correct_employee_no(
    db: Session,
    employee_id: int,
    payload: EmployeeNoChange,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Employee:
    employee = get_employee(db, employee_id)
    new_value = normalize_stable_identifier(
        payload.new_employee_no,
        max_length=50,
        invalid_detail="工号格式不合法",
    )
    reject_same(new_value, employee.employee_no, "新工号与当前工号一致")
    taken = db.query(Employee).filter(Employee.employee_no == new_value).first()
    reject_taken(taken.id if taken else None, employee.id, "工号已存在")
    previous = employee.employee_no
    employee.employee_no = new_value
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="EMPLOYEE_NO_CHANGE",
        module="employees",
        target_type="employee",
        target_id=employee.id,
        before_data={"employee_no": previous},
        after_data={"employee_no": new_value},
        ip_address=ip_address,
    )
    commit_stable_identifier(
        db,
        constraint_names=("ix_employees_employee_no", "employees_employee_no_key"),
        duplicate_detail="工号已存在",
        failure_detail="工号修正失败",
    )
    db.refresh(employee)
    return employee


def disable_employee(
    db: Session,
    employee_id: int,
    *,
    operator_user_id: int,
    ip_address: str | None,
) -> Employee:
    employee = get_employee(db, employee_id)
    before = _snapshot(employee)
    employee.employment_status = EmploymentStatus.INACTIVE.value
    db.add(employee)
    db.flush()
    write_audit(
        db,
        operator_user_id=operator_user_id,
        action="disable_employee",
        module="employees",
        target_type="employee",
        target_id=employee.id,
        before_data=before,
        after_data=_snapshot(employee),
        ip_address=ip_address,
    )
    db.commit()
    db.refresh(employee)
    return employee


def serialize_employee(employee: Employee) -> EmployeePublic:
    return _to_public(employee)

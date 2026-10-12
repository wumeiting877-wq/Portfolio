"""Shared rules for stable business identifiers.

Uniqueness is enforced here and by the existing unique indexes. This module
does not create aliases and does not rewrite foreign keys.
"""

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.expense_distribution import ExpenseDistribution
from app.models.expense_record import ExpenseRecord
from app.models.expense_type import ExpenseType
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.recurring_expense_rule import RecurringExpenseRule
from app.models.recurring_rule_distribution import RecurringRuleDistribution
from app.models.resource_account import ResourceAccount
from app.models.resource_allocation import ResourceAllocation
from app.models.resource_type import ResourceType
from app.models.user import User
from app.schemas.stable_identifier import IdentifierImpact, ImpactItem


def normalize_stable_identifier(value: str, *, max_length: int, invalid_detail: str) -> str:
    text = value.strip()
    if not text or len(text) > max_length:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=invalid_detail)
    return text


def reject_same(new_value: str, current_value: str, detail: str) -> None:
    if new_value == current_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def reject_taken(existing_id: int | None, current_id: int, detail: str) -> None:
    if existing_id is not None and existing_id != current_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def commit_stable_identifier(
    db: Session,
    *,
    constraint_names: tuple[str, ...],
    duplicate_detail: str,
    failure_detail: str,
) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        constraint = str(getattr(exc, "orig", exc))
        if any(name in constraint for name in constraint_names):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=duplicate_detail) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=failure_detail) from exc


def _require(db: Session, model: type, entity_id: int, detail: str):
    row = db.query(model).filter(model.id == entity_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return row


def _count(query) -> int:
    return int(query.scalar() or 0)


def _impact(*pairs: tuple[str, int]) -> IdentifierImpact:
    return IdentifierImpact(items=[ImpactItem(label=label, count=count) for label, count in pairs])


def employee_identifier_impact(db: Session, employee_id: int) -> IdentifierImpact:
    _require(db, Employee, employee_id, "人员不存在")
    return _impact(
        (
            "负责项目",
            _count(db.query(func.count(Project.id)).filter(Project.manager_employee_id == employee_id)),
        ),
        (
            "项目成员",
            _count(db.query(func.count(ProjectMember.id)).filter(ProjectMember.employee_id == employee_id)),
        ),
        (
            "资源分配",
            _count(
                db.query(func.count(ResourceAllocation.id)).filter(ResourceAllocation.employee_id == employee_id)
            ),
        ),
        (
            "费用归属",
            _count(
                db.query(func.count(ExpenseDistribution.id)).filter(ExpenseDistribution.employee_id == employee_id)
            ),
        ),
        (
            "系统账号",
            _count(db.query(func.count(User.id)).filter(User.employee_id == employee_id)),
        ),
    )


def project_identifier_impact(db: Session, project_id: int) -> IdentifierImpact:
    _require(db, Project, project_id, "项目不存在")
    return _impact(
        (
            "项目成员",
            _count(db.query(func.count(ProjectMember.id)).filter(ProjectMember.project_id == project_id)),
        ),
        (
            "资源分配",
            _count(db.query(func.count(ResourceAllocation.id)).filter(ResourceAllocation.project_id == project_id)),
        ),
        (
            "费用归属",
            _count(db.query(func.count(ExpenseDistribution.id)).filter(ExpenseDistribution.project_id == project_id)),
        ),
        (
            "周期规则",
            _count(
                db.query(func.count(func.distinct(RecurringRuleDistribution.rule_id))).filter(
                    RecurringRuleDistribution.project_id == project_id
                )
            ),
        ),
    )


def resource_type_identifier_impact(db: Session, type_id: int) -> IdentifierImpact:
    _require(db, ResourceType, type_id, "资源类型不存在")
    return _impact(
        (
            "关联资源",
            _count(db.query(func.count(ResourceAccount.id)).filter(ResourceAccount.resource_type_id == type_id)),
        )
    )


def expense_type_identifier_impact(db: Session, type_id: int) -> IdentifierImpact:
    _require(db, ExpenseType, type_id, "费用类型不存在")
    return _impact(
        (
            "费用记录",
            _count(db.query(func.count(ExpenseRecord.id)).filter(ExpenseRecord.expense_type_id == type_id)),
        ),
        (
            "周期规则",
            _count(
                db.query(func.count(RecurringExpenseRule.id)).filter(RecurringExpenseRule.expense_type_id == type_id)
            ),
        ),
    )


def username_identifier_impact(db: Session, user_id: int) -> IdentifierImpact:
    user = _require(db, User, user_id, "账号不存在")
    return _impact(("关联人员", 1 if user.employee_id is not None else 0))


def resource_name_identifier_impact(db: Session, resource_id: int) -> IdentifierImpact:
    _require(db, ResourceAccount, resource_id, "资源不存在")
    allocation_filter = ResourceAllocation.resource_account_id == resource_id
    return _impact(
        (
            "资源分配",
            _count(db.query(func.count(ResourceAllocation.id)).filter(allocation_filter)),
        ),
        (
            "关联项目",
            _count(
                db.query(func.count(func.distinct(ResourceAllocation.project_id))).filter(
                    allocation_filter,
                    ResourceAllocation.project_id.isnot(None),
                )
            ),
        ),
        (
            "关联人员",
            _count(
                db.query(func.count(func.distinct(ResourceAllocation.employee_id))).filter(
                    allocation_filter,
                    ResourceAllocation.employee_id.isnot(None),
                )
            ),
        ),
        (
            "费用引用",
            _count(db.query(func.count(ExpenseRecord.id)).filter(ExpenseRecord.resource_account_id == resource_id)),
        ),
        (
            "周期规则",
            _count(
                db.query(func.count(RecurringExpenseRule.id)).filter(
                    RecurringExpenseRule.resource_account_id == resource_id
                )
            ),
        ),
    )

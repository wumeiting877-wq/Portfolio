"""Identify Gate verification data. Default is dry-run; never auto-delete."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.models.employee import Employee
from app.models.expense_record import ExpenseRecord
from app.models.project import Project
from app.models.resource_account import ResourceAccount

logger = logging.getLogger(__name__)

BOOTSTRAP_EMPLOYEE_NOS = {"ADMIN001", "BOSS001", "PM001", "MB001"}
BOOTSTRAP_USERNAMES = {"admin", "boss", "pm", "member"}
GATE_PREFIX = re.compile(r"^(GATE[1-5]-|gate[1-5]-)", re.IGNORECASE)


def _is_gate_text(value: str | None) -> bool:
    if not value:
        return False
    return bool(GATE_PREFIX.search(value.strip()))


def identify(db: Session) -> dict:
    employees = db.query(Employee).all()
    projects = db.query(Project).all()
    resources = db.query(ResourceAccount).all()
    expenses = db.query(ExpenseRecord).all()

    candidate_employees = [
        {"id": item.id, "employee_no": item.employee_no, "name": item.name}
        for item in employees
        if item.employee_no not in BOOTSTRAP_EMPLOYEE_NOS
        and (_is_gate_text(item.employee_no) or _is_gate_text(item.name) or _is_gate_text(item.remark))
    ]
    candidate_projects = [
        {"id": item.id, "project_code": item.project_code, "name": item.name}
        for item in projects
        if _is_gate_text(item.project_code) or _is_gate_text(item.name) or _is_gate_text(item.description)
    ]
    candidate_resources = [
        {"id": item.id, "resource_name": item.resource_name}
        for item in resources
        if _is_gate_text(item.resource_name) or _is_gate_text(item.remark)
    ]
    candidate_expenses = [
        {"id": item.id, "description": item.description, "amount": str(item.amount), "currency": item.currency}
        for item in expenses
        if _is_gate_text(item.description) or _is_gate_text(item.external_reference)
    ]
    return {
        "database": settings.POSTGRES_DB,
        "dry_run": True,
        "keep": {
            "bootstrap_employee_nos": sorted(BOOTSTRAP_EMPLOYEE_NOS),
            "bootstrap_usernames": sorted(BOOTSTRAP_USERNAMES),
        },
        "candidates": {
            "employees": candidate_employees,
            "projects": candidate_projects,
            "resources": candidate_resources,
            "expenses": candidate_expenses,
        },
        "counts": {
            "employees_total": len(employees),
            "employees_candidate": len(candidate_employees),
            "projects_total": len(projects),
            "projects_candidate": len(candidate_projects),
            "resources_total": len(resources),
            "resources_candidate": len(candidate_resources),
            "expenses_total": len(expenses),
            "expenses_candidate": len(candidate_expenses),
        },
        "delete_order_if_executed": [
            "expense_distributions of candidate expenses",
            "expense_records",
            "resource_allocations of candidate resources",
            "resource_accounts",
            "project_members of candidate projects",
            "projects",
            "employees without login account and not bootstrap",
        ],
        "note": "Candidates are prefix-based guesses. Do not DELETE by prefix alone without review.",
    }


def execute_cleanup(db: Session, database_name: str) -> dict:
    if database_name != settings.POSTGRES_DB:
        raise SystemExit(
            f"Refusing cleanup: --database-name {database_name!r} != connected {settings.POSTGRES_DB!r}"
        )
    if "test" in (settings.POSTGRES_DB or "").lower() and database_name != settings.POSTGRES_DB:
        raise SystemExit("Refusing cleanup against mismatched database")
    report = identify(db)
    expense_ids = [item["id"] for item in report["candidates"]["expenses"]]
    resource_ids = [item["id"] for item in report["candidates"]["resources"]]
    project_ids = [item["id"] for item in report["candidates"]["projects"]]
    employee_ids = [item["id"] for item in report["candidates"]["employees"]]
    if expense_ids:
        db.execute(
            text("DELETE FROM expense_distributions WHERE expense_record_id = ANY(:ids)"),
            {"ids": expense_ids},
        )
        db.execute(text("DELETE FROM expense_records WHERE id = ANY(:ids)"), {"ids": expense_ids})
    if resource_ids:
        db.execute(
            text("DELETE FROM resource_allocations WHERE resource_account_id = ANY(:ids)"),
            {"ids": resource_ids},
        )
        db.execute(text("DELETE FROM resource_accounts WHERE id = ANY(:ids)"), {"ids": resource_ids})
    if project_ids:
        db.execute(text("DELETE FROM project_members WHERE project_id = ANY(:ids)"), {"ids": project_ids})
        db.execute(text("DELETE FROM projects WHERE id = ANY(:ids)"), {"ids": project_ids})
    if employee_ids:
        # never delete employees that still have a user account
        db.execute(
            text(
                """
                DELETE FROM employees
                WHERE id = ANY(:ids)
                  AND id NOT IN (SELECT employee_id FROM users WHERE employee_id IS NOT NULL)
                """
            ),
            {"ids": employee_ids},
        )
    db.commit()
    report["dry_run"] = False
    report["executed"] = True
    return report


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Cleanup candidate Gate verification data")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--execute", action="store_true", default=False)
    parser.add_argument("--database-name", default=os.environ.get("POSTGRES_DB", settings.POSTGRES_DB))
    args = parser.parse_args()
    if args.execute and args.dry_run:
        raise SystemExit("Use either --dry-run or --execute")
    execute = args.execute
    db = SessionLocal()
    try:
        if execute:
            report = execute_cleanup(db, args.database_name)
        else:
            report = identify(db)
            report["dry_run"] = True
        print(json.dumps(report, ensure_ascii=False, indent=2))
        logger.info(
            "cleanup_dev_data dry_run=%s db=%s candidates=%s",
            report.get("dry_run"),
            report.get("database"),
            report.get("counts"),
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

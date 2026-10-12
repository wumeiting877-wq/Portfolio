from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.database import engine
from tests.helpers import (
    admin_headers,
    create_employee,
    create_expense_type,
    create_project,
    create_resource,
    create_resource_type,
    unique,
)


def _detail(response) -> str:
    body = response.json()
    detail = body.get("detail")
    return detail if isinstance(detail, str) else ""


def test_employee_empty_employee_no_is_422(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.post(
        "/api/employees",
        json={"employee_no": "", "name": "校验人员"},
        headers=headers,
    )
    assert response.status_code == 422


def test_employee_empty_name_is_422(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.post(
        "/api/employees",
        json={"employee_no": unique("E"), "name": ""},
        headers=headers,
    )
    assert response.status_code == 422


def test_employee_invalid_email_is_422(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.post(
        "/api/employees",
        json={"employee_no": unique("E"), "name": "校验人员", "email": "not-an-email"},
        headers=headers,
    )
    assert response.status_code == 422

    created = create_employee(client, headers, email=None)
    updated = client.put(
        f"/api/employees/{created['id']}",
        json={"email": "bad@"},
        headers=headers,
    )
    assert updated.status_code == 422


def test_employee_blank_email_is_allowed(client: TestClient) -> None:
    headers = admin_headers(client)
    omitted = client.post(
        "/api/employees",
        json={"employee_no": unique("E"), "name": "无邮箱"},
        headers=headers,
    )
    assert omitted.status_code == 200, omitted.text
    assert omitted.json()["email"] is None

    blank = client.post(
        "/api/employees",
        json={"employee_no": unique("E"), "name": "空邮箱", "email": "   "},
        headers=headers,
    )
    assert blank.status_code == 200, blank.text
    assert blank.json()["email"] is None


def test_employee_duplicate_employee_no_is_400(client: TestClient) -> None:
    headers = admin_headers(client)
    employee_no = unique("E")
    create_employee(client, headers, employee_no=employee_no, email=None)
    response = client.post(
        "/api/employees",
        json={"employee_no": employee_no, "name": "重复工号"},
        headers=headers,
    )
    assert response.status_code == 400
    assert _detail(response) == "工号已存在"


def test_employee_valid_minimal_passes(client: TestClient) -> None:
    headers = admin_headers(client)
    employee_no = unique("E")
    response = client.post(
        "/api/employees",
        json={"employee_no": employee_no, "name": "最小人员", "email": "valid.user@example.com"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["employee_no"] == employee_no
    assert body["name"] == "最小人员"
    assert body["email"] == "valid.user@example.com"


def test_project_duplicate_code_inactive_manager_and_dates(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    project_code = unique("P")
    created = client.post(
        "/api/projects",
        json={"project_code": project_code, "name": "有效项目", "manager_employee_id": manager["id"]},
        headers=headers,
    )
    assert created.status_code == 200, created.text

    duplicate = client.post(
        "/api/projects",
        json={"project_code": project_code, "name": "重复编码", "manager_employee_id": manager["id"]},
        headers=headers,
    )
    assert duplicate.status_code == 400
    assert _detail(duplicate) == "项目编码已存在"

    inactive = create_employee(client, headers)
    disabled = client.delete(f"/api/employees/{inactive['id']}", headers=headers)
    assert disabled.status_code == 200
    inactive_manager = client.post(
        "/api/projects",
        json={
            "project_code": unique("P"),
            "name": "停用负责人",
            "manager_employee_id": inactive["id"],
        },
        headers=headers,
    )
    assert inactive_manager.status_code == 400
    assert _detail(inactive_manager) == "负责人必须是在职人员"

    bad_dates = client.post(
        "/api/projects",
        json={
            "project_code": unique("P"),
            "name": "日期颠倒",
            "manager_employee_id": manager["id"],
            "start_date": "2026-09-10",
            "end_date": "2026-09-01",
        },
        headers=headers,
    )
    assert bad_dates.status_code == 400
    assert _detail(bad_dates) == "结束日期不能早于开始日期"


def test_resource_name_rules_and_unique_index(client: TestClient) -> None:
    headers = admin_headers(client)
    resource_type = create_resource_type(client, headers)
    empty_name = client.post(
        "/api/resources",
        json={"resource_type_id": resource_type["id"], "resource_name": ""},
        headers=headers,
    )
    assert empty_name.status_code == 422
    blank_name = client.post(
        "/api/resources",
        json={"resource_type_id": resource_type["id"], "resource_name": "   "},
        headers=headers,
    )
    assert blank_name.status_code == 422

    empty_type = client.post(
        "/api/resources",
        json={"resource_name": unique("资源")},
        headers=headers,
    )
    assert empty_type.status_code == 422

    name = unique("资源")
    created = create_resource(
        client, headers, resource_type_id=resource_type["id"], resource_name=name
    )
    assert created["resource_name"] == name

    duplicate = client.post(
        "/api/resources",
        json={"resource_type_id": resource_type["id"], "resource_name": name},
        headers=headers,
    )
    assert duplicate.status_code == 400
    assert _detail(duplicate) == "资源名称已存在"

    other = create_resource(client, headers, resource_type_id=resource_type["id"])
    renamed = client.put(
        f"/api/resources/{other['id']}",
        json={"resource_name": name},
        headers=headers,
    )
    assert renamed.status_code == 422
    assert client.get(f"/api/resources/{other['id']}", headers=headers).json()["resource_name"] == other["resource_name"]

    kept = client.put(
        f"/api/resources/{created['id']}",
        json={"remark": "同名保留"},
        headers=headers,
    )
    assert kept.status_code == 200, kept.text
    assert kept.json()["resource_name"] == name
    assert kept.json()["remark"] == "同名保留"

    indexes = {item["name"]: item for item in inspect(engine).get_indexes("resource_accounts")}
    assert indexes["uq_resource_accounts_resource_name"]["unique"] is True
    assert "ix_resource_accounts_resource_name" not in indexes


def test_allocation_target_rules(client: TestClient) -> None:
    headers = admin_headers(client)
    manager = create_employee(client, headers)
    member = create_employee(client, headers)
    outsider = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"])
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member["id"]},
        headers=headers,
    )
    resource = create_resource(client, headers)

    both_empty = client.post(
        f"/api/resources/{resource['id']}/allocations",
        json={},
        headers=headers,
    )
    assert both_empty.status_code == 400
    assert _detail(both_empty) == "项目与成员至少选择一项"

    non_member = client.post(
        f"/api/resources/{resource['id']}/allocations",
        json={"project_id": project["id"], "employee_id": outsider["id"]},
        headers=headers,
    )
    assert non_member.status_code == 400
    assert _detail(non_member) == "该成员不属于此项目"

    project_only = client.post(
        f"/api/resources/{resource['id']}/allocations",
        json={"project_id": project["id"]},
        headers=headers,
    )
    assert project_only.status_code == 200, project_only.text
    assert project_only.json()["employee_id"] is None

    employee_only = client.post(
        f"/api/resources/{resource['id']}/allocations",
        json={"employee_id": member["id"]},
        headers=headers,
    )
    assert employee_only.status_code == 200, employee_only.text
    assert employee_only.json()["project_id"] is None

    both = client.post(
        f"/api/resources/{resource['id']}/allocations",
        json={"project_id": project["id"], "employee_id": member["id"]},
        headers=headers,
    )
    assert both.status_code == 200, both.text
    assert both.json()["project_id"] == project["id"]
    assert both.json()["employee_id"] == member["id"]


def _expense_payload(expense_type_id: int, **overrides) -> dict:
    payload = {
        "expense_type_id": expense_type_id,
        "billing_mode": "MANUAL",
        "source": "MANUAL",
        "expense_date": "2026-09-23",
        "amount": "12.50",
        "currency": "CNY",
        "distributions": [],
    }
    payload.update(overrides)
    return payload


def test_expense_validation_rules(client: TestClient) -> None:
    headers = admin_headers(client)
    required = client.post("/api/expenses", json={}, headers=headers)
    assert required.status_code == 422

    expense_type = create_expense_type(client, headers)
    manager = create_employee(client, headers)
    member = create_employee(client, headers)
    outsider = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"])
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member["id"]},
        headers=headers,
    )

    negative = client.post(
        "/api/expenses",
        json=_expense_payload(
            expense_type["id"],
            amount="-1.00",
            distributions=[
                {
                    "project_id": project["id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "-1.00",
                }
            ],
        ),
        headers=headers,
    )
    assert negative.status_code == 400
    assert _detail(negative) == "金额不能为负数"

    no_attribution = client.post(
        "/api/expenses",
        json=_expense_payload(expense_type["id"]),
        headers=headers,
    )
    assert no_attribution.status_code == 400
    assert _detail(no_attribution) == "至少需要一条费用归属"

    non_member = client.post(
        "/api/expenses",
        json=_expense_payload(
            expense_type["id"],
            distributions=[
                {
                    "project_id": project["id"],
                    "employee_id": outsider["id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "12.50",
                }
            ],
        ),
        headers=headers,
    )
    assert non_member.status_code == 400
    assert _detail(non_member) == "该成员不属于此项目"

    valid = client.post(
        "/api/expenses",
        json=_expense_payload(
            expense_type["id"],
            distributions=[
                {
                    "project_id": project["id"],
                    "employee_id": member["id"],
                    "allocation_method": "DIRECT",
                    "allocated_amount": "12.50",
                }
            ],
        ),
        headers=headers,
    )
    assert valid.status_code == 200, valid.text
    assert valid.json()["amount"] in {"12.5000", "12.50"}
    assert valid.json()["currency"] == "CNY"

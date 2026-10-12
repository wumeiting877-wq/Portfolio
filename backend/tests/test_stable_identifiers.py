from io import BytesIO
from types import SimpleNamespace

from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import text

from app.core.database import engine
from app.services.import_service import HANDLERS
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_allocation,
    create_employee,
    create_expense,
    create_expense_type,
    create_project,
    create_recurring_rule,
    create_resource,
    create_resource_type,
    create_user_account,
    login,
    unique,
)

KINDS = ("employee", "project", "resource_type", "expense_type", "user", "resource")


def _detail(response) -> str:
    body = response.json()
    detail = body.get("detail")
    return detail if isinstance(detail, str) else ""


def _xlsx(headers: list[str], rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _preview(client: TestClient, headers: dict[str, str], import_type: str, columns: list[str], row: list[object]):
    return client.post(
        f"/api/imports/{import_type}/preview",
        headers=headers,
        files={
            "file": (
                f"{import_type}.xlsx",
                _xlsx(columns, [row]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )


def _role_headers(client: TestClient, admin: dict[str, str], role_code: str) -> dict[str, str]:
    employee = create_employee(client, admin)
    _, username, password = create_user_account(
        client, admin, role_code=role_code, employee_id=employee["id"]
    )
    return auth_headers_for(client, username, password)


def _prepare(client: TestClient, headers: dict[str, str], kind: str) -> SimpleNamespace:
    if kind == "employee":
        first = create_employee(client, headers)
        second = create_employee(client, headers)
        return SimpleNamespace(
            id=first["id"],
            value=first["employee_no"],
            other=second["employee_no"],
            patch=f"/api/employees/{first['id']}/employee-no",
            impact=f"/api/employees/{first['id']}/employee-no/impact",
            missing="/api/employees/99999999/employee-no",
            read=f"/api/employees/{first['id']}",
            update=f"/api/employees/{first['id']}",
            update_body={"name": "普通编辑"},
            locked_body={"name": "绕过", "employee_no": unique("HACK")},
            body_key="new_employee_no",
            field="employee_no",
            audit="EMPLOYEE_NO_CHANGE",
            duplicate_detail="工号已存在",
            same_detail="新工号与当前工号一致",
            invalid_detail="工号格式不合法",
            forbidden_detail="无权限修正工号",
            missing_detail="人员不存在",
            too_long="N" * 51,
            new_value=unique("ENO"),
        )
    if kind == "project":
        first = create_project(client, headers)
        second = create_project(client, headers)
        return SimpleNamespace(
            id=first["id"],
            value=first["project_code"],
            other=second["project_code"],
            patch=f"/api/projects/{first['id']}/project-code",
            impact=f"/api/projects/{first['id']}/project-code/impact",
            missing="/api/projects/99999999/project-code",
            read=f"/api/projects/{first['id']}",
            update=f"/api/projects/{first['id']}",
            update_body={"name": "普通编辑"},
            locked_body={"name": "绕过", "project_code": unique("HACK")},
            body_key="new_project_code",
            field="project_code",
            audit="PROJECT_CODE_CHANGE",
            duplicate_detail="项目编码已存在",
            same_detail="新项目编码与当前项目编码一致",
            invalid_detail="项目编码格式不合法",
            forbidden_detail="无权限修正项目编码",
            missing_detail="项目不存在",
            too_long="P" * 51,
            new_value=unique("PCD"),
        )
    if kind == "resource_type":
        first = create_resource_type(client, headers)
        second = create_resource_type(client, headers)
        return SimpleNamespace(
            id=first["id"],
            value=first["code"],
            other=second["code"],
            patch=f"/api/resource-types/{first['id']}/code",
            impact=f"/api/resource-types/{first['id']}/code/impact",
            missing="/api/resource-types/99999999/code",
            read=f"/api/resource-types/{first['id']}",
            update=f"/api/resource-types/{first['id']}",
            update_body={"name": "普通编辑"},
            locked_body={"name": "绕过", "code": unique("HACK").upper()},
            body_key="new_code",
            field="code",
            audit="RESOURCE_TYPE_CODE_CHANGE",
            duplicate_detail="资源类型编码已存在",
            same_detail="新编码与当前编码一致",
            invalid_detail="编码格式不合法",
            forbidden_detail="无权限修正资源类型编码",
            missing_detail="资源类型不存在",
            too_long="C" * 51,
            new_value=unique("RTC").upper(),
        )
    if kind == "expense_type":
        first = create_expense_type(client, headers)
        second = create_expense_type(client, headers)
        return SimpleNamespace(
            id=first["id"],
            value=first["code"],
            other=second["code"],
            patch=f"/api/expense-types/{first['id']}/code",
            impact=f"/api/expense-types/{first['id']}/code/impact",
            missing="/api/expense-types/99999999/code",
            read=f"/api/expense-types/{first['id']}",
            update=f"/api/expense-types/{first['id']}",
            update_body={"name": "普通编辑"},
            locked_body={"name": "绕过", "code": unique("HACK").upper()},
            body_key="new_code",
            field="code",
            audit="EXPENSE_TYPE_CODE_CHANGE",
            duplicate_detail="费用类型编码已存在",
            same_detail="新编码与当前编码一致",
            invalid_detail="编码格式不合法",
            forbidden_detail="无权限修正费用类型编码",
            missing_detail="费用类型不存在",
            too_long="E" * 51,
            new_value=unique("ETC").upper(),
        )
    if kind == "user":
        employee = create_employee(client, headers)
        other_employee = create_employee(client, headers)
        first, username, _password = create_user_account(
            client, headers, role_code="MEMBER", employee_id=employee["id"]
        )
        _second, other_name, _other_password = create_user_account(
            client, headers, role_code="MEMBER", employee_id=other_employee["id"]
        )
        return SimpleNamespace(
            id=first["id"],
            value=username,
            other=other_name,
            patch=f"/api/users/{first['id']}/username",
            impact=f"/api/users/{first['id']}/username/impact",
            missing="/api/users/99999999/username",
            read=f"/api/users/{first['id']}",
            update=f"/api/users/{first['id']}",
            update_body={"status": "ACTIVE"},
            locked_body={"status": "ACTIVE", "username": unique("hack")},
            body_key="new_username",
            field="username",
            audit="USERNAME_CHANGE",
            duplicate_detail="用户名已存在",
            same_detail="新用户名与当前用户名一致",
            invalid_detail="用户名格式不合法",
            forbidden_detail="无权限修正用户名",
            missing_detail="账号不存在",
            too_long="U" * 81,
            new_value=unique("usr"),
        )
    resource_type = create_resource_type(client, headers)
    first = create_resource(client, headers, resource_type_id=resource_type["id"])
    second = create_resource(client, headers, resource_type_id=resource_type["id"])
    return SimpleNamespace(
        id=first["id"],
        value=first["resource_name"],
        other=second["resource_name"],
        patch=f"/api/resources/{first['id']}/resource-name",
        impact=f"/api/resources/{first['id']}/resource-name/impact",
        missing="/api/resources/99999999/resource-name",
        read=f"/api/resources/{first['id']}",
        update=f"/api/resources/{first['id']}",
        update_body={"remark": "普通编辑"},
        locked_body={"remark": "绕过", "resource_name": unique("HACK")},
        body_key="new_resource_name",
        field="resource_name",
        audit="RESOURCE_NAME_CHANGE",
        duplicate_detail="资源名称已存在",
        same_detail="新资源名称与当前资源名称一致",
        invalid_detail="资源名称格式不合法",
        forbidden_detail="无权限修正资源名称",
        missing_detail="资源不存在",
        too_long="R" * 201,
        new_value=unique("资源名"),
    )


def _audit_row(target_id: int, action: str):
    with engine.connect() as connection:
        return connection.execute(
            text(
                """
                SELECT action, before_data, after_data, operator_user_id
                FROM audit_logs
                WHERE target_id = :target_id AND action = :action
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"target_id": str(target_id), "action": action},
        ).one()


def test_username_is_not_an_import_match_key() -> None:
    assert "users" not in HANDLERS


def test_stable_identifier_guards(client: TestClient) -> None:
    headers = admin_headers(client)
    for kind in KINDS:
        spec = _prepare(client, headers, kind)
        updated = client.put(spec.update, json=spec.update_body, headers=headers)
        assert updated.status_code == 200, updated.text
        assert updated.json()[spec.field] == spec.value

        locked = client.put(spec.update, json=spec.locked_body, headers=headers)
        assert locked.status_code == 422, locked.text
        current = client.get(spec.read, headers=headers)
        assert current.status_code == 200, current.text
        assert current.json()[spec.field] == spec.value

        for role_code in ("BOSS", "PROJECT_MANAGER", "MEMBER"):
            role_headers = _role_headers(client, headers, role_code)
            forbidden = client.patch(
                spec.patch,
                json={spec.body_key: spec.new_value},
                headers=role_headers,
            )
            assert forbidden.status_code == 403, forbidden.text
            assert _detail(forbidden) == spec.forbidden_detail
            hidden = client.get(spec.impact, headers=role_headers)
            assert hidden.status_code == 403, hidden.text

        for bad in ("", "   ", spec.too_long):
            invalid = client.patch(spec.patch, json={spec.body_key: bad}, headers=headers)
            assert invalid.status_code == 422, invalid.text
            assert _detail(invalid) == spec.invalid_detail

        same = client.patch(spec.patch, json={spec.body_key: f"  {spec.value}  "}, headers=headers)
        assert same.status_code == 400, same.text
        assert _detail(same) == spec.same_detail

        duplicate = client.patch(spec.patch, json={spec.body_key: spec.other}, headers=headers)
        assert duplicate.status_code == 400, duplicate.text
        assert _detail(duplicate) == spec.duplicate_detail
        assert "duplicate key" not in duplicate.text.lower()
        assert "sql" not in duplicate.text.lower()

        missing = client.patch(spec.missing, json={spec.body_key: spec.new_value}, headers=headers)
        assert missing.status_code == 404, missing.text
        assert _detail(missing) == spec.missing_detail
        missing_impact = client.get(f"{spec.missing}/impact", headers=headers)
        assert missing_impact.status_code == 404, missing_impact.text

        unchanged = client.get(spec.read, headers=headers)
        assert unchanged.json()[spec.field] == spec.value


def _assert_audit(spec: SimpleNamespace, before: str, after: str, operator_id: int) -> None:
    action, before_data, after_data, operator = _audit_row(spec.id, spec.audit)
    assert action == spec.audit
    assert operator == operator_id
    assert before_data == {spec.field: before}
    assert after_data == {spec.field: after}
    blob = f"{before_data} {after_data}".lower()
    assert "password" not in blob
    assert "token" not in blob
    assert "secret" not in blob


def test_employee_correction_keeps_relations(client: TestClient) -> None:
    headers = admin_headers(client)
    operator_id = client.get("/api/auth/me", headers=headers).json()["id"]
    employee = create_employee(client, headers, name="关系人员")
    project = create_project(client, headers, manager_employee_id=employee["id"])
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], employee_id=employee["id"])
    expense = create_expense(
        client,
        headers,
        distributions=[
            {
                "employee_id": employee["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "100.00",
            }
        ],
    )
    user, _username, password = create_user_account(
        client, headers, role_code="MEMBER", employee_id=employee["id"], password="Passw0rd!"
    )
    with engine.connect() as connection:
        password_before = connection.execute(
            text("SELECT password_hash FROM users WHERE id = :id"),
            {"id": user["id"]},
        ).scalar_one()

    impact = client.get(f"/api/employees/{employee['id']}/employee-no/impact", headers=headers)
    assert impact.status_code == 200, impact.text
    counts = {item["label"]: item["count"] for item in impact.json()["items"]}
    assert counts == {"负责项目": 1, "项目成员": 1, "资源分配": 1, "费用归属": 1, "系统账号": 1}

    new_no = unique("ENO")
    corrected = client.patch(
        f"/api/employees/{employee['id']}/employee-no",
        json={"new_employee_no": f"  {new_no}  "},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["id"] == employee["id"]
    assert corrected.json()["employee_no"] == new_no
    assert corrected.json()["name"] == "关系人员"

    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT id FROM employees WHERE id = :id"),
            {"id": employee["id"]},
        ).scalar_one() == employee["id"]
        assert connection.execute(
            text("SELECT manager_employee_id FROM projects WHERE id = :id"),
            {"id": project["id"]},
        ).scalar_one() == employee["id"]
        assert connection.execute(
            text("SELECT employee_id FROM project_members WHERE project_id = :id"),
            {"id": project["id"]},
        ).scalar_one() == employee["id"]
        assert connection.execute(
            text("SELECT employee_id FROM resource_allocations WHERE id = :id"),
            {"id": allocation["id"]},
        ).scalar_one() == employee["id"]
        assert connection.execute(
            text("SELECT employee_id FROM expense_distributions WHERE expense_record_id = :id"),
            {"id": expense["id"]},
        ).scalar_one() == employee["id"]
        account = connection.execute(
            text("SELECT employee_id, password_hash FROM users WHERE id = :id"),
            {"id": user["id"]},
        ).one()
    assert account[0] == employee["id"]
    assert account[1] == password_before
    assert login(client, new_no, password).status_code != 200
    assert login(client, user["username"], password).status_code == 200

    spec = SimpleNamespace(id=employee["id"], field="employee_no", audit="EMPLOYEE_NO_CHANGE")
    _assert_audit(spec, employee["employee_no"], new_no, operator_id)

    stale = _preview(
        client,
        headers,
        "project_members",
        ["project_code", "employee_no"],
        [project["project_code"], employee["employee_no"]],
    )
    assert stale.status_code == 200, stale.text
    assert stale.json()["errors"][0]["message"] == "人员不存在"
    matched = _preview(
        client,
        headers,
        "project_members",
        ["project_code", "employee_no"],
        [project["project_code"], new_no],
    )
    assert matched.status_code == 200, matched.text
    assert not any(item.get("message") == "人员不存在" for item in matched.json().get("errors") or [])


def test_project_correction_keeps_relations(client: TestClient) -> None:
    headers = admin_headers(client)
    operator_id = client.get("/api/auth/me", headers=headers).json()["id"]
    manager = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=manager["id"], name="关系项目")
    member = create_employee(client, headers)
    client.post(
        f"/api/projects/{project['id']}/members",
        json={"employee_id": member["id"]},
        headers=headers,
    )
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], project_id=project["id"])
    expense = create_expense(
        client,
        headers,
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "100.00"}
        ],
    )
    rule = create_recurring_rule(
        client,
        headers,
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "140.00"}
        ],
    )
    impact = client.get(f"/api/projects/{project['id']}/project-code/impact", headers=headers)
    assert impact.status_code == 200, impact.text
    counts = {item["label"]: item["count"] for item in impact.json()["items"]}
    assert counts["项目成员"] == 2
    assert counts["资源分配"] == 1
    assert counts["费用归属"] == 1
    assert counts["周期规则"] == 1

    new_code = unique("PCD")
    corrected = client.patch(
        f"/api/projects/{project['id']}/project-code",
        json={"new_project_code": f"  {new_code}  "},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["id"] == project["id"]
    assert corrected.json()["project_code"] == new_code

    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT project_id FROM project_members WHERE project_id = :id"),
            {"id": project["id"]},
        ).first()[0] == project["id"]
        assert connection.execute(
            text("SELECT project_id FROM resource_allocations WHERE id = :id"),
            {"id": allocation["id"]},
        ).scalar_one() == project["id"]
        assert connection.execute(
            text("SELECT project_id FROM expense_distributions WHERE expense_record_id = :id"),
            {"id": expense["id"]},
        ).scalar_one() == project["id"]
        assert connection.execute(
            text("SELECT project_id FROM recurring_rule_distributions WHERE rule_id = :id"),
            {"id": rule["id"]},
        ).scalar_one() == project["id"]
    spec = SimpleNamespace(id=project["id"], field="project_code", audit="PROJECT_CODE_CHANGE")
    _assert_audit(spec, project["project_code"], new_code, operator_id)

    stale = _preview(
        client,
        headers,
        "project_members",
        ["project_code", "employee_no"],
        [project["project_code"], manager["employee_no"]],
    )
    assert stale.json()["errors"][0]["message"] == "项目不存在"
    matched = _preview(
        client,
        headers,
        "project_members",
        ["project_code", "employee_no"],
        [new_code, manager["employee_no"]],
    )
    assert "项目不存在" not in str(matched.json().get("errors"))


def test_resource_type_correction_keeps_accounts(client: TestClient) -> None:
    headers = admin_headers(client)
    operator_id = client.get("/api/auth/me", headers=headers).json()["id"]
    created = create_resource_type(client, headers, name="关系类型")
    first = create_resource(client, headers, resource_type_id=created["id"])
    second = create_resource(client, headers, resource_type_id=created["id"])
    impact = client.get(f"/api/resource-types/{created['id']}/code/impact", headers=headers)
    assert impact.json()["items"] == [{"label": "关联资源", "count": 2}]
    new_code = unique("RTC").upper()
    corrected = client.patch(
        f"/api/resource-types/{created['id']}/code",
        json={"new_code": new_code},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["id"] == created["id"]
    assert corrected.json()["code"] == new_code
    with engine.connect() as connection:
        links = {
            row[0]: row[1]
            for row in connection.execute(
                text("SELECT id, resource_type_id FROM resource_accounts WHERE id IN (:first_id, :second_id)"),
                {"first_id": first["id"], "second_id": second["id"]},
            )
        }
    assert links == {first["id"]: created["id"], second["id"]: created["id"]}
    spec = SimpleNamespace(id=created["id"], field="code", audit="RESOURCE_TYPE_CODE_CHANGE")
    _assert_audit(spec, created["code"], new_code, operator_id)
    stale = _preview(
        client,
        headers,
        "resources",
        ["resource_name", "resource_type_code"],
        [unique("旧类型导入"), created["code"]],
    )
    assert stale.json()["errors"][0]["message"] == "资源类型不存在"
    matched = _preview(
        client,
        headers,
        "resources",
        ["resource_name", "resource_type_code"],
        [unique("新类型导入"), new_code],
    )
    assert matched.json()["valid_rows"] == 1


def test_expense_type_correction_keeps_expenses(client: TestClient) -> None:
    headers = admin_headers(client)
    operator_id = client.get("/api/auth/me", headers=headers).json()["id"]
    employee = create_employee(client, headers)
    expense_type = create_expense_type(client, headers, name="关系费用类型")
    expense = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        distributions=[
            {"employee_id": employee["id"], "allocation_method": "DIRECT", "allocated_amount": "100.00"}
        ],
    )
    rule = create_recurring_rule(
        client,
        headers,
        expense_type_id=expense_type["id"],
        distributions=[
            {"employee_id": employee["id"], "allocation_method": "DIRECT", "allocated_amount": "140.00"}
        ],
    )
    impact = client.get(f"/api/expense-types/{expense_type['id']}/code/impact", headers=headers)
    counts = {item["label"]: item["count"] for item in impact.json()["items"]}
    assert counts == {"费用记录": 1, "周期规则": 1}
    new_code = unique("ETC").upper()
    corrected = client.patch(
        f"/api/expense-types/{expense_type['id']}/code",
        json={"new_code": f"  {new_code}  "},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["id"] == expense_type["id"]
    assert corrected.json()["code"] == new_code
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT expense_type_id FROM expense_records WHERE id = :id"),
            {"id": expense["id"]},
        ).scalar_one() == expense_type["id"]
        assert connection.execute(
            text("SELECT expense_type_id FROM recurring_expense_rules WHERE id = :id"),
            {"id": rule["id"]},
        ).scalar_one() == expense_type["id"]
    spec = SimpleNamespace(id=expense_type["id"], field="code", audit="EXPENSE_TYPE_CODE_CHANGE")
    _assert_audit(spec, expense_type["code"], new_code, operator_id)
    stale = _preview(
        client,
        headers,
        "expenses",
        ["expense_type_code", "billing_mode", "expense_date", "amount", "currency", "employee_no"],
        [expense_type["code"], "MANUAL", "2026-09-01", "100.00", "CNY", employee["employee_no"]],
    )
    assert stale.json()["errors"][0]["message"] == "费用类型不存在"
    matched = _preview(
        client,
        headers,
        "expenses",
        ["expense_type_code", "billing_mode", "expense_date", "amount", "currency", "employee_no"],
        [new_code, "MANUAL", "2026-09-01", "100.00", "CNY", employee["employee_no"]],
    )
    assert matched.json()["valid_rows"] == 1


def test_username_correction_keeps_password_and_binding(client: TestClient) -> None:
    headers = admin_headers(client)
    operator_id = client.get("/api/auth/me", headers=headers).json()["id"]
    employee = create_employee(client, headers, name="绑定人员")
    user, username, password = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=employee["id"], password="Passw0rd!"
    )
    with engine.connect() as connection:
        before = connection.execute(
            text("SELECT password_hash, employee_id, role_id FROM users WHERE id = :id"),
            {"id": user["id"]},
        ).one()
    impact = client.get(f"/api/users/{user['id']}/username/impact", headers=headers)
    assert impact.json()["items"] == [{"label": "关联人员", "count": 1}]
    new_name = unique("usr")
    corrected = client.patch(
        f"/api/users/{user['id']}/username",
        json={"new_username": f"  {new_name}  "},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["id"] == user["id"]
    assert corrected.json()["username"] == new_name
    assert corrected.json()["employee_id"] == employee["id"]
    assert corrected.json()["role_id"] == user["role_id"]
    with engine.connect() as connection:
        after = connection.execute(
            text("SELECT password_hash, employee_id, role_id FROM users WHERE id = :id"),
            {"id": user["id"]},
        ).one()
    assert after == before
    assert login(client, new_name, password).status_code == 200
    assert login(client, username, password).status_code != 200
    spec = SimpleNamespace(id=user["id"], field="username", audit="USERNAME_CHANGE")
    _assert_audit(spec, username, new_name, operator_id)


def test_resource_name_correction_keeps_links(client: TestClient) -> None:
    headers = admin_headers(client)
    operator_id = client.get("/api/auth/me", headers=headers).json()["id"]
    employee = create_employee(client, headers)
    project = create_project(client, headers, manager_employee_id=employee["id"])
    resource = create_resource(client, headers)
    allocation = create_allocation(client, headers, resource["id"], project_id=project["id"])
    expense = create_expense(
        client,
        headers,
        resource_account_id=resource["id"],
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "100.00"}
        ],
    )
    rule = create_recurring_rule(
        client,
        headers,
        resource_account_id=resource["id"],
        distributions=[
            {"project_id": project["id"], "allocation_method": "DIRECT", "allocated_amount": "140.00"}
        ],
    )
    impact = client.get(f"/api/resources/{resource['id']}/resource-name/impact", headers=headers)
    counts = {item["label"]: item["count"] for item in impact.json()["items"]}
    assert counts["资源分配"] == 1
    assert counts["关联项目"] == 1
    assert counts["费用引用"] == 1
    assert counts["周期规则"] == 1
    new_name = unique("资源名")
    corrected = client.patch(
        f"/api/resources/{resource['id']}/resource-name",
        json={"new_resource_name": f"  {new_name}  "},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["id"] == resource["id"]
    assert corrected.json()["resource_name"] == new_name
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT resource_account_id FROM resource_allocations WHERE id = :id"),
            {"id": allocation["id"]},
        ).scalar_one() == resource["id"]
        assert connection.execute(
            text("SELECT resource_account_id FROM expense_records WHERE id = :id"),
            {"id": expense["id"]},
        ).scalar_one() == resource["id"]
        assert connection.execute(
            text("SELECT resource_account_id FROM recurring_expense_rules WHERE id = :id"),
            {"id": rule["id"]},
        ).scalar_one() == resource["id"]
    spec = SimpleNamespace(id=resource["id"], field="resource_name", audit="RESOURCE_NAME_CHANGE")
    _assert_audit(spec, resource["resource_name"], new_name, operator_id)
    stale = _preview(
        client,
        headers,
        "resource_allocations",
        ["resource_name", "project_code"],
        [resource["resource_name"], project["project_code"]],
    )
    assert stale.json()["errors"][0]["message"] == "资源不存在"
    matched = _preview(
        client,
        headers,
        "resource_allocations",
        ["resource_name", "project_code"],
        [new_name, project["project_code"]],
    )
    assert matched.json()["valid_rows"] == 1 or "资源不存在" not in str(matched.json().get("errors"))

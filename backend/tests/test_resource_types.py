from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import inspect, text

from app.core.database import engine
from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_employee,
    create_resource,
    create_resource_type,
    create_user_account,
    unique,
)


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


def _role_headers(client: TestClient, admin: dict[str, str], role_code: str) -> dict[str, str]:
    employee = create_employee(client, admin)
    _, username, password = create_user_account(
        client, admin, role_code=role_code, employee_id=employee["id"]
    )
    return auth_headers_for(client, username, password)


def test_admin_create_update_resource_type(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource_type(
        client, headers, name="Cursor", category="DEVELOPMENT"
    )
    assert created["name"] == "Cursor"
    assert created["category"] == "DEVELOPMENT"
    assert created["is_active"] is True

    updated = client.put(
        f"/api/resource-types/{created['id']}",
        json={"name": "Cursor IDE", "description": "开发工具"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Cursor IDE"
    assert updated.json()["description"] == "开发工具"


def test_duplicate_resource_type_code_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    code = unique("CHATGPT").upper()
    create_resource_type(client, headers, code=code)
    response = client.post(
        "/api/resource-types",
        json={"code": code, "name": "重复", "category": "AI"},
        headers=headers,
    )
    assert response.status_code == 400


def test_admin_disable_enable_resource_type(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource_type(client, headers)
    disabled = client.post(f"/api/resource-types/{created['id']}/disable", headers=headers)
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
    enabled = client.post(f"/api/resource-types/{created['id']}/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["is_active"] is True


def test_non_admin_cannot_write_resource_types(client: TestClient) -> None:
    headers = admin_headers(client)
    employee = create_employee(client, headers)
    _, username, password = create_user_account(
        client, headers, role_code="BOSS", employee_id=employee["id"]
    )
    boss = auth_headers_for(client, username, password)
    pm_emp = create_employee(client, headers)
    _, pm_user, pm_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_emp["id"]
    )
    pm = auth_headers_for(client, pm_user, pm_pass)
    member_emp = create_employee(client, headers)
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_emp["id"]
    )
    member = auth_headers_for(client, member_user, member_pass)

    payload = {"code": "FIGMA", "name": "Figma", "category": "DESIGN"}
    for role_headers in (boss, pm, member):
        response = client.post("/api/resource-types", json=payload, headers=role_headers)
        assert response.status_code == 403


def test_logged_in_users_can_read_active_types(client: TestClient) -> None:
    headers = admin_headers(client)
    active = create_resource_type(client, headers, code="GITHUB")
    inactive = create_resource_type(client, headers, code="OLDTYPE")
    client.post(f"/api/resource-types/{inactive['id']}/disable", headers=headers)
    member_emp = create_employee(client, headers)
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_emp["id"]
    )
    member = auth_headers_for(client, member_user, member_pass)
    listed = client.get("/api/resource-types", headers=member)
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()}
    assert active["id"] in ids
    assert inactive["id"] not in ids


def test_resource_type_write_is_audited(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource_type(client, headers, code="AUDITTYPE")
    client.put(f"/api/resource-types/{created['id']}", json={"name": "审计类型"}, headers=headers)
    client.post(f"/api/resource-types/{created['id']}/disable", headers=headers)
    with engine.connect() as connection:
        actions = {
            row[0]
            for row in connection.execute(
                text("SELECT action FROM audit_logs WHERE target_id = :target_id"),
                {"target_id": str(created["id"])},
            )
        }
    assert "RESOURCE_TYPE_CREATE" in actions
    assert "RESOURCE_TYPE_UPDATE" in actions
    assert "RESOURCE_TYPE_DISABLE" in actions


def test_resource_type_code_unique_index_kept() -> None:
    indexes = inspect(engine).get_indexes("resource_types")
    code_unique = [
        item
        for item in indexes
        if item.get("unique") and list(item.get("column_names") or []) == ["code"]
    ]
    assert code_unique


def test_normal_edit_changes_profile_but_rejects_code(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource_type(client, headers, code=unique("LOCK").upper(), category="AI")
    updated = client.put(
        f"/api/resource-types/{created['id']}",
        json={"name": "已改名称", "category": "DESIGN", "description": "已改说明"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["name"] == "已改名称"
    assert body["category"] == "DESIGN"
    assert body["description"] == "已改说明"
    assert body["code"] == created["code"]
    assert body["is_active"] is True

    disabled = client.post(f"/api/resource-types/{created['id']}/disable", headers=headers)
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
    assert disabled.json()["code"] == created["code"]
    enabled = client.post(f"/api/resource-types/{created['id']}/enable", headers=headers)
    assert enabled.status_code == 200
    assert enabled.json()["is_active"] is True

    rejected = client.put(
        f"/api/resource-types/{created['id']}",
        json={"name": "绕过编码", "code": unique("HACK").upper()},
        headers=headers,
    )
    assert rejected.status_code == 422
    current = client.get(f"/api/resource-types/{created['id']}", headers=headers)
    assert current.status_code == 200
    assert current.json()["code"] == created["code"]
    assert current.json()["name"] == "已改名称"


def test_code_correction_validation_and_permissions(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_resource_type(client, headers, code=unique("OLD").upper())
    other = create_resource_type(client, headers, code=unique("TAKEN").upper())
    path = f"/api/resource-types/{created['id']}/code"

    for role_code in ("MEMBER", "PROJECT_MANAGER", "BOSS"):
        response = client.patch(
            path,
            json={"new_code": unique("NO").upper()},
            headers=_role_headers(client, headers, role_code),
        )
        assert response.status_code == 403
        assert _detail(response) == "无权限修正资源类型编码"

    missing = client.get("/api/resource-types/99999999", headers=headers)
    assert missing.status_code == 404
    absent = client.patch("/api/resource-types/99999999/code", json={"new_code": "missing-type"}, headers=headers)
    assert absent.status_code == 404
    assert _detail(absent) == "资源类型不存在"

    for bad in ("", "   ", "x" * 51):
        response = client.patch(path, json={"new_code": bad}, headers=headers)
        assert response.status_code == 422
        assert _detail(response) == "编码格式不合法"

    same = client.patch(path, json={"new_code": f"  {created['code']}  "}, headers=headers)
    assert same.status_code == 400
    assert _detail(same) == "新编码与当前编码一致"

    duplicate = client.patch(path, json={"new_code": other["code"]}, headers=headers)
    assert duplicate.status_code == 400
    assert _detail(duplicate) == "资源类型编码已存在"
    assert "sql" not in duplicate.text.lower()
    assert "duplicate key" not in duplicate.text.lower()

    unchanged = client.get(f"/api/resource-types/{created['id']}", headers=headers)
    assert unchanged.json()["code"] == created["code"]


def test_code_correction_keeps_accounts_import_and_audit(client: TestClient) -> None:
    headers = admin_headers(client)
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    operator_id = me.json()["id"]
    old_code = f"{unique('IMP').upper()}A"
    new_code = old_code.lower()
    assert new_code != old_code
    created = create_resource_type(client, headers, code=old_code, name="导入类型")
    first = create_resource(client, headers, resource_type_id=created["id"], resource_name=unique("账号甲"))
    second = create_resource(client, headers, resource_type_id=created["id"], resource_name=unique("账号乙"))
    with engine.connect() as connection:
        before_ids = [
            row[0]
            for row in connection.execute(
                text(
                    "SELECT id FROM resource_accounts WHERE resource_type_id = :type_id ORDER BY id"
                ),
                {"type_id": created["id"]},
            )
        ]
    assert before_ids == sorted([first["id"], second["id"]])

    corrected = client.patch(
        f"/api/resource-types/{created['id']}/code",
        json={"new_code": f"  {new_code}  "},
        headers=headers,
    )
    assert corrected.status_code == 200, corrected.text
    body = corrected.json()
    assert body["code"] == new_code
    assert body["name"] == "导入类型"
    assert body["related_account_count"] == 2
    assert body["id"] == created["id"]

    with engine.connect() as connection:
        links = connection.execute(
            text(
                """
                SELECT id, resource_type_id
                FROM resource_accounts
                WHERE id IN (:first_id, :second_id)
                ORDER BY id
                """
            ),
            {"first_id": first["id"], "second_id": second["id"]},
        ).all()
        after_ids = [row[0] for row in links]
        assert after_ids == before_ids
        assert {row[1] for row in links} == {created["id"]}
        audit = connection.execute(
            text(
                """
                SELECT action, operator_user_id, before_data, after_data, created_at
                FROM audit_logs
                WHERE target_id = :target_id AND action = 'RESOURCE_TYPE_CODE_CHANGE'
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"target_id": str(created["id"])},
        ).one()
    assert audit[0] == "RESOURCE_TYPE_CODE_CHANGE"
    assert audit[1] == operator_id
    assert audit[2] == {"code": old_code}
    assert audit[3] == {"code": new_code}
    assert audit[4] is not None
    assert "password" not in str(audit[2]).lower()
    assert "token" not in str(audit[3]).lower()

    listed = client.get(f"/api/resources/{first['id']}", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["resource_type"]["id"] == created["id"]
    assert listed.json()["resource_type"]["code"] == new_code

    def preview(type_code: str, resource_name: str):
        content = _xlsx(
            ["resource_name", "resource_type_code"],
            [[resource_name, type_code]],
        )
        return client.post(
            "/api/imports/resources/preview",
            headers=headers,
            files={
                "file": (
                    "resources.xlsx",
                    content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    matched = preview(new_code, unique("新编码导入"))
    assert matched.status_code == 200, matched.text
    assert matched.json()["valid_rows"] == 1
    assert matched.json()["invalid_rows"] == 0

    stale = preview(old_code, unique("旧编码导入"))
    assert stale.status_code == 200, stale.text
    assert stale.json()["valid_rows"] == 0
    assert stale.json()["errors"][0]["field"] == "resource_type_code"
    assert stale.json()["errors"][0]["message"] == "资源类型不存在"

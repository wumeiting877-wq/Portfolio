from io import BytesIO

from openpyxl import Workbook
from fastapi.testclient import TestClient

from tests.helpers import admin_headers, auth_headers_for, create_employee, create_user_account, unique


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


def _file(content: bytes, name: str = "ok.xlsx"):
    return {"file": (name, content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


def test_template_download(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.get("/api/imports/templates/employees", headers=headers)
    assert response.status_code == 200
    assert "spreadsheet" in response.headers["content-type"]


def test_preview_success(client: TestClient) -> None:
    headers = admin_headers(client)
    content = _xlsx(["employee_no", "name", "email"], [[unique("IMP"), "导入人员", "ok@example.com"]])
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(content))
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 1
    assert body["valid_rows"] == 1
    assert body["invalid_rows"] == 0


def test_reject_non_xlsx(client: TestClient) -> None:
    headers = admin_headers(client)
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(b"abc", "bad.csv"))
    assert response.status_code == 400


def test_reject_oversized_file(client: TestClient) -> None:
    headers = admin_headers(client)
    huge = b"a" * (10 * 1024 * 1024 + 10)
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(huge))
    assert response.status_code == 400


def test_error_returns_row_and_field(client: TestClient) -> None:
    headers = admin_headers(client)
    existing = create_employee(client, headers)
    content = _xlsx(["employee_no", "name"], [[existing["employee_no"], "重复"]])
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(content))
    assert response.status_code == 200
    error = response.json()["errors"][0]
    assert error["row"] == 2
    assert error["field"] == "employee_no"


def test_preview_does_not_write(client: TestClient) -> None:
    headers = admin_headers(client)
    before = client.get("/api/employees", headers=headers).json()
    content = _xlsx(["employee_no", "name"], [[unique("PREV"), "预检不写"]])
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(content))
    assert response.status_code == 200
    after = client.get("/api/employees", headers=headers).json()
    assert len(after) == len(before)


def test_commit_success(client: TestClient) -> None:
    headers = admin_headers(client)
    employee_no = unique("CMT")
    content = _xlsx(["employee_no", "name", "email"], [[employee_no, "正式导入", "ok@example.com"]])
    response = client.post("/api/imports/employees/commit", headers=headers, files=_file(content))
    assert response.status_code == 200, response.text
    assert response.json()["committed"] is True
    listed = client.get("/api/employees", headers=headers).json()
    assert any(item["employee_no"] == employee_no for item in listed)


def test_commit_rolls_back_whole_batch(client: TestClient) -> None:
    headers = admin_headers(client)
    before = {item["employee_no"] for item in client.get("/api/employees", headers=headers).json()}
    content = _xlsx(
        ["employee_no", "name", "email"],
        [[unique("RB1"), "回滚甲", "ok@example.com"], [unique("RB2"), "回滚乙", "bad-email"]],
    )
    response = client.post("/api/imports/employees/commit", headers=headers, files=_file(content))
    assert response.status_code == 400
    after = {item["employee_no"] for item in client.get("/api/employees", headers=headers).json()}
    assert after == before


def test_non_admin_import_forbidden(client: TestClient) -> None:
    admin = admin_headers(client)
    employee = create_employee(client, admin)
    _, username, password = create_user_account(
        client, admin, role_code="BOSS", employee_id=employee["id"]
    )
    headers = auth_headers_for(client, username, password)
    content = _xlsx(["employee_no", "name"], [[unique("NO"), "不可导入"]])
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(content))
    assert response.status_code == 403


def test_password_column_rejected(client: TestClient) -> None:
    headers = admin_headers(client)
    content = _xlsx(["employee_no", "name", "password"], [[unique("SEC"), "安全", "secret"]])
    response = client.post("/api/imports/employees/preview", headers=headers, files=_file(content))
    assert response.status_code == 400
    assert "凭据" in response.text or "password" in response.text.lower()


def test_api_key_column_rejected(client: TestClient) -> None:
    headers = admin_headers(client)
    content = _xlsx(["resource_name", "resource_type_code", "api_key"], [["R1", "X", "k"]])
    response = client.post("/api/imports/resources/preview", headers=headers, files=_file(content))
    assert response.status_code == 400

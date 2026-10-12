from fastapi.testclient import TestClient

from tests.helpers import admin_headers, create_employee, unique


def test_create_query_update_disable_employee(client: TestClient) -> None:
    headers = admin_headers(client)
    created = create_employee(client, headers, name="张三", department="研发部")
    employee_id = created["id"]

    listed = client.get("/api/employees", headers=headers, params={"q": "张三"})
    assert listed.status_code == 200
    assert any(item["id"] == employee_id for item in listed.json())

    detail = client.get(f"/api/employees/{employee_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["employee_no"] == created["employee_no"]

    updated = client.put(
        f"/api/employees/{employee_id}",
        json={"position": "高级工程师", "department": "研发部"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["position"] == "高级工程师"

    disabled = client.delete(f"/api/employees/{employee_id}", headers=headers)
    assert disabled.status_code == 200
    assert disabled.json()["employment_status"] == "INACTIVE"


def test_duplicate_employee_no_fails(client: TestClient) -> None:
    headers = admin_headers(client)
    employee_no = unique("NO")
    create_employee(client, headers, employee_no=employee_no)
    response = client.post(
        "/api/employees",
        json={"employee_no": employee_no, "name": "重复工号"},
        headers=headers,
    )
    assert response.status_code == 400

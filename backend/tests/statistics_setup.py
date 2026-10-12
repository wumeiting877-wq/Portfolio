from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.helpers import (
    admin_headers,
    auth_headers_for,
    create_allocation,
    create_employee,
    create_expense,
    create_expense_type,
    create_project,
    create_resource,
    create_resource_type,
    create_user_account,
    unique,
)


def setup_statistics_world(client: TestClient) -> dict:
    headers = admin_headers(client)
    pm_a = create_employee(client, headers, name="统计负责人A")
    pm_b = create_employee(client, headers, name="统计负责人B")
    member_a = create_employee(client, headers, name="统计成员A")
    member_d = create_employee(client, headers, name="同项目另一成员")
    extra = create_employee(client, headers, name="统计老板人员")

    _, pm_user, pm_pass = create_user_account(
        client, headers, role_code="PROJECT_MANAGER", employee_id=pm_a["id"]
    )
    _, member_user, member_pass = create_user_account(
        client, headers, role_code="MEMBER", employee_id=member_a["id"]
    )
    _, boss_user, boss_pass = create_user_account(
        client, headers, role_code="BOSS", employee_id=extra["id"]
    )

    project_a = create_project(client, headers, name="Project A", manager_employee_id=pm_a["id"])
    project_b = create_project(client, headers, name="Project B", manager_employee_id=pm_b["id"])
    year = 1500 + project_a["id"]
    sep_from = f"{year}-09-01"
    sep_to = f"{year}-09-30"
    year_from = f"{year}-01-01"
    year_to = f"{year}-12-31"
    span_from = f"{year}-07-01"
    span_to = f"{year}-09-30"
    client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": member_a["id"]},
        headers=headers,
    )
    client.post(
        f"/api/projects/{project_a['id']}/members",
        json={"employee_id": member_d["id"]},
        headers=headers,
    )

    expense_type = create_expense_type(client, headers, category="SOFTWARE")
    usage_type = create_expense_type(client, headers, category="API_USAGE")
    server_type = create_expense_type(client, headers, category="SERVER")
    rt_ai = create_resource_type(client, headers, category="AI", name="AI 账号")
    bound = create_resource(client, headers, resource_type_id=rt_ai["id"], resource_name=unique("绑定资源"))
    create_allocation(client, headers, bound["id"], project_id=project_a["id"], employee_id=member_a["id"])

    idle = create_resource(client, headers, status="IDLE", resource_name=unique("显式闲置资源"))
    unassigned = create_resource(client, headers, status="ACTIVE", resource_name=unique("未分配活跃资源"))
    expired = create_resource(client, headers, status="EXPIRED", resource_name=unique("已到期资源"))
    expiring = create_resource(
        client,
        headers,
        status="ACTIVE",
        resource_name=unique("即将到期资源"),
        expires_at=(date.today() + timedelta(days=10)).isoformat(),
    )
    later = create_resource(
        client,
        headers,
        status="ACTIVE",
        resource_name=unique("远期到期资源"),
        expires_at=(date.today() + timedelta(days=90)).isoformat(),
    )
    released_resource = create_resource(client, headers, resource_name=unique("已释放分配资源"))
    released_alloc = create_allocation(
        client,
        headers,
        released_resource["id"],
        project_id=project_a["id"],
        employee_id=member_a["id"],
    )
    client.delete(
        f"/api/resources/{released_resource['id']}/allocations/{released_alloc['id']}",
        headers=headers,
    )

    cny_a = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="100.00",
        currency="CNY",
        expense_date=sep_from,
        resource_account_id=bound["id"],
        distributions=[
            {
                "project_id": project_a["id"],
                "employee_id": member_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "100.00",
            }
        ],
    )
    usd_a = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="100.00",
        currency="USD",
        expense_date=sep_from,
        distributions=[
            {
                "project_id": project_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "100.00",
            }
        ],
    )
    cny_b = create_expense(
        client,
        headers,
        expense_type_id=server_type["id"],
        amount="200.00",
        currency="CNY",
        expense_date=f"{year}-08-15",
        billing_mode="ONE_TIME",
        distributions=[
            {
                "project_id": project_b["id"],
                "employee_id": pm_b["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "200.00",
            }
        ],
    )
    shared = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="1000.00",
        currency="CNY",
        expense_date=f"{year}-09-10",
        distributions=[
            {
                "project_id": project_a["id"],
                "allocation_method": "RATIO",
                "allocation_ratio": "0.6",
            },
            {
                "project_id": project_b["id"],
                "allocation_method": "RATIO",
                "allocation_ratio": "0.4",
            },
        ],
    )
    member_direct = create_expense(
        client,
        headers,
        expense_type_id=usage_type["id"],
        amount="30.00",
        currency="CNY",
        expense_date=f"{year}-07-20",
        billing_mode="USAGE",
        distributions=[
            {
                "employee_id": member_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "30.00",
            }
        ],
    )
    project_public = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="50.00",
        currency="CNY",
        expense_date=f"{year}-09-12",
        distributions=[
            {
                "project_id": project_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "50.00",
            }
        ],
    )
    other_member = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="300.00",
        currency="CNY",
        expense_date=f"{year}-09-05",
        distributions=[
            {
                "project_id": project_a["id"],
                "employee_id": member_d["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "300.00",
            }
        ],
    )
    voided = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="999.00",
        currency="CNY",
        expense_date=f"{year}-09-08",
        distributions=[
            {
                "project_id": project_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "999.00",
            }
        ],
    )
    client.post(f"/api/expenses/{voided['id']}/void", headers=headers)

    unbound = create_expense(
        client,
        headers,
        expense_type_id=expense_type["id"],
        amount="40.00",
        currency="USD",
        expense_date=f"{year}-09-18",
        distributions=[
            {
                "project_id": project_a["id"],
                "allocation_method": "DIRECT",
                "allocated_amount": "40.00",
            }
        ],
    )

    return {
        "admin": headers,
        "boss": auth_headers_for(client, boss_user, boss_pass),
        "pm": auth_headers_for(client, pm_user, pm_pass),
        "member": auth_headers_for(client, member_user, member_pass),
        "project_a": project_a,
        "project_b": project_b,
        "member_a": member_a,
        "member_d": member_d,
        "pm_a": pm_a,
        "pm_b": pm_b,
        "cny_a": cny_a,
        "usd_a": usd_a,
        "cny_b": cny_b,
        "shared": shared,
        "member_direct": member_direct,
        "project_public": project_public,
        "other_member": other_member,
        "voided": voided,
        "unbound": unbound,
        "bound": bound,
        "idle": idle,
        "unassigned": unassigned,
        "expired": expired,
        "expiring": expiring,
        "later": later,
        "released_resource": released_resource,
        "rt_ai": rt_ai,
        "year": year,
        "sep_from": sep_from,
        "sep_to": sep_to,
        "year_from": year_from,
        "year_to": year_to,
        "span_from": span_from,
        "span_to": span_to,
        "sep_period": f"{year}-09",
        "aug_period": f"{year}-08",
        "jul_period": f"{year}-07",
    }

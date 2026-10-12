# Gate 5 Statistics Scope Verification

日期：2026-09-22  
方式：对运行中的后端 `http://127.0.0.1:8010` 使用真实账号调用 Statistics API  
脚本：`backend/app/scripts/verify_gate5_statistics.py`  
过滤日期：`date_from=date_to=2026-09-22`（仅本轮 Gate 5 取证费用）

不能只做代码检查。以下为真实返回。

## 账号

| 用户名 | 角色 | Scope |
| --- | --- | --- |
| admin | ADMIN | GLOBAL |
| boss | BOSS | GLOBAL |
| pm | PROJECT_MANAGER | MANAGED_PROJECTS |
| member | MEMBER | MEMBER_PROJECTS |

## 准备数据

Project A = `GATE2-A`（id=1），负责人 pm，成员含 member。  
Project B = `GATE2-B`（id=2），负责人 PM002。

| 标记 | description | amount | 分摊 |
| --- | --- | --- | --- |
| A CNY | GATE5-A-CNY | 100 CNY | Project A / member，绑定 GATE5-BOUND |
| A USD | GATE5-A-USD | 100 USD | Project A 公共 |
| B CNY | GATE5-B-CNY | 200 CNY | Project B / PM002 |
| Shared | GATE5-SHARED | 1000 CNY | A 60% + B 40% |
| Member direct | GATE5-MEMBER-DIRECT | 30 CNY | 仅 member，无 project_id |
| Public | GATE5-PUBLIC | 50 CNY | Project A 公共 |
| Voided | GATE5-VOIDED | 999 CNY | 已作废 |

资源：GATE5-IDLE、GATE5-UNASSIGNED、GATE5-EXPIRING（expires_at=2026-10-02，剩余 10 天，status 仍为 ACTIVE）。

## 期望（2026-09-22）

```text
ADMIN CNY = 100 + 200 + 1000 + 30 + 50 = 1380
ADMIN USD = 100
VOIDED 999 不计

PM 可见 A 份额 CNY = 100 + 600 + 50 = 750
PM USD = 100
PM 不见 B 的 200 与 shared 400
PM 不见 member-direct 30（无 project_id）

MEMBER CNY = 100 + 30 = 130
MEMBER 不见 USD、项目公共、他人、公司总费用
```

## admin

HTTP 200。`GET /api/statistics/overview`：

```json
{
  "amounts_by_currency": { "CNY": "1380.00", "USD": "100.00" },
  "project_count": 2,
  "resource_count": 11,
  "active_resource_count": 10,
  "idle_resource_count": 1,
  "unassigned_active_resource_count": 3,
  "expiring_soon_count": 1
}
```

无 `total`。Project costs：A CNY 750.00、B CNY 600.00、A USD 100.00。  
Employee costs：PM002 200.00、普通成员 130.00；公共费用 A CNY 650.00 / B CNY 400.00 / A USD 100.00。  
Resource type：UNBOUND CNY 1280.00、GATE5-AI CNY 100.00、UNBOUND USD 100.00。

## boss

HTTP 200。Overview / Trend / Project / Employee 与 admin **同范围同数值**。无写入口（Statistics 只读）。

## pm

HTTP 200。Overview：

```json
{
  "amounts_by_currency": { "CNY": "750.00", "USD": "100.00" },
  "project_count": 1
}
```

Project costs 仅 Project A。无 Project B。  
Employee costs 仅普通成员 100.00（A 上的直接分摊）；不见 PM002 200。  
Resource status：ACTIVE 5，IDLE 0，UNASSIGNED_ACTIVE 0，EXPIRING_SOON 0（全局闲置/未分配资源不在 PM ResourceScope）。

## member

Overview：

```json
{
  "amounts_by_currency": { "CNY": "130.00" },
  "my_project_count": 1,
  "my_resource_count": 4,
  "my_expiring_resource_count": 0
}
```

无 `project_count` / `employee_count` / 公司总费用。无 USD。  
`GET /api/statistics/project-costs` → **403** `没有权限`  
`GET /api/statistics/employee-costs` → **403** `没有权限`  
Resource type：GATE5-AI 100.00、UNBOUND 30.00。

## 结论

| 规则 | 结果 |
| --- | --- |
| ADMIN GLOBAL | PASS |
| BOSS GLOBAL READ 同范围 | PASS |
| PM 仅负责项目份额 | PASS |
| MEMBER 仅本人直接费用 | PASS |
| MEMBER 排行 403 | PASS |
| VOIDED 不计 | PASS |
| 共享费用按 Distribution | PASS |
| employee-only 不反推项目 | PASS |

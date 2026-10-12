# Gate 4 Expense Scope Verification

日期：2026-09-22  
方式：对运行中的后端 `http://127.0.0.1:8010` 使用真实账号登录并调用 API  
脚本：`backend/app/scripts/verify_gate4_scope.py`

不能只做代码检查。以下为真实返回摘要。

## 账号

| 用户名 | 角色 | Scope | employee_id | 姓名 |
| --- | --- | --- | --- | --- |
| admin | ADMIN | GLOBAL | 1 | 系统管理员 |
| boss | BOSS | GLOBAL | 2 | 老板 |
| pm | PROJECT_MANAGER | MANAGED_PROJECTS | 3 | 项目负责人 |
| member | MEMBER | MEMBER_PROJECTS | 4 | 普通成员 |

密码均来自当前 `.env` 示例值，未写入本报告。

## 准备数据

Project A = `GATE2-A`，负责人 pm，成员含 member 与 MB002。  
Project B = `GATE2-B`，负责人 PM002，pm / member 未负责、未加入。

| 标记 | description | amount | 分摊 |
| --- | --- | --- | --- |
| A | GATE4-A | 100 | Project A / member |
| B | GATE4-B | 200 | Project B / PM002 |
| D | GATE4-D | 300 | Project A / MB002 |
| E | GATE4-E-SHARED | 1000 | Project A 60% + Project B 40% |

本次运行 A 的 id = 8（脚本按 description 查找；历史 id=1 曾被 ADMIN PUT 改写说明）。B=2，D=3，E=4。

## GET /api/expenses

### admin

HTTP 200。可见全部费用，金额为原额。

含 A/B/D/E 及分摊验证、周期生成记录。`PUT A` → **200**。

```json
{
  "status": 200,
  "GET A": { "amount": "100.0000", "original_amount_visible": true },
  "GET B": { "amount": "200.0000" },
  "GET D": { "amount": "300.0000" },
  "GET E": {
    "amount": "1000.0000",
    "distribution_project_ids": [1, 2]
  },
  "PUT A": { "status": 200 }
}
```

### boss

HTTP 200。列表与详情与 admin 同范围。`PUT A` → **403** `没有权限`。

```json
{
  "GET A": { "amount": "100.0000", "original_amount_visible": true },
  "GET E": { "amount": "1000.0000", "distribution_project_ids": [1, 2] },
  "PUT A": { "status": 403, "detail": "没有权限" }
}
```

### pm

HTTP 200。列表**不含 B**。共享费用 E 的列表/详情金额为 **600.0000**（仅 Project A 份额），`original_amount_visible=false`，分摊只返回 project_id=1。D 可见（负责项目上的他人成员份额）。写 403。

```json
{
  "GET /api/expenses amounts (E, D excerpt)": ["600.0000", "300.0000"],
  "GET B": { "status": 404, "detail": "费用不存在" },
  "GET E": {
    "status": 200,
    "amount": "600.0000",
    "visible_allocated_amount": "600.0000",
    "original_amount_visible": false,
    "distribution_project_ids": [1]
  },
  "PUT A": { "status": 403 }
}
```

PM 看不到 Project B 的 400 分摊行，也不能看到 1000 原额。

### member

HTTP 200。只看见直接分摊给自己的 A（100）。B / D / E 均为 **404**。写 403。

```json
{
  "GET A": {
    "status": 200,
    "amount": "100.0000",
    "original_amount_visible": false,
    "distribution_employee_ids": [4]
  },
  "GET B": { "status": 404 },
  "GET D": { "status": 404 },
  "GET E": { "status": 404 },
  "PUT A": { "status": 403 }
}
```

MEMBER 看不到同项目 MB002 的 300，也看不到仅项目级共享的 1000。

## 结论

| 规则 | 结果 |
| --- | --- |
| ADMIN 全局读写 | PASS |
| BOSS 全局只读 | PASS |
| PM 只读负责项目份额 | PASS |
| MEMBER 只读本人直接分摊 | PASS |
| 越权 404 | PASS |
| 筛选不得扩大 Scope | 由 `test_expense_security.py` 覆盖，PASS |
| 后端 Scope 为真实边界 | PASS |

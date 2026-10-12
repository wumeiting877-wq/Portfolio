# Gate 2 Scope Verification

日期：2026-09-22  
方式：对运行中的后端 `http://127.0.0.1:8010` 使用真实账号登录并调用 API  
脚本：`backend/app/scripts/verify_gate2_scope.py`

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

Project A

```text
id = 1
project_code = GATE2-A
manager_employee_id = 3   # pm 的 Employee
members = pm_employee + member_employee
member_count = 2
```

Project B

```text
id = 2
project_code = GATE2-B
manager_employee_id = 45  # 另一负责人 PM002
members = 仅负责人
member 未加入
```

## GET /api/projects

### admin

HTTP 200。返回 GATE2-B、GATE2-A。

```json
{
  "ids": [2, 1],
  "codes": ["GATE2-B", "GATE2-A"]
}
```

### boss

HTTP 200。返回全部，与 admin 相同。

```json
{
  "ids": [2, 1],
  "codes": ["GATE2-B", "GATE2-A"]
}
```

### pm

HTTP 200。只返回自己负责的 Project A。

```json
{
  "ids": [1],
  "codes": ["GATE2-A"]
}
```

### member

HTTP 200。只返回自己参与的 Project A。

```json
{
  "ids": [1],
  "codes": ["GATE2-A"]
}
```

## GET /api/projects/{id}

| 角色 | Project A | Project B |
| --- | --- | --- |
| admin | 200 GATE2-A | 200 GATE2-B |
| boss | 200 GATE2-A | 200 GATE2-B |
| pm | 200 GATE2-A | 404 |
| member | 200 GATE2-A | 404 |

## PUT /api/projects/A（写探测）

| 角色 | HTTP | detail |
| --- | --- | --- |
| admin | 200 | 成功（description 被更新为探测值） |
| boss | 403 | 没有权限 |
| pm | 403 | 没有权限 |
| member | 403 | 没有权限 |

## 结论

- `GLOBAL`：admin / boss 看到 A+B
- `MANAGED_PROJECTS`：通过 `projects.manager_employee_id` 过滤，pm 只看到 A
- `MEMBER_PROJECTS`：通过 active `project_members` 过滤，member 只看到 A
- 后端拒绝越权详情与写操作；前端没有承担过滤职责

浏览器补充：

- member 项目列表只显示 GATE2-A，操作仅「查看」
- admin 项目列表显示 GATE2-A 与 GATE2-B，可见「新建项目 / 编辑 / 成员 / 归档」

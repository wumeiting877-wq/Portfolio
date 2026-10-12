# Gate 3 Resource Scope Verification

日期：2026-09-22  
方式：对运行中的后端 `http://127.0.0.1:8010` 使用真实账号登录并调用 API  
脚本：`backend/app/scripts/verify_gate3_scope.py`

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

Resource A = `GATE3-A`

```text
id = 1
allocation: Project A / member(employee_id=4)
```

Resource B = `GATE3-B`

```text
id = 2
allocation: Project B / 另一负责人 PM002
```

Resource C = `GATE3-C`

```text
id = 3
未分配
```

Resource D = `GATE3-D`

```text
id = 4
allocation: Project A / 同项目另一成员 MB002
```

Project A 由 pm 负责，member 与 MB002 均为成员。  
Project B 由 PM002 负责，member 未加入。

## GET /api/resources

### admin

HTTP 200。返回 D/C/B/A。

```json
{
  "ids": [4, 3, 2, 1],
  "names": ["GATE3-D", "GATE3-C", "GATE3-B", "GATE3-A"]
}
```

### boss

HTTP 200。返回全部，与 admin 相同。

```json
{
  "ids": [4, 3, 2, 1],
  "names": ["GATE3-D", "GATE3-C", "GATE3-B", "GATE3-A"]
}
```

### pm

HTTP 200。只返回 Project A 相关 A/D。看不到 B 和未分配 C。

```json
{
  "ids": [4, 1],
  "names": ["GATE3-D", "GATE3-A"]
}
```

### member

HTTP 200。只返回直接分配给自己的 A。看不到同项目他人 D，也看不到 B/C。

```json
{
  "ids": [1],
  "names": ["GATE3-A"]
}
```

## GET /api/resources/{id}

| 角色 | A | B | C | D |
| --- | --- | --- | --- | --- |
| admin | 200 | 200 | 200 | 200 |
| boss | 200 | 200 | 200 | 200 |
| pm | 200 | 404 | 404 | 200 |
| member | 200 | 404 | 404 | 404 |

## PUT /api/resources/A（写探测）

| 角色 | HTTP | detail |
| --- | --- | --- |
| admin | 200 | 成功 |
| boss | 403 | 没有权限 |
| pm | 403 | 没有权限 |
| member | 403 | 没有权限 |

## GET /api/resources/A/allocations

member 仅看到 `employee_id=4`（自己）。  
同项目另一成员的 D 资源对 member 为 404，因此 member 无法读取他人账号分配。

## 结论

- `GLOBAL`：admin / boss 看到 A+B+C+D
- `MANAGED_PROJECTS`：通过 active allocation.project_id 属于自己负责项目过滤，pm 只看到 A/D
- `MEMBER`：通过 active allocation.employee_id 过滤，member 只看到 A
- 后端拒绝越权详情与写操作；前端没有承担过滤职责

浏览器补充：

- member 资源列表只显示 GATE3-ChatGPT-Team-01、GATE3-GitHub-Seat、GATE3-A，操作仅「查看」
- member 无「新建资源 / 资源类型 / 使用人」
- admin 资源列表显示全部 7 条，可见「新建资源 / 资源类型 / 编辑 / 分配 / 停用」

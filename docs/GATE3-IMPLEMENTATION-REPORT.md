# Gate 3 Implementation Report

阶段：Gate 3  
日期：2026-09-22  
结果：PASS

## GATE3 CURRENT STATE（实施前扫描）

对照真实仓库，不按文档假设。扫描完成后再实施 `G3-00 → G3-30`。

### 当前 Models

```text
roles
employees
users
audit_logs
projects
project_members
```

没有 `resource_types` / `resource_accounts` / `resource_allocations`。  
`ResourceAccount` 不存在 `project_id` / `employee_id` 单归属字段，也不存在费用字段。

### 当前 Alembic head（实施前）

```text
0003_gate2_projects (head)
0002_gate1_identity
0001_gate0_baseline
```

没有 `0004`。

### 当前 Project Scope 实现

`backend/app/permissions/project_scope.py`

| 角色 | Scope | 读 | 写 |
| --- | --- | --- | --- |
| ADMIN | GLOBAL | 全部项目 | 是 |
| BOSS | GLOBAL | 全部项目 | 否 |
| PROJECT_MANAGER | MANAGED_PROJECTS | `manager_employee_id == current_user.employee_id` | 否 |
| MEMBER | MEMBER_PROJECTS | active `project_members` | 否 |

没有 `resource_scope.py`。

### 当前 API

```text
/health /health/db
/api/auth/*
/api/employees
/api/users
/api/roles
/api/projects
/api/projects/{id}/members
```

没有 `/api/resource-types`、`/api/resources`、`/api/resource-allocations`。

### 当前前端 Router / Menu

路由：`/login` `/change-password` `/` `/projects` `/projects/:id` `/employees` `/users`  
菜单：首页、项目管理；人员管理（ADMIN/BOSS）；系统账号（ADMIN）  
没有「资源账号」菜单，没有 `/resources`。

### 当前测试数量

Gate 2 冻结：`55 passed`，强制 `project_cost_hub_test`。

### IBM UI 基础

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
frontend/src/styles/tokens.css
frontend/src/style.css
PageHeader.vue / StatusTag.vue / AdminLayout.vue
```

`tokens.css` 是 IBM-DESIGN 的代码实现层。

### Gate 3 需要修改的真实文件

新增：

```text
backend/app/models/resource_type.py
backend/app/models/resource_account.py
backend/app/models/resource_allocation.py
backend/alembic/versions/0004_gate3_resources.py
backend/app/schemas/resource.py
backend/app/repositories/resource_repository.py
backend/app/permissions/resource_scope.py
backend/app/services/resource_service.py
backend/app/api/resource_types/*
backend/app/api/resources/*
backend/tests/test_resource_*.py
frontend/src/api/resources.ts
frontend/src/views/resources/ResourceListView.vue
frontend/src/views/resources/ResourceDetailView.vue
```

修改：

```text
backend/app/models/enums.py
backend/app/models/__init__.py
backend/app/main.py
backend/app/services/audit_service.py
backend/tests/helpers.py
backend/tests/test_alembic_config.py
frontend/src/router/index.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/stores/auth.ts
frontend/src/components/StatusTag.vue
PROJECT-UI-CONSTRAINTS.md
```

### 与 Gate 3 文档存在的差异

1. `PROJECT-UI-CONSTRAINTS.md` 实施前禁止创建「资源管理」页面，并写「禁止修改 backend」。那是 UI 任务保护；Gate 3 是全栈任务。落地后已把 `/resources` 写入真实页面清单。
2. Gate 1 Service 直接查库；Gate 2 引入 `ProjectRepository`。Gate 3 沿用 Repository 模式新增 `ResourceRepository`，未回改 Gate 1/2。
3. Gate 1 审计 action 为 `create_employee` 等；Gate 3 按规格使用 `RESOURCE_*`。不改旧 action。
4. 资源类型管理规模很小，未强制独立 `/resource-types` 路由，而是在资源列表 Dialog 中管理。
5. `GET /api/resource-allocations` 仅 ADMIN/BOSS，符合规格“供全局检索”。
6. IBM-DESIGN 是营销站 Carbon 提取；后台壳层继续使用已校准 `tokens.css`，不另起视觉体系。

## 实施范围

完成资源类型、企业资源账号、资源分配、多人/跨项目共享，以及 Resource Scope。未开发金额、账单、费用分摊或 Dashboard。

## 完成项

| ID | 内容 | 状态 |
| --- | --- | --- |
| G3-00 | 扫描真实 Gate 2 代码与报告 | 完成 |
| G3-01 | ResourceType Model | 完成 |
| G3-02 | ResourceAccount Model | 完成 |
| G3-03 | ResourceAllocation Model | 完成 |
| G3-04 | Alembic `0004_gate3_resources` | 完成 |
| G3-05 | Resource Schemas | 完成 |
| G3-06 | Resource Repository | 完成 |
| G3-07 | Resource Service | 完成 |
| G3-08 | Resource Scope Service | 完成 |
| G3-09 | Resource Type API | 完成 |
| G3-10 | Resource Account API | 完成 |
| G3-11 | Allocation API | 完成 |
| G3-12 | Allocation 一致性规则 | 完成 |
| G3-13 | Shared Resource 规则 | 完成 |
| G3-14 | Audit | 完成 |
| G3-15 | Backend CRUD Tests | 完成 |
| G3-16 | Scope Tests | 完成 |
| G3-17 | Security Tests | 完成 |
| G3-18 | 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS | 完成 |
| G3-19 | Frontend API | 完成 |
| G3-20 | Router / Menu | 完成 |
| G3-21 | ResourceListView | 完成 |
| G3-22 | 新建/编辑 Resource | 完成 |
| G3-23 | ResourceDetailView | 完成 |
| G3-24 | Allocation UI | 完成 |
| G3-25 | Resource Type UI | 完成 |
| G3-26 | IBM UI Review | 完成 |
| G3-27 | npm run build | 完成 |
| G3-28 | pytest 全量回归 | 完成（92 passed，连续两次） |
| G3-29 | 四角色运行态取证 | 完成 |
| G3-30 | Gate 3 报告 | 完成 |

## 数据模型

新增：

```text
resource_types.code UNIQUE
resource_accounts.resource_type_id → resource_types.id
resource_allocations.resource_account_id → resource_accounts.id
resource_allocations.project_id 可空
resource_allocations.employee_id 可空
ck_resource_allocations_has_target: project_id 与 employee_id 不能同时为空
```

规则：

- 资源账号不绑定单一 Employee / Project
- 归属全部通过 `resource_allocations`
- 同一资源允许多条 active allocation（多人共享、跨项目）
- 同时指定项目+成员时，成员必须是该项目 active `project_member`
- 释放为逻辑释放：`is_active=false`，写 `released_at`
- 恢复可复用同一 allocation 记录
- 不保存 password / api_key / secret / token / credential
- 不保存 price / amount / cost / billing

计算字段：

- `is_expiring_soon`：`0 < expires_at - today <= 30`
- `is_shared`：`active_allocation_count > 1`
- `active_user_count` / `active_project_count`

## API

- `GET/POST /api/resource-types`
- `GET/PUT /api/resource-types/{id}`
- `POST /api/resource-types/{id}/disable|enable`
- `GET/POST /api/resources`
- `GET/PUT /api/resources/{id}`
- `POST /api/resources/{id}/disable|enable`
- `GET/POST /api/resources/{id}/allocations`
- `DELETE /api/resources/{id}/allocations/{allocation_id}`
- `POST /api/resources/{id}/allocations/{allocation_id}/restore`
- `GET /api/resource-allocations`（ADMIN/BOSS）

列表按当前用户 Resource Scope 在后端过滤。筛选参数不能扩大 Scope。

## Resource Scope

复用 `readable_projects()`，不复制 Gate 2 项目权限。

| 角色 | 可见资源 | 写 |
| --- | --- | --- |
| ADMIN | 全部 | 是 |
| BOSS | 全部 | 否 |
| PROJECT_MANAGER | active allocation.project_id 属于自己负责的项目 | 否 |
| MEMBER | active allocation.employee_id == 自己，且带项目时项目必须在自己的 member projects 中 | 否 |

MEMBER 的分配记录只返回自己的 allocation，看不到同项目其他成员。

## 前端

- 菜单「资源账号」对全部已登录角色显示
- `/resources` 列表 + 筛选 + 分页
- `/resources/:id` 仅「概览」「分配记录」
- ADMIN 可见新建/编辑/分配/停用/资源类型
- 其他角色只读
- MEMBER 不显示「使用人」筛选

## 结论

Gate 3 企业资源账号管理已落地，可以进入 Gate 4（费用与计费管理）。

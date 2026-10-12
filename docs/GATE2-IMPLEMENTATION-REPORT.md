# Gate 2 Implementation Report

阶段：Gate 2  
日期：2026-09-22  
结果：PASS

## GATE2 CURRENT STATE（实施前扫描）

对照真实仓库，不按文档假设。

### 文档差异

用户要求读取 `GATE2-PROJECT-SCOPE-IMPLEMENTATION.md`，仓库中不存在该文件名。真实规格是：

```text
企业项目资源与费用管理系统_Gate2_项目管理与真实Scope_开发执行文档.md
```

Gate 2 按该文件的 `G2-00 → G2-26` 实施。

### 当前前端结构（实施前）

```text
frontend/src/
  api/          auth.ts, employees.ts, users.ts, http.ts, health.ts
  components/   PageHeader.vue, StatusTag.vue
  layouts/      AdminLayout.vue
  stores/       auth.ts, user.ts
  styles/       tokens.css
  views/
    home/       HomeView.vue
    login/      LoginView.vue, ChangePasswordView.vue
    employees/  EmployeeListView.vue
    users/      UserListView.vue
  router/index.ts
  style.css
  main.ts
```

真实路由只有：`/login` `/change-password` `/` `/employees` `/users`。  
没有 `/projects`，菜单没有项目管理。

### 当前后端结构（实施前）

```text
backend/app/
  api/          health, auth, employees, users, roles
  models/       employee, user, role, audit_log, enums
  permissions/  roles.py, scopes.py, dependencies.py
  services/     auth, employee, user, role, audit
  repositories/ 仅空包说明，无真实 Repository
  scripts/      bootstrap.py, create_admin.py
```

没有 `projects` API、模型或 Scope 查询服务。

### 当前数据库模型

表：`roles` `employees` `users` `audit_logs`  
没有 `projects` / `project_members`。

### 当前 Alembic head（实施前）

```text
0002_gate1_identity (head)
```

### Auth / RBAC / Scope 实现位置

| 能力 | 位置 |
| --- | --- |
| JWT / 密码 | `backend/app/core/security.py` |
| 登录 / me | `backend/app/api/auth/router.py`, `services/auth_service.py` |
| 角色权限 | `backend/app/permissions/roles.py` |
| Scope 声明 | `backend/app/permissions/scopes.py`（仅 Enum → JWT / `/me`） |
| 依赖 | `backend/app/permissions/dependencies.py` |
| 人员/账号写权限 | `require_admin` / `require_admin_or_boss` |

Gate 1 已冻结：`ADMIN/BOSS/PROJECT_MANAGER/MEMBER`，Scope `GLOBAL/MANAGED_PROJECTS/MEMBER_PROJECTS`。真实项目过滤未接入。

### 当前测试结构

```text
backend/tests/
  conftest.py          直接 TestClient(app)，共用开发库
  helpers.py
  test_auth.py
  test_employees.py
  test_users.py
  test_roles.py
  test_security.py
  test_seeded_accounts.py
  test_health.py
  test_health_db.py
  test_app_skeleton.py
  test_alembic_config.py
```

Gate 1 已知问题：pytest 写入 `project_cost_hub`。

### 当前 IBM UI 基础文件

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
frontend/src/styles/tokens.css
frontend/src/style.css
PageHeader.vue / StatusTag.vue / AdminLayout.vue
```

`tokens.css` 是 IBM-DESIGN 的代码实现层，不是第二套 Design System。

### Gate 2 所需修改点

1. 独立测试库 `project_cost_hub_test`
2. `projects` / `project_members` + Alembic `0003`
3. Project 绑定 Employee，不绑定 User
4. `permissions/project_scope.py` 后端真实过滤
5. Project / Member API + Audit
6. 前端 `/projects` `/projects/:id`，详情仅概览/成员
7. 更新 `PROJECT-UI-CONSTRAINTS.md` 中的真实页面清单

### 与 Gate 2 文档不一致之处（已报告，未静默改业务）

1. 规格文件名不是 `GATE2-PROJECT-SCOPE-IMPLEMENTATION.md`。
2. `PROJECT-UI-CONSTRAINTS.md` 实施前禁止创建「项目管理」页面，并写「禁止修改 backend/database/API」。那是 UI 任务保护；Gate 2 是全栈任务。API 落地后已把 `/projects` 写入真实页面清单。
3. Gate 1 Service 直接查库，Repository 目录为空。Gate 2 按规格新增 `ProjectRepository`，未回改 Gate 1。
4. 人员列表无分页；项目列表按规格使用 `items/total/page/page_size`。
5. Gate 1 审计 action 为 `create_employee` 等；Gate 2 按规格使用 `PROJECT_CREATE` 等。不改 Gate 1 旧 action。
6. IBM-DESIGN 是营销站 Carbon 提取；后台壳层沿用已校准的 `tokens.css` 映射，不另起视觉体系。

## 实施范围

完成项目管理、项目负责人、项目成员，并把 `MANAGED_PROJECTS` / `MEMBER_PROJECTS` 接到真实数据库关系。未开发资源账号、费用、Dashboard。

## 完成项

| ID | 内容 | 状态 |
| --- | --- | --- |
| G2-00 | 独立 pytest 数据库 | 完成 |
| G2-01 | Project 数据模型 | 完成 |
| G2-02 | ProjectMember 数据模型 | 完成 |
| G2-03 | Alembic `0003_gate2_projects` | 完成 |
| G2-04 | Project Schema | 完成 |
| G2-05 | Project Repository | 完成 |
| G2-06 | Project Service | 完成 |
| G2-07 | Project Scope Service | 完成 |
| G2-08 | Project API | 完成 |
| G2-09 | Project Member API | 完成 |
| G2-10 | 负责人变更规则 | 完成 |
| G2-11 | Audit Log | 完成 |
| G2-12 | Scope 自动测试 | 完成 |
| G2-13 | CRUD 自动测试 | 完成 |
| G2-14 | 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS | 完成 |
| G2-15 | Project 前端 API | 完成 |
| G2-16 | Project Router | 完成 |
| G2-17 | 项目管理菜单 | 完成 |
| G2-18 | ProjectListView | 完成 |
| G2-19 | 新建/编辑项目 | 完成 |
| G2-20 | ProjectDetailView | 完成 |
| G2-21 | Project Members | 完成 |
| G2-22 | IBM UI 审计 | 完成 |
| G2-23 | npm run build | 完成 |
| G2-24 | pytest 全量回归 | 完成（55 passed，连续两次 + 最终一次） |
| G2-25 | 四角色真实运行验收 | 完成 |
| G2-26 | Gate 2 报告 | 完成 |

## 数据模型

新增：

```text
projects.manager_employee_id  → employees.id
project_members (project_id, employee_id) UNIQUE
```

规则：

- 一个项目一个主负责人
- 负责人是 Employee，不是 User
- 成员多对多，一人可参与多个项目
- 移除成员为逻辑退出（`is_active=false`，写 `left_at`）
- 项目删除语义为归档 `ARCHIVED`
- 负责人变更时自动保证新负责人在 `project_members` 中 active；原负责人不自动移除

## API

- `GET/POST /api/projects`
- `GET/PUT /api/projects/{id}`
- `POST /api/projects/{id}/archive`
- `GET/POST /api/projects/{id}/members`
- `PUT/DELETE /api/projects/{id}/members/{employee_id}`

列表按当前用户 Scope 在后端过滤，不返回全量再交给前端筛选。

## Scope

| 角色 | Scope | 读 | 写 |
| --- | --- | --- | --- |
| ADMIN | GLOBAL | 全部项目 | 是 |
| BOSS | GLOBAL | 全部项目 | 否 |
| PROJECT_MANAGER | MANAGED_PROJECTS | `projects.manager_employee_id == current_user.employee_id` | 否 |
| MEMBER | MEMBER_PROJECTS | active `project_members` | 否 |

过滤集中在 `backend/app/permissions/project_scope.py`。

## 前端

- 菜单「项目管理」对全部已登录角色显示
- `/projects` 列表 + 筛选 + 分页
- `/projects/:id` 仅「概览」「成员」
- ADMIN 可见新建/编辑/归档/添加/移除
- 其他角色只读

## 结论

Gate 2 项目管理与真实 Scope 已落地，可以进入 Gate 3（企业资源账号管理）。费用仍留 Gate 4。

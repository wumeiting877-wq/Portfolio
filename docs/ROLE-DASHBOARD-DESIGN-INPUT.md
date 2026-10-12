# 分角色看板设计输入

审计日期：2026-09-23  
范围：当前已实现的登录后首页 `/`（route name `home`）  
用途：交给后续设计，重做 ADMIN / BOSS / PROJECT_MANAGER / MEMBER 四种角色的看板  
本文件只记录已经存在的代码、路由、权限、接口和一次真实运行结果。未实现的能力不写成已实现。

本轮没有修改前端、后端、样式、路由、权限或数据。

---

## 1. 怎么核对的

| 核对方式 | 结果 |
|---|---|
| 阅读角色、路由、首页、统计接口与数据范围代码 | 已完成 |
| 开发环境 `http://127.0.0.1:8010` 与 `http://127.0.0.1:5173` | 当时均在运行。`GET /health`、`GET /health/db` 均为 `{"status":"ok"}` |
| 用现有账号登录 `admin`、`boss`、`pm`、`member`，调用 `/api/auth/me` 与首页实际会打的统计接口 | 四个账号均登录成功。口令不写入本文 |
| 浏览器打开已登录的 BOSS 首页 `http://127.0.0.1:5173/` | 已核对菜单、面包屑、标题、KPI、图表和表格 |
| 浏览器再登录 ADMIN / PROJECT_MANAGER / MEMBER | 未做。当时浏览器里已是 BOSS 会话；为保持只读，没有点击退出去切换账号 |

因此：

- BOSS 首页：代码 + 接口 + 浏览器实页。
- ADMIN / PROJECT_MANAGER / MEMBER 首页：代码 + 同一套运行中接口。页面上每个数字由 `HomeView.vue` 绑定这些接口。区块是否出现，由下面的模板条件决定，不是猜测。
- 这三份首页的像素级截图：未采集。

统计查询使用首页默认「本月」：`date_from=2026-09-01`，`date_to=2026-09-23`。数字是当时库里的开发/测试数据，会变。设计时应依赖字段和空态，不要把这些金额当成固定内容。

---

## 2. 后续看板设计必须遵守的约束

优先级以 `PROJECT-UI-CONSTRAINTS.md` 为准：

```text
真实业务
>
PROJECT-UI-CONSTRAINTS.md
>
IBM-DESIGN.md 视觉规则
>
Element Plus 默认样式
```

视觉最高规范是 `IBM-DESIGN.md`。代码落地是 `frontend/src/styles/tokens.css`，不是第二套设计系统。`IBM-DESIGN.md` 没有规定的部分，保持现有实现，不要另造规则。

和看板直接相关、已经写明的视觉约束：

- 字体 IBM Plex Sans。正文 16px / 字重 400 / 行高 1.50 / `letter-spacing: 0.16px`。14px 正文同样保留 `0.16px`。
- 大标题用字重 300，不要把标题加粗到 700。
- 唯一品牌色 IBM Blue `#0f62fe`。链接、主按钮、焦点线用它。不要把它铺成卡片底色，也不要再加第二种品牌色。
- 状态色只用文档里的绿 `#24a148`、黄 `#f1c21b`、红 `#da1e28`。
- 表面是白 `#ffffff` 与浅灰 `#f4f4f4`，字色 `#161616`，次级字 `#525252`，边线 `#e0e0e0`。
- 按钮、卡片、输入、容器圆角 0。不要胶囊按钮，不要投影，不要渐变面板。
- 层次靠 1px 边线和底色变化。
- 分区标签用句子大小写式的正常中文，不要全大写字距标签。
- 间距基准 4px。当前首页面板内边距是 16px（`--space-4`），不是营销页 feature card 的 24px。
- 顶栏高度 48px，与 Carbon `top-nav` 一致。当前左侧菜单宽 220px。
- 页头标题当前是 24px / 字重 400，对应 card-title，不是 42px 展示标题。

业务边界（设计不能改掉这些事实）：

- 角色 code 必须保持 `ADMIN`、`BOSS`、`PROJECT_MANAGER`、`MEMBER`。
- 首页数据由后端 Statistics Scope 过滤。前端隐藏区块不是安全边界。
- 费用按币种分别汇总，不跨币种相加。首页 KPI 已是「一种币种一行」。
- 系统登录账号和资源账号不是同一个东西。文案在语义不清时不要都叫「账号」。
- 不存在、也不要为看板补造「角色权限配置页」。
- 写操作目前只有 ADMIN。BOSS / PROJECT_MANAGER / MEMBER 的业务权限是读。看板本身没有新建、编辑、删除。
- 只有真实路由和真实 API 存在，才能在看板上增加对应入口或数字。

当前真实页面只有：

```text
/login
/change-password
/
/statistics
/projects
/projects/:id
/resources
/resources/:id
/expenses
/expenses/:id
/recurring-expenses
/employees
/users
/import-export
/notifications
/audit-logs
/settings
```

---

## 3. 真实角色体系

四种角色都存在，代码与运行中的 `/api/auth/me` 一致。

### 3.1 定义

| 项 | 位置 |
|---|---|
| 后端枚举 | `backend/app/models/enums.py` 的 `RoleCode` |
| 角色种子名称 | `backend/app/services/role_service.py` 的 `DEFAULT_ROLES` |
| 数据范围 | `backend/app/permissions/scopes.py` 的 `ROLE_SCOPES` |
| 动作权限 | `backend/app/permissions/roles.py` 的 `ROLE_PERMISSIONS` |
| 当前用户 | `backend/app/permissions/dependencies.py` 的 `get_current_user` |
| JWT | `backend/app/core/security.py` 的 `create_access_token` |
| 登录签发 | `backend/app/services/auth_service.py` 的 `issue_token` |
| `/api/auth/me` 字段 | `backend/app/schemas/auth.py` 的 `MeResponse` |
| 前端角色与菜单 | `frontend/src/config/roleUi.ts` |
| 前端路由 meta | `frontend/src/router/index.ts` |
| 前端会话 | `frontend/src/stores/auth.ts` |
| 顶栏显示名 | `frontend/src/stores/user.ts`，取 `employee_name`，否则 `username` |

`RoleCode`：

```text
ADMIN
BOSS
PROJECT_MANAGER
MEMBER
```

种子名称与范围：

| code | 库内 role.name | description | DataScope | 动作 |
|---|---|---|---|---|
| ADMIN | 系统管理员 | 全局读写 | GLOBAL | read, create, update, delete |
| BOSS | 老板 | 全局只读 | GLOBAL | read |
| PROJECT_MANAGER | 项目负责人 | 负责项目只读 | MANAGED_PROJECTS | read |
| MEMBER | 普通成员 | 参与项目只读 | MEMBER_PROJECTS | read |

另有项目成员角色 `ProjectMemberRole`：`PROJECT_MANAGER`、`MEMBER`。那是项目内成员身份，不是登录角色。

### 3.2 登录后角色从哪里来

1. `POST /api/auth/login` 成功后返回 `access_token` 和 `user.role_code`。
2. JWT payload 含 `user_id`、`username`、`role`、`scope`、`exp`。没有单独的 session 表字段被首页读取。
3. 之后每个请求用 Bearer token。`get_current_user` 用 token 里的 `user_id` 查库，**角色以数据库 `user.role.code` 为准**，不是只信任 JWT 里的 role 字符串。
4. `scope` 再按角色用 `scope_for_role()` 计算，不单独存成可被前端改写的权限。
5. 前端 `auth.fetchProfile()` 调用 `GET /api/auth/me`。`auth.role` 来自 `profile.role`。
6. token 存在 `localStorage.access_token`。

`/api/auth/me` 实际字段：

```text
id, username, role, role_name, scope, status, must_change_password, employee_id, employee_name
```

2026-09-23 四个现有账号：

| username | role | role_name | scope | employee_name | must_change_password |
|---|---|---|---|---|---|
| admin | ADMIN | 系统管理员 | GLOBAL | 系统管理员 | false |
| boss | BOSS | 老板 | GLOBAL | 老板 | false |
| pm | PROJECT_MANAGER | 项目负责人 | MANAGED_PROJECTS | 项目负责人 | false |
| member | MEMBER | 普通成员 | MEMBER_PROJECTS | 普通成员 | false |

演示账号由 `backend/app/scripts/bootstrap.py` 在 development/test 创建。本环境 `APP_ENV=development`，四个账号都已存在。

### 3.3 数据范围（看板数字的真实边界）

实现文件：

- 项目：`backend/app/permissions/project_scope.py`
- 资源：`backend/app/permissions/resource_scope.py`
- 费用与分摊：`backend/app/permissions/expense_scope.py`
- 统计汇总：`backend/app/repositories/statistics_repository.py`

| 角色 | 项目 | 资源 | 费用分摊 |
|---|---|---|---|
| ADMIN、BOSS | 全部项目 | 全部资源账号 | 全部有效分摊 |
| PROJECT_MANAGER | `manager_employee_id` 等于自己员工 id 的项目。没有员工档案则空 | 这些项目上、当前仍有效的资源分配所指向的资源 | 分摊到这些项目的费用 |
| MEMBER | 自己作为有效项目成员加入的项目 | 分配给自己、且项目为空或属于自己参与项目的有效分配 | 分摊到自己员工 id 的费用 |

统计金额一律来自 **状态为 ACTIVE 的费用记录上的分摊金额** `ExpenseDistribution.allocated_amount`，按 `ExpenseRecord.expense_date` 落入所选日期，再按 `ExpenseRecord.currency` 分组。作废费用不进入这些数字。

PROJECT_MANAGER 看不到自己不负责的项目。本次运行中，pm 看不到 Project B。MEMBER 的项目列表接口能看到自己加入的项目，但首页不调用项目费用排行。

### 3.4 前端权限开关（看板以外，但决定角色能点去哪里）

`frontend/src/stores/auth.ts`：

| getter | 为真的角色 |
|---|---|
| canWriteProjects / canWriteResources / canWriteExpenses / canWriteEmployees / canManageUsers / canImport / canWriteSettings | 仅 ADMIN |
| canViewEmployees / canViewRecurringExpenses / canViewAuditLogs | ADMIN、BOSS |
| canExport | 任一已登录角色 |
| canViewSettings | ADMIN、BOSS |

`canViewSettings` 与路由不一致，见第 8 节。菜单不读这些 getter，菜单只读 `roleUi.ts`。

写按钮出现在项目、资源、费用、人员等业务页，不出现在首页。

---

## 4. 登录后进入哪里

登录页：`frontend/src/views/login/LoginView.vue`，URL `/login`。  
登录成功后：`must_change_password` 为真则去 `/change-password`，否则 `router.push({ name: "home" })`，即 `/`。  
当前四个账号都不会被送去改密。  
未登录访问业务页会被送回 `/login`。已登录再打开 `/login` 会被送回 `home`。  
角色不在 `meta.roles` 里时，路由守卫 `return { name: "home" }`，没有独立的 403 页面。

浏览器标题始终是 `企业项目资源与费用管理系统`（`frontend/index.html`）。它不是看板名称。

壳层：`frontend/src/layouts/AdminLayout.vue`。

- 左上品牌：**项目费用中枢**
- 菜单：`menuItemsFor(auth.role)`
- 面包屑：`useBreadcrumb()`，文案来自 `roleUi.ts`
- 顶栏右侧：员工姓名；若 `role_name` 与员工姓名不同，再显示角色名；然后是「修改密码」「退出」
- 当前四个账号的员工姓名都等于 `role_name`，所以顶栏只显示姓名，不另显示角色。BOSS 实页顶栏是「老板」。

首页面包屑固定是两项：`首页`（链到 `home`）和当前看板标题（不可点）。  
`route name === "home"` 时，标题用 `dashboardTitle`，不用 `homeMenuLabel`。

| 角色 | 登录后 URL | route name | 页面组件 | 菜单第一项 | PageHeader | Breadcrumb |
|---|---|---|---|---|---|---|
| ADMIN | `/` | home | `frontend/src/views/home/HomeView.vue`，外包一层空壳 | 系统管理看板 | 系统管理看板 | 首页 / 系统管理看板 |
| BOSS | `/` | home | `HomeView.vue` 改为渲染 `BossDashboardShell.vue` | 经营总览 | 经营总览 | 首页 / 经营总览 |
| PROJECT_MANAGER | `/` | home | `HomeView.vue`，外包一层空壳 | 项目看板 | 项目看板 | 首页 / 项目看板 |
| MEMBER | `/` | home | `HomeView.vue`，外包一层空壳 | 我的工作台 | 我的资源 | 首页 / 我的资源 |

BOSS 的菜单、标题、面包屑已在浏览器看到：`首页 / 经营总览`，一级标题「经营总览」。

MEMBER 的菜单名和页头不是同一句：菜单是「我的工作台」，页头和面包屑当前项是「我的资源」。这是 `homeMenuLabel` 与 `dashboardTitle` 的现有差异。

### 4.1 各角色完整菜单

来源：`frontend/src/config/roleUi.ts` 的 `ROLE_UI` 与 `ROUTE_ROLES`。

ADMIN

```text
系统管理看板          /
统计分析              /statistics
项目管理              /projects
资源账号              /resources
费用管理              /expenses
周期规则              /recurring-expenses
人员管理              /employees
系统账号              /users
导入导出              /import-export
提醒中心              /notifications
审计日志              /audit-logs
系统设置              /settings
```

BOSS（浏览器已看到，没有「系统账号」「系统设置」）

```text
经营总览              /
统计分析              /statistics
项目管理              /projects
资源账号              /resources
费用管理              /expenses
周期规则              /recurring-expenses
人员管理              /employees
数据导出              /import-export
提醒中心              /notifications
审计日志              /audit-logs
```

PROJECT_MANAGER

```text
项目看板              /
项目统计              /statistics
我的项目              /projects
项目资源              /resources
项目费用              /expenses
数据导出              /import-export
提醒中心              /notifications
```

MEMBER

```text
我的工作台            /
我的统计              /statistics
我的项目              /projects
我的资源              /resources
我的费用              /expenses
数据导出              /import-export
提醒中心              /notifications
```

同一路由的菜单文案按角色不同。路由 path 相同。  
详情页不在菜单里：项目详情、资源详情、费用详情。它们的面包屑是 `首页 / 列表名 / 详情名`，详情名可被页面动态标题替换。

路由可见性：

| 路由 | 角色 |
|---|---|
| home、statistics、projects、project-detail、resources、resource-detail、expenses、expense-detail、import-export、notifications | 四种角色 |
| recurring-expenses、employees、audit-logs | ADMIN、BOSS |
| users、settings | 仅 ADMIN |

导入页所有角色都能打开路由，导入按钮只有 ADMIN。导出按数据集再限制角色，见 `frontend/src/api/exports.ts` 与 `backend/app/services/export_service.py`。

---

## 5. 首页现在到底是几套页面

文件：

```text
frontend/src/views/home/HomeView.vue
frontend/src/views/home/shells/index.ts
frontend/src/views/home/shells/AdminDashboardShell.vue
frontend/src/views/home/shells/BossDashboardShell.vue
frontend/src/views/home/shells/ProjectManagerDashboardShell.vue
frontend/src/views/home/shells/MemberDashboardShell.vue
```

实际结构：

- BOSS：独立模板 `BossDashboardShell.vue`，`data-dashboard="boss"`。不使用下面的共享版式。
- ADMIN / PROJECT_MANAGER / MEMBER：共用 `HomeView.vue` 里的同一段模板。三个 shell 只有 `data-dashboard` 属性和 `display: contents`，没有自己的标题、KPI 或图表。
- `dashboardShellFor()` 在角色无法识别时回退到 Admin shell。正常登录不会走到这里。

所以当前「分角色看板」的真实差异是：

1. BOSS 一套版式。
2. 其余三角色一套版式，用 `isMember`、`isPm`、`canRank` 开关区块。
3. 菜单名和页头文案按 `roleUi.ts` 变化。
4. 数字范围由后端 scope 变化，不是前端换一套假数据。

`canRank` = ADMIN、BOSS、PROJECT_MANAGER。MEMBER 不在其中。BOSS 虽然 `canRank` 为真，但走独立壳，不走共享模板里的排行图。

首页不调用提醒中心、审计、用户、设置、导入导出接口。那些是别的页面。

---

## 6. 首页数据从哪来

日期条：`frontend/src/utils/dateRange.ts`。默认 `month`（本月，从当月 1 日到今天）。还有近 3 个月、近 6 个月、今年、自定义。自定义在起止日期都选上之前不发请求。

金额格式：`formatMoney` → `CNY 7,232.50` 这种「币种代码 + 千分位两位小数」。没有币种时 KPI 显示「暂无费用」。

健康检查（只有共享模板页头右侧，BOSS 没有）：

| 显示 | 接口 |
|---|---|
| 后端 | `GET /health` |
| 数据库 | `GET /health/db` |

`status === "ok"` 时标签显示「正常」。失败显示「不可用」。本次两个接口都是 ok。

统计接口都在 `frontend/src/api/statistics.ts`，后端 `backend/app/api/statistics/router.py`。除 MEMBER 的项目排行和成员排行返回 403 外，其余统计 GET 只要登录即可，再由 scope 滤数据。

| 首页用途 | 方法 | 本次首页是否调用 |
|---|---|---|
| KPI | `GET /api/statistics/overview` | 四种角色都调用 |
| 费用趋势 | `GET /api/statistics/expense-trend` | 四种角色都调用 |
| 资源类型费用 | `GET /api/statistics/resource-type-costs?limit=5` | 四种角色都调用 |
| 资源状态、闲置、未分配 | `GET /api/statistics/resource-status` | 四种角色都调用。不传 days，后端用系统设置 `expiring_days`，默认 30 |
| 即将到期列表 | `GET /api/statistics/expiring-resources?days=30` | 四种角色都调用。天数写死 30，不读设置 |
| 项目费用 | `GET /api/statistics/project-costs` | ADMIN `limit=5`；BOSS `limit=6`；PROJECT_MANAGER `limit=5`；MEMBER 不调用。MEMBER 调用会 403，detail 为「没有权限」 |
| 成员费用与项目公共费用 | `GET /api/statistics/employee-costs?limit=5` | 仅 PROJECT_MANAGER 的首页调用。MEMBER 会 403。ADMIN、BOSS 的接口可用，但首页不调用 |
| 计费方式 / 费用类别 | `GET /api/statistics/billing-costs` | 仅 BOSS 的首页调用。接口对四种角色都返回 200，其他角色首页不调用 |
| 项目下拉 | `GET /api/projects?page=1&page_size=100` | 仅 PROJECT_MANAGER 的首页调用，且只有项目数大于 1 才显示下拉 |

`limit` 在后端是**每种币种保留前 N 条**，不是全局前 N 条。同一项目两种币种会成两行。

首页查询参数只有 `date_from`、`date_to`，以及 PROJECT_MANAGER 可选的 `project_id`。首页不传 `employee_id`。

### 6.1 overview 字段与首页是否展示

非 MEMBER 的响应（`response_model_exclude_none`，空字段不出现在 MEMBER 响应里）：

| 字段 | 含义 | 首页 |
|---|---|---|
| amounts_by_currency | 范围内有效分摊，按币种求和 | 展示。标签「本期费用」或 MEMBER 的「我的本期费用」 |
| project_count | 可见项目数 | ADMIN / BOSS / PM 展示为「项目数」 |
| employee_count | ADMIN/BOSS 且未按项目筛选时是全体员工数；否则是可见项目的有效成员加负责人 | 首页不展示。本次 admin/boss 为 47 |
| resource_count | 可见资源总数 | 首页不展示。统计页 KPI 用的是这个字段，标签「资源数」 |
| active_resource_count | 状态 ACTIVE | 展示为「活跃资源」 |
| idle_resource_count | 状态 IDLE | 与下一字段合成「闲置 / 未分配」 |
| unassigned_active_resource_count | 状态 ACTIVE 且没有有效分配 | 同上 |
| expired_resource_count | 状态 EXPIRED | 首页 KPI 不展示。资源状态表里有「已到期」 |
| expiring_soon_count | 到期日在今天之后、且在设置天数以内 | 展示为「即将到期」 |
| my_project_count | 仅 MEMBER | 展示为「我参与的项目」 |
| my_resource_count | 仅 MEMBER，取资源总数 total，不是仅 ACTIVE | 展示为「我的资源」 |
| my_expiring_resource_count | 仅 MEMBER | 展示为「即将到期」 |

### 6.2 其他对象字段

趋势点：`period`（`YYYY-MM`）、`currency`、`amount`。图例名是币种代码。没有该月数据的点为 null。

项目费用行：`project_id`、`project_name`、`currency`、`allocated_amount`。无项目的分摊不进这个排行。

成员费用行：`employee_id`、`employee_name`、`employee_no`、`currency`、`allocated_amount`。首页表格只用姓名和金额，不用工号。只统计分摊到具体员工的金额。

项目公共费用：`project_id`、`project_name`、`currency`、`allocated_amount`。分摊没有员工 id 的金额。PM 首页有数据才显示第二张表，并有一句「项目公共费用单独列出，不摊入成员。」

资源类型费用：`resource_type_id`、`resource_type_code`、`resource_type_name`、`currency`、`allocated_amount`。没有关联资源时，code 为 `UNBOUND`，名称是「未关联资源」（`statistics_repository.py`）。

计费结构：`billing_mode`、`category`、`currency`、`allocated_amount`。  
`billing_mode` 在 BOSS 表里用 `StatusTag kind="billing"`：周期、一次性、按量、手工。  
本次数据里的 category 是 `SOFTWARE`、`SUBSCRIPTION`，页面直接显示英文 code，没有中文映射。

资源简表：`id`、`resource_name`、`status`、`expires_at`、`resource_type_name`、`days_remaining`。  
资源状态中文：使用中、闲置、已到期、已停用；`EXPIRING_SOON` 为「即将到期」。

资源状态计数 `counts`：`ACTIVE`、`IDLE`、`EXPIRED`、`DISABLED`、`EXPIRING_SOON`、`UNASSIGNED_ACTIVE`。另有 `explicit_idle_count`、`unassigned_active_count`、`idle_resources`、`unassigned_active_resources`。列表默认最多 20 条。即将到期列表最多 100 条。

---

## 7. 四种角色首页现在展示什么

### 7.1 共用交互

- 时间范围五个选项：本月、近 3 个月、近 6 个月、今年、自定义。
- 改范围会重新请求。首页没有单独的查询按钮。
- 图表组件 `IbmChart`。没有类目或没有数值时显示空态标题，不画空坐标轴。
- 首页没有筛选币种、没有导出、没有提醒未读数、没有待办审批。当前系统也没有审批流页面。

### 7.2 BOSS：经营总览

浏览器实页已核对。组件 `BossDashboardShell.vue`。  
PageHeader 只有标题「经营总览」，没有说明文字，没有后端/数据库状态。

自上而下：

1. 时间范围。
2. KPI 五行固定列：本期费用、项目数、活跃资源、闲置 / 未分配、即将到期。  
   本次实页：`CNY 7,232.50` 与 `USD 100.00`；项目数 `3`；活跃资源 `11`；闲置 / 未分配 `1 / 3`；即将到期 `1`。
3. 「费用趋势」折线图，高 220px。空态「当前时间范围暂无费用数据」。本次只有 `2026-09` 的 CNY 与 USD 两个点。
4. 左「项目成本」表：项目名（链接）、金额。  
   请求 6 条后再 `slice(0, 5)`。多于 5 行才出现「查看全部」，去 `/statistics`。  
   本次 4 行，没有「查看全部」：Project A CNY 3,856.66、Project B CNY 2,666.66、Project A USD 100.00、校验项目 CNY 12.50。  
   空态「当前时间范围暂无项目费用」。这里没有项目费用柱状图。
5. 右「费用结构」。有资源类型费用时只显示类型表（资源类型、金额）。没有类型费用、但有计费数据时，才改显示计费方式、类别、金额。两套都没有则「当前时间范围暂无费用数据」。  
   本次走的是类型表，不是计费表：未关联资源 CNY 7,132.50、Gate5 AI CNY 100.00、未关联资源 USD 100.00。  
   计费接口当时有 6 行，页面上看不到。
6. 左「资源状态」表，固定 6 行：使用中、闲置、未分配但仍使用中、即将到期、已到期、已停用。本次 11、1、3、1、0，已停用在模板中为 0。无数据时「当前没有资源数据」。
7. 右「需要关注」。三项都是 0 时显示「当前暂无需要关注的资源事项。」否则分段：
   - 「N 个资源将在 30 天内到期」，下列资源名和到期日。本次：GATE5-EXPIRING，2026-10-02。
   - 「N 个活跃资源尚未分配」，下列资源名。本次：GATE5-EXPIRING、GATE5-UNASSIGNED、GATE3-C。
   - 「N 个资源处于闲置状态」。本次：GATE5-IDLE。  
   不显示剩余天数，不显示资源类型。同一资源可以既出现在即将到期，又出现在未分配。

点击：

| 元素 | 去向 |
|---|---|
| 项目名 | `/projects/:id?tab=expenses` |
| 关注列表中的资源名 | `/resources/:id`（不带 tab） |
| 查看全部（多于 5 行项目成本时） | `/statistics` |

窄于 980px 时，左右两列改成上下单列。

### 7.3 ADMIN：系统管理看板

共享模板。页头说明：「统计数字来自当前权限范围内的有效费用分摊与资源分配。」  
页头右侧：后端、数据库健康标签。按本次健康接口，应为「正常」。浏览器未切到该账号，这一句是绑定推断。

区块顺序：

1. 时间范围。没有项目下拉。
2. KPI 与 BOSS 相同的五项。本次接口与 BOSS 相同：CNY 7,232.50、USD 100.00、项目 3、活跃资源 11、闲置/未分配 1/3、即将到期 1。KPI 列数随宽度自适应，不是 BOSS 那种写死 5 列。
3. 左「费用趋势」折线图，高 300px。空态「当前时间范围暂无费用数据」。
4. 右「资源状态」表，六行与 BOSS 相同。
5. 左「项目费用 Top 5」：柱状图（高 280px，类目最多 5 个项目名）加表格（项目链接、金额）。空态「当前时间范围暂无项目费用」。本次接口在 limit=6 时为 4 行，首页请求的是 limit=5，仍然是这 4 行。没有「查看全部」。
6. 右「资源类型费用 Top 5」：只有柱状图，没有类型明细表。空态「当前时间范围暂无资源类型费用」。
7. 「即将到期资源」表：资源、类型、状态、到期日、剩余天数。空态「当前没有即将到期资源」。本次 1 行 GATE5-EXPIRING / Gate5 AI / 使用中 / 2026-10-02 / 9。
8. 左「闲置资源」表：资源、类型。本次 GATE5-IDLE。
9. 右「未分配但仍使用中」表：资源、类型。本次 3 条。

不展示：成员费用、项目公共费用、计费方式、员工数、健康以外的系统管理指标。名字叫「系统管理看板」，内容仍是费用和资源统计，没有用户数、审计、设置、导入状态。

点击：

| 元素 | 去向 |
|---|---|
| 项目名 | `/projects/:id?tab=expenses` |
| 即将到期 / 闲置 / 未分配里的资源名 | `/resources/:id?tab=expenses` |

宽于 1024px：趋势区为 2:1，下面的图和表为两列。否则单列。

### 7.4 PROJECT_MANAGER：项目看板

同一共享模板，页头同样有说明和健康标签。标题「项目看板」。

与 ADMIN 的差别：

- 负责的项目多于 1 个时，时间条右侧出现下拉，占位「我的负责项目」，可清空。选项来自项目列表接口，最多取 100 条。选中后，首页统计请求带 `project_id`。  
  本次 pm 可见 2 个项目（Project A、校验项目），所以**按代码会显示这个下拉**。浏览器未切到该账号。
- 项目图标题是「我的项目费用」，不是「项目费用 Top 5」。
- 额外一节「项目成员费用」：柱状图（空态「当前没有成员直接费用」）加表格（成员名、金额）。有公共费用时再显示说明和「项目 / 公共费用」表。
- 不展示计费方式表，不展示「查看全部」。

本次接口（未选项目，本月）：

- KPI：本期费用 CNY 3,869.16、USD 100.00；项目数 2；活跃资源 6；闲置 / 未分配 0 / 0；即将到期 0。
- 趋势：2026-09 的 CNY 3,869.16、USD 100.00。
- 我的项目费用：Project A CNY 3,856.66、Project A USD 100.00、校验项目 CNY 12.50。看不到 Project B。
- 资源类型：未关联资源 CNY 3,769.16、Gate5 AI CNY 100.00、未关联资源 USD 100.00。
- 成员费用：普通成员 CNY 300.00、同项目另一成员 CNY 300.00、项目负责人 CNY 12.50。工号不显示。
- 公共费用：Project A CNY 3,256.66、Project A USD 100.00。
- 资源状态六行：使用中 6，其余 0。即将到期、闲置、未分配列表为空，空态文案会出现。

点击：项目去费用 tab；资源去资源费用 tab；成员名去 `/expenses?employee_id=`。

`employee_count` 本次为 3，首页不展示。

### 7.5 MEMBER：我的资源

同一共享模板。菜单是「我的工作台」，页头是「我的资源」。有说明和健康标签。没有项目下拉。

展示：

1. KPI 四项：我的本期费用、我参与的项目、我的资源、即将到期。  
   本次：CNY 330.00；项目 2；资源 4；即将到期 0。没有 USD。
2. 费用趋势。本次一个月一个 CNY 点。
3. 资源状态六行。本次使用中 4，其余 0。MEMBER 看得到这张表。
4. 「我的资源类型费用」柱状图，单独占满一行，没有旁边的项目图。本次：未关联资源 CNY 230.00、Gate5 AI CNY 100.00。
5. 即将到期资源表。本次空。

不展示：项目费用、成员费用、公共费用、闲置表、未分配表、计费结构。  
overview 也不返回 `project_count`、`employee_count`、`active_resource_count` 这些非 MEMBER 字段。

「我的资源」KPI 用的是可见资源总数。本次与状态里的「使用中 4」相同，因为没有闲置或停用。字段含义并不总是「仅使用中」。

点击：即将到期资源去 `/resources/:id?tab=expenses`。

项目列表接口本次返回 2 个项目（校验项目、Project A），但首页不用这个接口。

---

## 8. 首页没有用、但系统里已经存在的数据

这些不是首页缺口方案，只是避免把它们当成首页已有模块，或当成完全不存在。

| 已有能力 | 首页现状 |
|---|---|
| `/statistics` 统计分析 | 独立页面。角色标题：统计分析 / 项目统计 / 我的统计。有 Top 10 / Top 20，有趋势、项目、成员、资源类型、费用类型、资源状态等 tab。MEMBER 只有「我的费用」「我的资源」两个 tab。首页不是这个页面的缩小复制 |
| employee-costs | ADMIN、BOSS 接口 200，首页不画。MEMBER 403 |
| billing-costs | 四种角色接口都 200。只有 BOSS 首页请求它，而且只要存在资源类型费用就被盖住 |
| employee_count、resource_count、expired_resource_count | overview 有，首页 KPI 不用 |
| 提醒中心 `/notifications` | 四种角色菜单都有。首页不显示未读或提醒列表。即将到期来自统计接口，不是通知接口 |
| 周期规则、人员、审计 | ADMIN 与 BOSS 有菜单。首页不摘要 |
| 系统账号 | 仅 ADMIN 菜单。首页不摘要 |
| 系统设置 | 前端路由仅 ADMIN。后端 `GET /api/settings` 允许 ADMIN 和 BOSS，`PUT` 仅 ADMIN。BOSS 的 `canViewSettings` 为真，但菜单和路由都进不去，会被送回首页。设置里的 `expiring_days` 默认 30 |
| 导入导出 | 首页无入口摘要。BOSS / PM / MEMBER 菜单文案是「数据导出」，ADMIN 是「导入导出」 |

首页项目图的类目用项目名去重后最多 5 个；表格仍是「每种币种最多 5 行」。多币种时，图和表的行数可以不一致。BOSS 没有这个柱状图，表是先取每种币种 6 行再砍到 5 行，因此「查看全部」只在返回超过 5 行时出现，不是服务端总数。

资源状态接口的「即将到期」天数跟随系统设置；首页到期列表写死 `days=30`。设置若被改成不是 30，KPI 的即将到期人数和列表可能不一致。当前默认仍是 30，本次两边都是 1（BOSS/ADMIN）或 0（PM/MEMBER）。

`GET /api/statistics/resource-status` 的 counts 含 `EXPIRING_SOON`，但它统计的是「到期日落在窗口内」，不要求状态字段本身等于某个 EXPIRING 枚举。状态列仍可能显示「使用中」。本次 GATE5-EXPIRING 的 status 就是 `ACTIVE`。

---

## 9. 给后续设计的事实边界

可以当作已实现、并且有真实数据的：

- 四种登录角色、四种数据范围、登录后都进 `/`。
- 一套共享首页（ADMIN、项目负责人、成员）和一套老板首页。
- 时间范围、分币种费用、费用月趋势、资源状态计数、资源类型费用、即将到期列表。
- 老板的项目成本表、费用结构表、需要关注列表。
- 管理员和项目负责人的项目费用图和表、闲置表、未分配表。
- 项目负责人的成员费用和项目公共费用，以及多于一个负责项目时的项目筛选。
- 成员的四项个人 KPI 和「我的资源类型费用」。
- 从首页点进项目费用、资源费用，或从成员点进费用列表。老板的资源链接不带费用 tab。

不要写成首页已经有的：

- 四套完全不同的看板布局。除老板外，三个 shell 是空的。
- 老板页上的计费方式结构。代码有回退，当前数据下不出现。
- 老板页上的「查看全部」。代码有，当前不足 6 行，实页没有这个按钮。
- 管理员首页上的用户、审计、设置、导入健康、员工总数。
- 成员首页上的项目排行、成员排行、闲置和未分配名单。
- 提醒未读、审批、预算、同比、目标、告警规则。代码里没有这些首页模块。
- 跨币种合计。
- 把「未关联资源」当成一种真实资源类型主数据。它是统计桶，`resource_type_id` 为 null。

设计若要新增首页模块，只能绑定已经存在的路由和 API，或明确标成尚未实现。视觉仍以 `IBM-DESIGN.md` 为最高规范，业务范围仍以后端 scope 为准。

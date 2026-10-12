# Gate 5 Implementation Report

阶段：Gate 5  
日期：2026-09-22  
结果：PASS

## GATE5 CURRENT STATE（实施前扫描）

对照真实仓库，不按文档假设。扫描完成后再实施 `G5-00 → G5-32`。  
来源：Gate 4 冻结代码与报告。

### 当前 Models

```text
roles
employees
users
audit_logs
projects
project_members
resource_types
resource_accounts
resource_allocations
expense_types
expense_records
expense_distributions
recurring_expense_rules
recurring_rule_distributions
```

没有 statistics 事实表。`ResourceAccount` 仍无 `price` / `monthly_cost`。

### 当前 Alembic head（实施前）

```text
0005_gate4_expenses (head)
```

没有 `0006`。

### Project / Resource / Expense Scope

| 角色 | Project | Resource | Expense |
| --- | --- | --- | --- |
| ADMIN | GLOBAL + WRITE | 全部 + WRITE | 全部 + WRITE |
| BOSS | GLOBAL + READ | 全部 + READ | 全部 + READ |
| PROJECT_MANAGER | 负责项目 | 负责项目上的 active allocation | 负责项目 Distribution 份额 |
| MEMBER | 参与项目 | 本人 active allocation | 本人 employee_id 分摊 |

### ExpenseDistribution 真实结构

```text
expense_record_id
project_id            NULLABLE
employee_id           NULLABLE
allocation_method
allocation_ratio      NUMERIC(18,6)
allocated_amount      NUMERIC(18,4)
ck: project_id IS NOT NULL OR employee_id IS NOT NULL
```

已有单列索引：`project_id`、`employee_id`、`expense_record_id`。

### 当前是否已有 Statistics 能力

无。没有 `statistics_service` / `statistics_repository` / `/api/statistics/*`。

### 当前 API

```text
/health /health/db
/api/auth/*
/api/employees /api/users /api/roles
/api/projects
/api/resource-types /api/resources /api/resource-allocations
/api/expense-types /api/expenses /api/recurring-expense-rules
```

### 当前 HomeView

身份事实 + `/health` + `/health/db`。无 KPI、无趋势、无排行。

### 当前 Router / Menu

路由：`/login` `/change-password` `/` `/projects` `/projects/:id` `/resources` `/resources/:id` `/expenses` `/expenses/:id` `/recurring-expenses` `/employees` `/users`  
菜单：首页、项目管理、资源账号、费用管理、周期规则（ADMIN/BOSS）、人员管理（ADMIN/BOSS）、系统账号（ADMIN）  
没有 `/statistics`。

### 当前测试数量

Gate 4 冻结：`133 passed`，测试库 `project_cost_hub_test`。

### 当前 IBM UI 基础

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
frontend/src/styles/tokens.css
PageHeader.vue / StatusTag.vue / AdminLayout.vue
```

0px radius、1px hairline、Surface `#f4f4f4`、IBM Blue `#0f62fe`。无 chart token。

### Gate 5 实际需要新增 / 修改的文件

新增：

```text
backend/app/schemas/statistics.py
backend/app/repositories/statistics_repository.py
backend/app/services/statistics_service.py
backend/app/api/statistics/router.py
backend/tests/statistics_setup.py
backend/tests/test_statistics_*.py
backend/app/scripts/verify_gate5_statistics.py
frontend/src/api/statistics.ts
frontend/src/views/statistics/StatisticsView.vue
frontend/src/components/KpiStrip.vue
frontend/src/components/MoneyText.vue
frontend/src/components/EmptyState.vue
frontend/src/components/charts/IbmChart.vue
frontend/src/components/charts/chartTheme.ts
frontend/src/utils/money.ts
frontend/src/utils/dateRange.ts
```

修改：

```text
backend/app/main.py
backend/app/repositories/__init__.py
frontend/src/router/index.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/views/home/HomeView.vue
frontend/src/views/expenses/ExpenseListView.vue
frontend/src/styles/tokens.css
PROJECT-UI-CONSTRAINTS.md
```

### 与 Gate 5 文档存在的差异（实施前）

文档要求 Dashboard / Statistics；仓库首页仅为健康检查。  
文档允许 Alembic `0006` 增加复合索引；仓库单列索引已覆盖 `expense_date` / `status` / `currency` / `project_id` / `employee_id` / `is_active` / `expires_at`。  
ECharts 未安装。

---

## 实施后状态

### 统计口径

所有金额类统计：

```text
SUM(expense_distributions.allocated_amount)
JOIN expense_records
WHERE expense_records.status = ACTIVE
  AND expense_date 在 date_from / date_to
按 currency GROUP BY
```

- 项目费用只按 `distribution.project_id`
- 成员费用只按 `distribution.employee_id`
- 资源类型费用按 `ExpenseRecord.resource_account_id` → ResourceType；未绑定为 `UNBOUND`
- VOIDED 不计入
- Released allocation（`is_active=false`）不作为 active 关系
- 不新增统计事实表，无 `0006`

### API

```text
GET /api/statistics/overview
GET /api/statistics/expense-trend
GET /api/statistics/project-costs          MEMBER 403
GET /api/statistics/employee-costs         MEMBER 403
GET /api/statistics/resource-type-costs
GET /api/statistics/billing-costs
GET /api/statistics/resource-status
GET /api/statistics/expiring-resources
```

Scope 复用 `ProjectScope` / `ResourceScope` / `ExpenseScope`，无第四套 Scope。

### 前端

```text
/            Dashboard（角色化）
/statistics  详细统计（职责分离）
```

KPI 为 IBM 紧凑指标带。图表为 IBM Blue 折线 / 横向条形 SVG（未引入 ECharts 依赖）。无假曲线。金额 `tabular-nums` + 显式币种。

### 测试

连续两次 `docker compose exec backend pytest`：

```text
第一次：163 passed
第二次：163 passed
```

Gate 4 原 133 项保留。新增 30 项。测试库 `project_cost_hub_test`。  
`npm run build` PASS。

### 索引说明

未创建 `0006`。现有索引已覆盖统计过滤列，避免无意义迁移。

## G5-00 → G5-32

| ID | 内容 | 结果 |
| --- | --- | --- |
| G5-00 | 扫描 Gate 4 代码与报告 | PASS |
| G5-01 | 统计口径与多币种规则 | PASS |
| G5-02 | Statistics Repository | PASS |
| G5-03 | Statistics Service | PASS |
| G5-04 | Overview API | PASS |
| G5-05 | Expense Trend API | PASS |
| G5-06 | Project Cost API | PASS |
| G5-07 | Employee Cost API | PASS |
| G5-08 | Resource Type Cost API | PASS |
| G5-09 | Billing Cost API | PASS |
| G5-10 | Resource Status API | PASS |
| G5-11 | Expiring Resource API | PASS |
| G5-12 | Statistics Scope 校验 | PASS |
| G5-13 | Query 性能 / N+1 | PASS |
| G5-14 | 后端统计自动测试 | PASS |
| G5-15 | 多币种专项测试 | PASS |
| G5-16 | Scope / Security 测试 | PASS |
| G5-17 | 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS | PASS |
| G5-18 | Frontend Statistics API | PASS |
| G5-19 | Dashboard HomeView | PASS |
| G5-20 | Role-specific Dashboard | PASS |
| G5-21 | Expense Trend Chart | PASS |
| G5-22 | Project Ranking | PASS |
| G5-23 | Employee / Resource Type Ranking | PASS |
| G5-24 | Resource Status / Expiring | PASS |
| G5-25 | StatisticsView | PASS |
| G5-26 | Drill-down | PASS |
| G5-27 | IBM UI Review | PASS |
| G5-28 | npm run build | PASS |
| G5-29 | pytest 全量回归两次 | PASS |
| G5-30 | 四角色真实 Dashboard 取证 | PASS |
| G5-31 | 多币种运行态取证 | PASS |
| G5-32 | Gate 5 报告 | PASS |

## 冻结语义未回改

Gate 0–4 身份、Project/Resource/Expense Scope、分摊合计、周期幂等、金额 NUMERIC 均未改写。

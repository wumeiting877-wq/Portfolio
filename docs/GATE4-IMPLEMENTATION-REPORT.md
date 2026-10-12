# Gate 4 Implementation Report

阶段：Gate 4  
日期：2026-09-22  
结果：PASS

## GATE4 CURRENT STATE（实施前扫描）

对照真实仓库，不按文档假设。扫描完成后再实施 `G4-00 → G4-38`。  
来源：Gate 3 冻结代码与报告（`docs/GATE3-CLOSURE-REPORT.md` 等）。

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
```

没有 `expense_types` / `expense_records` / `expense_distributions` / `recurring_expense_rules` / `recurring_rule_distributions`。

`ResourceAccount` 仍是资源资产：无 `project_id` / `employee_id` 单归属字段，无 `price` / `monthly_cost` / `amount` / `cost`。

### 当前 Alembic head（实施前）

```text
0004_gate3_resources (head)
0003_gate2_projects
0002_gate1_identity
0001_gate0_baseline
```

没有 `0005`。

### 当前 Project Scope

`backend/app/permissions/project_scope.py`

| 角色 | Scope | 读 | 写 |
| --- | --- | --- | --- |
| ADMIN | GLOBAL | 全部项目 | 是 |
| BOSS | GLOBAL | 全部项目 | 否 |
| PROJECT_MANAGER | MANAGED_PROJECTS | `manager_employee_id == current_user.employee_id` | 否 |
| MEMBER | MEMBER_PROJECTS | active `project_members` | 否 |

### 当前 Resource Scope

`backend/app/permissions/resource_scope.py`

| 角色 | 可见资源 |
| --- | --- |
| ADMIN | 全部 |
| BOSS | 全部，只读 |
| PROJECT_MANAGER | 负责项目上的 active allocation 资源 |
| MEMBER | 直接分配给自己的资源；看不到同项目他人账号 |

没有 `expense_scope.py`。

### 当前 ResourceAllocation 结构

```text
resource_allocations
  resource_account_id  NOT NULL
  project_id           NULLABLE
  employee_id          NULLABLE
  allocated_at
  released_at
  is_active
  remark
  ck: project_id IS NOT NULL OR employee_id IS NOT NULL
```

支持项目级 / 成员级 / 项目+成员；释放与恢复为逻辑变更；资源不绑定单一 Employee / Project。

### 当前 API

```text
/health /health/db
/api/auth/*
/api/employees
/api/users
/api/roles
/api/projects
/api/projects/{id}/members
/api/resource-types
/api/resources
/api/resource-allocations
```

没有 `/api/expense-types`、`/api/expenses`、`/api/recurring-expense-rules`。

### 当前前端 Router / Menu

路由：`/login` `/change-password` `/` `/projects` `/projects/:id` `/resources` `/resources/:id` `/employees` `/users`  
菜单：首页、项目管理、资源账号；人员管理（ADMIN/BOSS）；系统账号（ADMIN）  
资源详情 Tab：概览、分配记录。**无费用 Tab。**  
没有「费用管理」「周期规则」菜单，没有 `/expenses`。

### 当前测试数量

Gate 3 冻结：`92 passed`，强制 `project_cost_hub_test`。

### IBM UI 基础

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
frontend/src/styles/tokens.css
frontend/src/style.css
PageHeader.vue / StatusTag.vue / AdminLayout.vue
```

0px radius、1px hairline、Surface `#f4f4f4` / Canvas `#ffffff`、IBM Blue `#0f62fe`。Dashboard 假 KPI 留 Gate 5。

### Gate 4 实际需要修改的文件

新增：

```text
backend/app/models/expense_type.py
backend/app/models/expense_record.py
backend/app/models/expense_distribution.py
backend/app/models/recurring_expense_rule.py
backend/app/models/recurring_rule_distribution.py
backend/app/core/money.py
backend/app/permissions/expense_scope.py
backend/app/schemas/expense.py
backend/app/repositories/expense_repository.py
backend/app/services/expense_service.py
backend/app/api/expense_types/router.py
backend/app/api/expenses/router.py
backend/app/api/recurring_expense_rules/router.py
backend/app/scripts/generate_recurring_expenses.py
backend/app/scripts/verify_gate4_scope.py
backend/app/scripts/verify_gate4_distribution.py
backend/app/scripts/verify_gate4_recurring.py
backend/alembic/versions/0005_gate4_expenses.py
backend/tests/test_expense_types.py
backend/tests/test_expenses.py
backend/tests/test_expense_distributions.py
backend/tests/test_expense_decimal.py
backend/tests/test_expense_scope.py
backend/tests/test_expense_security.py
backend/tests/test_recurring_expenses.py
frontend/src/api/expenses.ts
frontend/src/views/expenses/ExpenseListView.vue
frontend/src/views/expenses/ExpenseDetailView.vue
frontend/src/views/expenses/RecurringExpenseListView.vue
```

修改：

```text
backend/app/models/enums.py
backend/app/models/__init__.py
backend/app/main.py
backend/app/repositories/__init__.py
backend/tests/test_alembic_config.py
frontend/src/router/index.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/stores/auth.ts
frontend/src/components/StatusTag.vue
frontend/src/style.css
frontend/src/views/resources/ResourceDetailView.vue
frontend/src/views/projects/ProjectDetailView.vue
PROJECT-UI-CONSTRAINTS.md
```

### 与 Gate 4 文档存在的差异（实施前）

文档要求费用进入独立事实表，仓库当时完全没有费用层。  
文档要求 ResourceAccount 不得作为唯一费用事实；仓库已满足（无价格字段）。  
文档要求 Dashboard 留 Gate 5；仓库首页仅为健康检查与身份事实，无 KPI 卡。  
文档要求 Resource / Project 详情在真实费用 API 完成后才允许费用 Tab；实施前无该 Tab。

---

## 实施后状态

### Models

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

金额列全部 `NUMERIC(18,4)`（用量/单价/比例为 `NUMERIC(18,6)`）。禁止 Float。

### Alembic head（实施后）

```text
0005_gate4_expenses (head)
```

`down_revision = 0004_gate3_resources`。pytest session 仍 DROP SCHEMA 后完整迁移。

### Expense Scope

`backend/app/permissions/expense_scope.py`，复用 ProjectScope 判定 PM 负责项目。

| 角色 | 读 | 写 | 金额 |
| --- | --- | --- | --- |
| ADMIN | 全部费用与分摊 | 是 | 原额 + 全部分摊 |
| BOSS | 全部费用与分摊 | 否 | 原额 + 全部分摊 |
| PROJECT_MANAGER | 分摊 `project_id` 落在负责项目上的费用 | 否 | 仅可见份额；`original_amount_visible=false` |
| MEMBER | 分摊 `employee_id == self` 的费用 | 否 | 仅本人直接份额 |

筛选参数在 `readable_expenses` 之后叠加，不能扩大 Scope。越权详情返回 404。

### API

```text
/api/expense-types
/api/expenses
/api/expenses/{id}
/api/expenses/{id}/void
/api/expenses/suggested-distributions
/api/expenses/recurring/generate
/api/recurring-expense-rules
```

周期生成另提供：`python -m app.scripts.generate_recurring_expenses`。

### 前端 Router / Menu

```text
/expenses
/expenses/:id
/recurring-expenses          ADMIN / BOSS
```

菜单：费用管理（已登录）；周期规则（ADMIN/BOSS）。  
Resource Detail 增加「费用记录」Tab；Project Detail 增加「费用」Tab；均走真实 `GET /api/expenses`。首页无费用 KPI。

### 测试

连续两次 `docker compose exec backend pytest`：

```text
第一次：133 passed in 36.56s
第二次：133 passed in 39.61s
```

Gate 3 原 92 项全部保留。测试库 `project_cost_hub_test`。

---

## G4-00 → G4-38

| ID | 内容 | 结果 |
| --- | --- | --- |
| G4-00 | 扫描 Gate 3 代码与报告 | PASS |
| G4-01 | ExpenseType | PASS |
| G4-02 | ExpenseRecord，金额 NUMERIC，作废不删 | PASS |
| G4-03 | ExpenseDistribution，XOR 目标 + 金额 ≥ 0 | PASS |
| G4-04 | RecurringExpenseRule | PASS |
| G4-05 | RecurringRuleDistribution | PASS |
| G4-06 | Alembic `0005_gate4_expenses` | PASS |
| G4-07 | Pydantic schemas，Decimal | PASS |
| G4-08 | Expense Repository | PASS |
| G4-09 | 分摊合计必须等于 amount | PASS |
| G4-10 | Expense Service | PASS |
| G4-11 | Expense Scope | PASS |
| G4-12 | Expense Type API | PASS |
| G4-13 | Expense API | PASS |
| G4-14 | Recurring Rule API | PASS |
| G4-15 | Recurring Generator 幂等 | PASS |
| G4-16 | Distribution Validation | PASS |
| G4-17 | Decimal / 余数进第一份 | PASS |
| G4-18 | Audit | PASS |
| G4-19 | CRUD Tests | PASS |
| G4-20 | Distribution Tests | PASS |
| G4-21 | Recurring Idempotency Tests | PASS |
| G4-22 | Scope / Security Tests | PASS |
| G4-23 | 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS | PASS |
| G4-24 | Frontend Expense API | PASS |
| G4-25 | Router / Menu | PASS |
| G4-26 | ExpenseListView | PASS |
| G4-27 | 新增/编辑 Expense | PASS |
| G4-28 | ExpenseDetailView | PASS |
| G4-29 | Distribution UI | PASS |
| G4-30 | RecurringRule UI | PASS |
| G4-31 | Resource Detail 费用 Tab | PASS |
| G4-32 | Project Detail 费用 Tab | PASS |
| G4-33 | IBM UI Review | PASS |
| G4-34 | npm run build | PASS |
| G4-35 | pytest 全量回归两次 | PASS |
| G4-36 | 周期费用幂等运行态 | PASS |
| G4-37 | 四角色真实 Scope 取证 | PASS |
| G4-38 | Gate 4 报告 | PASS |

---

## 冻结语义未回改

- Gate 0 基线、健康检查、独立测试库不变。
- Gate 1 身份 / 角色 / 审计不变。
- Gate 2 Project Scope 语义不变。
- Gate 3 ResourceAccount 仍为资产；分配仍通过 ResourceAllocation；未在资源上增加 `price` / `monthly_cost` 作为唯一费用事实。
- 真实费用只进入 `ExpenseRecord`；归属只进入 `ExpenseDistribution`。

## 审计动作

```text
EXPENSE_TYPE_CREATE / UPDATE / ENABLE / DISABLE
EXPENSE_CREATE / UPDATE / VOID
EXPENSE_DISTRIBUTION_UPDATE
RECURRING_RULE_CREATE / UPDATE / ENABLE / DISABLE
RECURRING_EXPENSE_GENERATE
```

## 已知差异（实施后，相对文档字面）

- `RecurringRuleDistribution.allocated_amount` 可空：规则模板允许 RATIO，生成时再量化金额。
- `ExpenseSource` 预留 `IMPORT` / `API_SYNC`，本 Gate 无导入器。
- 等额分摊余数加在第一份：`1000 / 3 → 333.34, 333.33, 333.33`。
- 周期规则读写入口仅 ADMIN/BOSS（写仅 ADMIN），MEMBER / PM 无菜单。
- 开发库仍有 Gate 1 时期测试人员，ADMIN 成员筛选会看到这些工号。未顺手清理。

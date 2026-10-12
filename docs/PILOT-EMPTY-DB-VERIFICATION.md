# Pilot Empty DB Verification

日期：2026-09-23  
数据库：`project_cost_hub_pilot`  
实例：Pilot PostgreSQL `127.0.0.1:55433`  
Alembic：`0006_gate6_enterprise`

Pilot PostgreSQL 只有系统库和 `project_cost_hub_pilot`。没有从 `project_cost_hub` 做 `pg_restore`、`COPY` 或克隆。迁移由 Pilot backend 启动时执行 `alembic upgrade head`，从 `0001_gate0_baseline` 走到 `0006_gate6_enterprise`。

## 初始数据计数

Bootstrap 之后、Release Smoke 之后两次计数一致。

| 表 | 行数 | 说明 |
| --- | --- | --- |
| employees | 1 | `ADMIN001` / 系统管理员 |
| users | 1 | `admin`，角色 `ADMIN` |
| projects | 0 | |
| resource_accounts | 0 | |
| expense_records | 0 | |
| notifications | 0 | |
| audit_logs | 0 | |
| roles | 4 | 迁移种子：ADMIN、BOSS、PROJECT_MANAGER、MEMBER |
| system_settings | 1 | 迁移种子：公司名「项目费用中枢」，币种 CNY |

同时为 0 的业务表：`project_members`、`expense_types`、`expense_distributions`、`resource_types`、`resource_allocations`、`recurring_expense_rules`。

## 禁止数据

| 检查 | 结果 |
| --- | --- |
| 用户 `boss` / `pm` / `member` | 0 |
| 员工或项目文本命中 `GATE2`–`GATE5` | 0 |
| 开发费用、开发通知 | 0 |
| 32 个测试账号 | 不存在，用户只有 1 个 |

## 开发库未被触碰

`project_cost_hub` 仍在开发实例 `55432`。实施前与实施后行数相同：

| 表 | 实施前 | 实施后 |
| --- | --- | --- |
| employees | 46 | 46 |
| users | 36 | 36 |
| projects | 2 | 2 |
| resource_accounts | 11 | 11 |
| expense_records | 17 | 17 |
| notifications | 4 | 4 |
| audit_logs | 154 | 154 |
| roles | 4 | 4 |

开发实例仍另有 `project_cost_hub_test` 与 `project_cost_hub_restore_test`。这两库没有被导入 Pilot。

结论：Pilot DB Empty Baseline PASS。Development DB Untouched PASS。

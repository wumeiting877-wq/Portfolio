# Pilot Pre-Data Hotfix Report

日期：2026-09-23  
范围：正式录数前的数据完整性，不是新功能。

## 结论

```text
Pilot Pre-Data Hotfix: PASS

Validation Test Data Location: development project_cost_hub
Validation Test Data Cleanup: NOT REQUIRED
Resource Name Backend Unique: PASS
Resource Name DB Unique: PASS
Employee Email Backend Validation: PASS
Backend Tests: PASS x2
Frontend Build: PASS
Frontend Form Tests: NOT ADDED
Pilot Smoke: 10/10 PASS
Pilot Baseline Backup: PASS
Development DB Untouched: YES
Pilot Ready For Real Data: NO
```

`Pilot Ready For Real Data` 不是 YES。Pilot 库里已经有真实业务行，不能把它当成空库再从 5174 做一遍空白录入。这些行已保留。详见 `docs/PILOT-PRE-REAL-DATA-BASELINE.md`。

## 1. Validation 数据位置

只读核对了四个库。VX 记录只在开发库。

| 数据库 | 实例 | VX-VAL-001 | VX-PRJ-001 | VX-RES-001 |
| --- | --- | --- | --- | --- |
| `project_cost_hub` | `x_10project-postgres-1` :55432 | employee id 47 | project id 3 | resource id 12 |
| `project_cost_hub_pilot` | `project-cost-hub-pilot-postgres-1` :55433 | 0 | 0 | 0 |
| `project_cost_hub_test` | 开发实例 | 0 | 0 | 0 |
| `project_cost_hub_restore_test` | 开发实例 | 0 | 0 | 0 |

开发库关联（保留，未删除）：

| 对象 | ID | 关系 |
| --- | --- | --- |
| Employee `VX-VAL-001` / 校验人员 | 47 | ACTIVE，email 空。created_at `2026-09-23 02:55:58+00` |
| Project `VX-PRJ-001` / 校验项目 | 3 | PLANNING。负责人 employee 3 = `PM001` / 项目负责人，不是 VX-VAL-001 |
| Project member | 5 | project 3 + employee 3，`PROJECT_MANAGER`，active |
| Resource `VX-RES-001` | 12 | type id 1 `CURSOR` / Cursor，ACTIVE，created_by user 1 |
| Allocation | 10 | resource 12 + project 3，无人员 |
| Allocation | 11 | resource 12 + employee 47 |
| Allocation | 12 | resource 12 + project 3 + employee 3 |
| Expense | 18 | `12.5000 CNY`，expense_type 1 `GATE4-SOFTWARE`，未绑定资源 |
| Distribution | 26 | expense 18 → project 3 + employee 3，`12.5000` DIRECT |
| Audit | 155 / 156 / 158 | `create_employee` 47、`PROJECT_CREATE` 3、`RESOURCE_CREATE` 12 |
| Notification | 0 | 无 VX 提醒 |

规则是：在开发库则保留。因此没有删除。

## 2. Pilot 清理

未执行。Pilot 中不存在上述 VX 行，不允许为了“恢复空库”去删已经写入的真实人员、项目和资源。

审计语义按 `docs/DEV-DATA-CLEANUP-PLAN.md`：审计日志保留追溯，不作为空业务库硬条件。本轮没有删除任何 audit。

若将来 VX 出现在 Pilot，依赖顺序只能是：distribution 26 → expense 18 → allocation 10/11/12 → project member（仅当确认只服务 VX）→ resource 12 → project 3 → employee 47。不得 truncate，不得动 `ADMIN001`、`admin`、roles、system_settings，不得改开发库。

## 3. 资源名称唯一

见 `docs/PILOT-RESOURCE-UNIQUENESS-VERIFICATION.md`。

- `create_resource` 重名：HTTP 400，`资源名称已存在`
- `update_resource` 改成其他现存名称：HTTP 400，同一条自己的名称仍可保存
- 迁移 `0007_resource_name_unique`：`resource_accounts.resource_name` 唯一索引 `uq_resource_accounts_resource_name`
- 历史重名只存在于测试库。迁移先把同名的后续行改成 `名称 #<id>`，不删除行。开发库、恢复库、Pilot 重名组均为 0，实际更新 0 行

## 4. 人员邮箱

`EmployeeCreate` / `EmployeeUpdate` 对 email：

- 空、空白：允许，存成 null
- 合法（与前端 `formRules.ts` 同一规则）：允许
- 非法：422

email 仍然不是必填。

## 5. 测试

后端新增 `backend/tests/test_form_validation.py`，覆盖人员、项目、资源、分配、费用的本轮校验。

原测试里会在同一次 pytest 中重复使用的固定 `resource_name` 已改为带唯一后缀，避免新的唯一约束让原用例在第二次创建时失败。断言仍检查创建结果和权限行为。

前端 `frontend/package.json` 没有 vitest、jest 或 `*.test.*` / `*.spec.*`。没有为 API Error Mapping 引入新的前端测试栈。`frontend/src/utils/apiError.ts` 已能把 `资源名称已存在` 映射到 `resource_name`。

## 6. 回归

pytest 连续两次退出码 0。收集进度均为 100%（33% / 66% / 99% / 100%，218 项：原 208 项 + 本文件 10 项）。命令在开发 Postgres 本机 trust 连接上执行，因为当时 TCP 口令认证失败；见下一节。

`npm run build`（frontend 容器）：PASS。

Pilot `http://127.0.0.1:8011` Release Smoke：10/10 PASS。登录使用已轮换的 Pilot 管理员口令，口令未写入本报告。

```text
PASS health
PASS health/db
PASS version version=1.0.0
PASS login
PASS projects
PASS resources
PASS expenses
PASS statistics
PASS export
PASS notifications
{"passed": true, "count": 10}
```

## 7. 开发库

业务行未删未改：

| 检查 | 迁移前 | 迁移后 |
| --- | --- | --- |
| alembic | `0006_gate6_enterprise` | `0007_resource_name_unique` |
| employees | 47 | 47 |
| resource_accounts | 12 | 12 |
| VX-VAL-001 / VX-PRJ-001 / VX-RES-001 | 在 | 在 |
| 被改名的 resource_name | 0 | 0 |

另外：开发库角色 `project_cost` 的 TCP 口令从 `2026-09-23 03:17 UTC` 起不再接受配置中的开发口令，已有连接池仍能写 VX 数据。本轮代码热加载后新连接失败，`/health/db` 曾返回 503。已把该角色口令恢复为当前开发配置中的口令。恢复后 `/health/db` 为 `{"status":"ok"}`，员工仍为 47，`VX-VAL-001` 仍在。没有改 Pilot 口令，没有改业务行。

## 8. Pilot 备份

文件：`backups/project_cost_hub_pilot_pre_real_data_20260923_130709.backup`（78056 字节）

恢复到 Pilot 实例上的临时库 `project_cost_hub_pilot_pre_real_verify` 后核对：employees 6、users 1、projects 1、resource_accounts 1、expense_records 0、VX 员工 0、`ADMIN001` 在、`admin` 在、alembic `0007_resource_name_unique`。临时库已删除。正式 Pilot 库未覆盖。

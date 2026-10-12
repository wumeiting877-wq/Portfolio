# Pilot Pre-Real-Data Baseline

日期：2026-09-23  
数据库：`project_cost_hub_pilot`  
实例：`project-cost-hub-pilot-postgres-1`，端口 55433  
alembic：`0007_resource_name_unique`

本文件记录 hotfix 收口时的只读事实。Pilot 不是空业务库。下列真实行在本轮之前已经写入，本轮没有删除。

## 与“录数前空库”预期的差异

预期中的“真实业务人员 / 项目 / 资源 / 费用 = 0”不成立。VX 验证数据不在 Pilot，所以不能靠删除 VX 把库清回只剩 `ADMIN001`。

| 对象 | 预期空库 | 实际 |
| --- | --- | --- |
| employees | 1（ADMIN001） | 6 |
| users | 1（admin） | 1 |
| projects | 0 | 1 |
| project_members | 0 | 5 |
| resource_types | 0 | 2 |
| resource_accounts | 0 | 1 |
| resource_allocations | 0 | 1 |
| expense_types | 0 | 0 |
| expense_records | 0 | 0 |
| expense_distributions | 0 | 0 |
| notifications | 0 | 0 |
| audit_logs | 不要求为 0 | 17 |
| roles | 保留 | 4 |
| system_settings | 保留 | 1 |
| VX Validation Data | 0 | 0 |

## 系统账号

| 对象 | 值 |
| --- | --- |
| user | id 1，`admin`，ACTIVE，employee_id 1，role_id 1 |
| employee | id 1，`ADMIN001`，系统管理员，ACTIVE |
| roles | ADMIN、BOSS、PROJECT_MANAGER、MEMBER |

## 已存在的真实业务行

人员（除 ADMIN001）：

| id | employee_no | name |
| --- | --- | --- |
| 2 | wmt | 吴美婷 |
| 3 | gsj | 国书杰 |
| 4 | phx | 潘鸿秀 |
| 5 | fjh | 冯建辉 |
| 6 | hya | 何宇昂 |

项目：

| id | project_code | name | status | manager |
| --- | --- | --- | --- | --- |
| 1 | hwd | 海旺达 | ACTIVE | employee 5 `fjh` / 冯建辉 |

项目成员均为 active：冯建辉 PROJECT_MANAGER；何宇昂、吴美婷、国书杰、潘鸿秀 MEMBER。

资源类型：

| id | code | name | category | is_active |
| --- | --- | --- | --- | --- |
| 1 | gpt | GPT账号 | DEVELOPMENT | false |
| 2 | zh | 账号 | DEVELOPMENT | true |

资源：id 1，`GPT账号`，type 2，ACTIVE。created_at `2026-09-23 02:33:23+00`。  
分配：id 1，resource 1 + project 1 + employee 2（吴美婷），active。  
项目 created_at `2026-09-23 02:12:43+00`。

费用、费用类型、分摊、提醒：0。

审计 17 条，动作包括 `create_employee` ×5、`PROJECT_CREATE`、`PROJECT_MEMBER_ADD` ×5、`RESOURCE_TYPE_CREATE` ×2、`RESOURCE_TYPE_UPDATE`、`RESOURCE_TYPE_DISABLE`、`RESOURCE_CREATE`、`RESOURCE_ALLOCATION_ADD`。按现有语义保留。

`resource_name` 重名组：0。唯一索引 `uq_resource_accounts_resource_name` 已在。

## 备份

`backups/project_cost_hub_pilot_pre_real_data_20260923_130709.backup`

恢复验证库 `project_cost_hub_pilot_pre_real_verify` 与上表计数一致（employees 6、users 1、projects 1、resources 1、expenses 0、VX 0、ADMIN001、admin、alembic `0007_resource_name_unique`）。验证库已删除，正式库未覆盖。

## 下一步

不要把 Pilot 当成空库重新导入这 5 名人员和项目 `hwd`。继续录入时避开已有工号 `ADMIN001`、`wmt`、`gsj`、`phx`、`fjh`、`hya`，已有项目编码 `hwd`，已有资源名称 `GPT账号`。

# Pilot Resource Uniqueness Verification

日期：2026-09-23

## Duplicate Resource Name Audit

扫描时间在迁移之前。判定标准：`resource_accounts.resource_name` 完全相同（大小写敏感，与导入和前端精确匹配一致）。

| 数据库 | 实例 | 重名组 | 处理 |
| --- | --- | --- | --- |
| `project_cost_hub` | 开发 :55432 | 0 | 直接加唯一索引。更新 0 行 |
| `project_cost_hub_test` | 开发 :55432 | 13 | 见下方兼容策略。不删除行 |
| `project_cost_hub_restore_test` | 开发 :55432 | 0 | 未在该恢复库上执行迁移。重名为 0，将来 upgrade 不会改写行 |
| `project_cost_hub_pilot` | Pilot :55433 | 0 | 直接加唯一索引。`GPT账号` 仍在 |

测试库重名组（pytest 残留，固定名称被多次提交）：

| resource_name | 行数 |
| --- | --- |
| ChatGPT-Team-01 | 2 |
| Cursor-开发01 | 2 |
| Resource A | 9 |
| Resource B | 9 |
| Resource C | 9 |
| Resource D | 9 |
| 即将到期资源 | 27 |
| 已到期资源 | 27 |
| 已释放分配资源 | 27 |
| 显式闲置资源 | 27 |
| 未分配活跃资源 | 27 |
| 绑定资源 | 27 |
| 远期到期资源 | 27 |

测试库当时共 248 行资源账号。

## 兼容策略

不允许迁移在有历史重名时直接失败，也不删除重复资源。

`0007_resource_name_unique` 对同一 `resource_name` 保留最小 id，其余行改名为：

```text
left(resource_name, 200 - len(" #" + id)) || " #" || id
```

然后再删除非唯一索引 `ix_resource_accounts_resource_name`，创建唯一索引 `uq_resource_accounts_resource_name`。

在 `project_cost_hub_test` 的副本 `project_cost_hub_test_migration_check` 上验证：

| 检查 | 结果 |
| --- | --- |
| 迁移前行数 | 248 |
| 被改名的后续行 | 216 |
| 迁移后行数 | 248 |
| 迁移后重名组 | 0 |
| 唯一索引 | 已创建 |
| 删除行 | 0 |

副本库已删除。pytest 自己的 session 仍会 `DROP SCHEMA public` 再 `alembic upgrade head`，所以正式测试运行时这 216 行改名不会作用到业务库。

开发库与 Pilot 的重名组为 0，迁移后 `resource_name LIKE '% #%'` 在开发库为 0 行。Pilot 资源仍是 id 1 `GPT账号`。

## 服务边界

`create_resource`：名称已存在 → HTTP 400 `资源名称已存在`。  
`update_resource`：改成另一条现存名称 → HTTP 400；保持自己的名称 → 允许。  
并发下唯一索引冲突同样返回 HTTP 400 `资源名称已存在`。

导入创建资源走 `create_resource`，因此库内重名也会在提交时被拒绝。导入查找仍按 `resource_name` 精确匹配；唯一约束去掉同名歧义。

空白名称由 Schema 返回 422，不进入数据库。

## 已应用的库

| 数据库 | alembic |
| --- | --- |
| `project_cost_hub` | `0007_resource_name_unique` |
| `project_cost_hub_pilot` | `0007_resource_name_unique` |
| `project_cost_hub_test` | pytest 每次 session 升级到 head |
| `project_cost_hub_restore_test` | 仍是迁移前的恢复件，本轮未 upgrade |

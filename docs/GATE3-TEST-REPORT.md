# Gate 3 Test Report

日期：2026-09-22  
命令：`docker compose exec backend pytest`  
结果：92 passed（连续两次均为 92 passed）

## 测试库隔离

pytest 强制使用 `project_cost_hub_test`。

- 启动时若数据库名不含 `test`，直接 FAIL
- session 开始时 DROP SCHEMA + Alembic upgrade head + bootstrap
- 不写入开发库 `project_cost_hub`

隔离断言仍有效：

- `settings.POSTGRES_DB == project_cost_hub_test`
- engine URL database 不是 `project_cost_hub`
- 在测试库创建的工号，在开发库 `employees` 中不存在

连续运行：

```text
第一次：92 passed in 28.86s
第二次：92 passed in 29.77s
```

Gate 2 原 55 项测试全部保留且通过。

## 后端自动测试覆盖

### Isolation / Alembic

- pytest 使用独立 test DB
- `0004_gate3_resources.py` 存在
- 空 schema 可从 Gate 0 → Gate 1 → Gate 2 → Gate 3 完整迁移（session fixture）

### Resource Types

- ADMIN 创建 / 修改成功
- `code` 重复失败
- ADMIN 停用 / 启用成功
- BOSS / PM / MEMBER 写接口 403
- 登录用户可读 active 类型，不可见已停用类型
- `RESOURCE_TYPE_CREATE` / `UPDATE` / `DISABLE` 写入审计

### Resource Accounts

- ADMIN 创建 / 修改成功
- 无效 resource_type 失败
- 停用类型不能新建账号
- ADMIN 停用 / 启用成功
- 接口不返回 password / api_key / secret
- 创建请求携带 secret 字段 422
- 模型不存在明文 password / api_key / secret / token / credential
- 模型不存在 project_id / employee_id / price / amount / cost
- `is_expiring_soon` 按日期计算，筛选不扩大其他结果
- `RESOURCE_CREATE` / `UPDATE` / `DISABLE` 写入审计

### Allocations

- 项目级分配成功
- 成员级分配成功
- 项目+成员分配成功
- 同一资源可多人共享
- 跨项目共享成功
- 项目+成员不匹配时失败
- 项目与成员同时为空失败
- 释放成功且不再 active
- 恢复成功
- 再次 POST 同一目标会恢复历史记录
- `RESOURCE_ALLOCATION_ADD` / `RELEASE` / `RESTORE` 写入审计

### Scope / 越权

- ADMIN 看见 A/B/C/D 且可写
- BOSS 看见 A/B/C/D，写 403
- PROJECT_MANAGER 只看见 Project A 相关 A/D；B 与未分配 C 为 404；写 403
- MEMBER 只看见直接分配给自己的 A；看不到同项目他人 D；看不到 B/C；写 403
- MEMBER 传 `employee_id=其他人` 不能扩大结果
- PM 传 `project_id=其他项目` 不能扩大结果
- 猜测 resource id 不能越权
- 非 ADMIN 不能释放 allocation

## 前端构建

```text
docker compose exec frontend npm run build
vue-tsc -b && vite build  成功
```

产物包含 `ResourceListView` 与 `ResourceDetailView`。

## 运行时

Compose：

```text
backend   Up (healthy)   8010
frontend  Up             5173
postgres  Up (healthy)   55432
```

Alembic（开发库）：

```text
0004_gate3_resources (head)
```

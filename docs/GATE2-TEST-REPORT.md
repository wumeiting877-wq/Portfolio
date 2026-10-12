# Gate 2 Test Report

日期：2026-09-22  
命令：`docker compose exec backend pytest`  
结果：55 passed（连续两次 + 最终回归均为 55 passed）

## 测试库隔离

pytest 强制使用 `project_cost_hub_test`。

- 启动时若数据库名不含 `test`，直接 FAIL
- session 开始时 DROP SCHEMA + Alembic upgrade head + bootstrap
- 不写入开发库 `project_cost_hub`

隔离断言：

- `settings.POSTGRES_DB == project_cost_hub_test`
- engine URL database 不是 `project_cost_hub`
- 在测试库创建的工号，在开发库 `employees` 中不存在

连续运行：

```text
第一次：55 passed in 16.14s
第二次：55 passed in 16.00s
最终回归：55 passed in 15.71s
```

Gate 1 原 32 项测试全部保留且通过。

## 后端自动测试覆盖

### Isolation / Alembic

- pytest 使用独立 test DB
- `0003_gate2_projects.py` 存在
- 空 schema 可从 Gate 0 → Gate 1 → Gate 2 完整迁移（session fixture）

### Project CRUD

- ADMIN 创建 / 修改 / 归档成功
- `project_code` 重复失败
- 无效负责人 404
- 停用负责人 400
- 负责人自动进入 `project_members`，`member_role=PROJECT_MANAGER`
- `PROJECT_CREATE` / `PROJECT_UPDATE` / `PROJECT_ARCHIVE` 写入审计

### Project Members

- ADMIN 添加成员成功
- 同一成员不可重复 active 添加
- 逻辑移除成功，MEMBER 立即失去访问
- 重新加入后恢复权限
- 不能移除当前负责人
- 更换负责人后，原负责人仍为 active 普通成员，新负责人 Scope 立即生效
- `PROJECT_MEMBER_ADD` / `REMOVE` / `RESTORE` 写入审计

### Scope

- ADMIN 看见全部且可写
- BOSS 看见全部，写接口 403
- PROJECT_MANAGER 只看见自己负责的项目；另一项目 404；写 403
- MEMBER 只看见自己参与的项目；未参与项目 404；写 403
- 同一成员加入多个项目后可看到多个
- 查询参数 `employee_id` 不能扩大 Scope
- 猜测 project id 不能越权

## 前端构建

```text
docker compose exec frontend npm run build
vue-tsc -b && vite build  成功
```

## 运行时

Compose：

```text
backend   Up (healthy)   8010
frontend  Up             5173
postgres  Up (healthy)   55432
```

Alembic（开发库）：

```text
0003_gate2_projects (head)
```

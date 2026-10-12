# Gate 4 Test Report

日期：2026-09-22  
命令：`docker compose exec backend pytest`  
结果：133 passed（连续两次均为 133 passed）

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
第一次：133 passed in 36.56s
第二次：133 passed in 39.61s
```

Gate 3 原 92 项测试全部保留且通过。新增 41 项（含 `test_gate4_migration_file_exists`）。

## Alembic

- `0005_gate4_expenses.py` 存在
- `down_revision = 0004_gate3_resources`
- 开发库 `alembic current`：`0005_gate4_expenses (head)`
- 空 schema 可从 Gate 0 → 1 → 2 → 3 → 4 完整迁移（pytest session fixture）

## Expense Types

- ADMIN 创建 / 修改成功
- `code` 重复失败
- ADMIN 停用 / 启用成功
- BOSS / PM / MEMBER 写接口 403
- 登录用户可读 active 类型
- `EXPENSE_TYPE_CREATE` 写入审计

## Expense Records

- 周期订阅（MANUAL + 类型/计费）创建成功
- 一次性 `ONE_TIME` 创建成功
- API 按量 `USAGE`（quantity / unit / unit_price）创建成功
- 服务器类别 `SERVER` 创建成功
- 币种必填；金额为 Decimal 字符串，非 float
- 作废后默认列表不再出现有效记录；记录仍在库中
- `EXPENSE_CREATE` 写入审计
- ORM / 表金额列为 Numeric，不是 Float

## Distributions

- 项目级 DIRECT
- 成员级 DIRECT
- 项目+成员 DIRECT，且校验 active `project_member`
- 项目+成员不匹配失败
- 无目标（项目与成员皆空）失败
- EQUAL 等额
- RATIO 跨项目
- MANUAL 指定金额
- 合计不等于 `amount` → 400

## Decimal

- `0.1 + 0.2` 经 Decimal 路径不等于 float 漂移
- `1000 / 3` → `333.34, 333.33, 333.33`
- 等额分摊落库后合计等于原额

## Recurring

- MONTHLY 生成一条 ExpenseRecord + 分摊
- QUARTERLY / YEARLY 规则可创建
- 连续两次 generate 不重复出账
- 停用规则不生成
- `end_date` 已过不生成
- 非 ADMIN 调用 generate 403

## Scope / Security

- ADMIN 看见全部且可写
- BOSS 看见全部，写 403
- PM 只看见负责项目份额；跨项目费用只返回本项目 allocated；看不到 Project B 专属费用；写 403
- MEMBER 只看见直接分摊给自己的费用；同项目他人份额 404；共享项目级费用若无本人 employee 分摊则 404；写 403
- PM 用其他 `project_id` 筛选不能扩大 Scope
- MEMBER 用其他 `employee_id` 筛选不能扩大 Scope
- 猜测不存在/无权限费用 ID 返回 404，不是 403  enumeration 泄露写权限

## Frontend build

```text
docker compose exec frontend npm run build
vue-tsc -b && vite build  成功（7.36s）
```

产物含 `ExpenseListView`、`ExpenseDetailView`、`RecurringExpenseListView`。

## 运行态补充（非 pytest）

四角色真实登录取证见 `docs/GATE4-EXPENSE-SCOPE-VERIFICATION.md`。  
分摊合计见 `docs/GATE4-DISTRIBUTION-VERIFICATION.md`。  
周期幂等见 `docs/GATE4-RECURRING-IDEMPOTENCY-VERIFICATION.md`。

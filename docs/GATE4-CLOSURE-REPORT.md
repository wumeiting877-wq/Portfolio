# Gate 4 Closure Report

阶段：Gate 4  
日期：2026-09-22  
结论：CLOSED / PASS

## 验收对照

### 运行

- [x] frontend 正常打开
- [x] backend healthy
- [x] PostgreSQL healthy
- [x] `/health` 200 `{"status":"ok"}`
- [x] `/health/db` 200 `{"status":"ok"}`

### 数据库

- [x] `expense_types` 存在
- [x] `expense_records` 存在
- [x] `expense_distributions` 存在
- [x] `recurring_expense_rules` 存在
- [x] `recurring_rule_distributions` 存在
- [x] Alembic head = `0005_gate4_expenses`
- [x] 空库可完整迁移（pytest session：DROP SCHEMA 后 Gate 0 → 4）
- [x] 测试库独立：`project_cost_hub_test`

### 费用与计费

- [x] ResourceAccount 仍为资产，无 `price` / `monthly_cost` 作为唯一费用事实
- [x] 真实费用进入 ExpenseRecord
- [x] 归属进入 ExpenseDistribution
- [x] 项目 / 成员 / 项目+成员
- [x] 共享资源跨项目分摊
- [x] SUM(distributions) == amount
- [x] Decimal / NUMERIC，禁止 Float
- [x] 周期 / 一次性 / API 按量 / 服务器
- [x] 周期费用经 RecurringExpenseRule
- [x] 生成幂等，连续两次不重复出账
- [x] 作废保留历史，不物理删除

### Scope

- [x] ADMIN = GLOBAL + WRITE
- [x] BOSS = GLOBAL + READ
- [x] PROJECT_MANAGER = 负责项目份额 + READ
- [x] MEMBER = 本人直接分摊 + READ
- [x] PM / MEMBER 看不到无权限分摊细节
- [x] 后端过滤，前端不承担数据范围
- [x] 筛选参数不能扩大 Scope
- [x] 四类真实账号运行态取证通过
- [x] 分摊运行态取证通过
- [x] 周期幂等运行态取证通过

### 安全 / 审计

- [x] 金额与分摊修改写 Audit Log
- [x] 越权费用 404
- [x] 非 ADMIN 写 403

### 前端

- [x] 费用管理菜单真实存在
- [x] 周期规则菜单仅 ADMIN/BOSS
- [x] 列表 / 详情 / 规则走真实 API
- [x] Resource / Project 费用 Tab 真实 API
- [x] 无假 Dashboard / KPI 卡
- [x] IBM UI Review 完成
- [x] `npm run build` 成功

### 测试

- [x] Gate 3 原 92 tests 不退化
- [x] Gate 4 新测试全部 PASS
- [x] 连续运行 pytest 两次 PASS
- [x] 最终 133 passed

## 交付物

- ExpenseType / ExpenseRecord / ExpenseDistribution / RecurringExpenseRule / RecurringRuleDistribution 与 Alembic `0005`
- Expense Scope（复用 ProjectScope）
- 费用类型 / 费用 / 周期规则 API + Audit + 幂等生成器
- 费用列表 / 详情 / 周期规则前端
- `docs/GATE4-IMPLEMENTATION-REPORT.md`
- `docs/GATE4-TEST-REPORT.md`
- `docs/GATE4-EXPENSE-SCOPE-VERIFICATION.md`
- `docs/GATE4-DISTRIBUTION-VERIFICATION.md`
- `docs/GATE4-RECURRING-IDEMPOTENCY-VERIFICATION.md`
- `docs/GATE4-IBM-UI-REVIEW.md`
- `docs/GATE4-CLOSURE-REPORT.md`

## 已知问题

- 开发库仍留有 Gate 1 时期 pytest 写入的测试人员数据。未顺手删除。清理需单独 `DEV-DATA-CLEANUP-PLAN.md`。
- Windows Docker 绑定挂载下 Vite 文件监听仍依赖 polling。
- IBM Plex Sans 仍是 CSS 字体栈声明，未单独引入字体文件（Gate 1 UI 基线既有状态）。
- 运行态 Scope 脚本若对已改写 description 的费用再次 `ensure`，会再建一条同语义记录（id=8）；不影响 Scope 结论。
- GATE3-A 资源详情费用 Tab 当前为空，因为取证费用未绑定 `resource_account_id`；Tab 本身走真实筛选。

## Next Gate

Gate 5：统计与 Dashboard。

此时才允许公司费用总览、项目费用趋势、成员/资源类型/月度费用、闲置与即将到期、排行。

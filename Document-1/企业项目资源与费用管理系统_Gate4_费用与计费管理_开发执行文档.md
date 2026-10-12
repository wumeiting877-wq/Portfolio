# 企业项目资源与费用管理系统
# Gate 4 费用与计费管理开发执行文档

版本：V1.0  
阶段：Gate 4  
前置状态：Gate 0 PASS / Gate 1 PASS / Gate 2 PASS / Gate 3 PASS  
Gate 3 回归：92 passed  
目标：完成费用类型、费用记录、费用归属/分摊、周期计费、一次性费用、API 按量费用、服务器费用，并把费用权限接入真实 Project / Resource Scope。

---

# 1. Gate 4 进入条件

当前已确认：

```text
Gate 0: PASS
Gate 1: PASS
Gate 2: PASS
Gate 3: PASS

Auth: PASS
RBAC: PASS
Project Scope: PASS
Resource Scope: PASS
Shared Resource: PASS
Credential Safety: PASS
IBM UI Review: PASS
Tests: 92 passed
Alembic head: 0004_gate3_resources
Test DB: project_cost_hub_test
```

Gate 3 已实现：

```text
ResourceType
ResourceAccount
ResourceAllocation
Project / Employee 真实关系
多人共享
跨项目共享
资源访问 Scope
```

Gate 4 不得破坏上述冻结语义。

---

# 2. Gate 4 核心目标

本阶段必须让系统能够回答：

- 某个月公司花了多少钱？
- 某个项目花了多少钱？
- 某个成员产生了多少费用？
- 某个资源账号累计花了多少钱？
- ChatGPT / Cursor / Claude / GitHub 等各花了多少？
- 一次性费用是多少？
- 周期订阅是多少？
- API 按量费用是多少？
- 服务器费用是多少？
- 一个共享资源的费用如何分摊到不同项目/成员？
- 哪些费用是系统自动生成，哪些是人工录入？
- 某个资源本月是否已经生成订阅费用？

Gate 4 只负责：

```text
费用事实
费用归属
费用生成规则
费用分摊
费用查询
```

---

# 3. Gate 4 暂时不做

本阶段禁止提前开发：

```text
复杂 Dashboard
公司级 BI 大屏
项目费用排行大屏
预算
预算审批
发票
报销
财务凭证
采购审批
多级审批流
邮件提醒
Excel 大批量导入
成本预测
AI 分析
```

这些后续分别进入 Gate 5 / Gate 6。

Gate 4 可以提供统计 API，为 Gate 5 做准备，但不做大型可视化 Dashboard。

---

# 4. 前端最高级设计约束

Gate 4 所有新增和修改前端必须先读取：

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

优先级：

```text
真实业务
>
PROJECT-UI-CONSTRAINTS.md
>
IBM-DESIGN.md
>
Element Plus 默认视觉
>
工具自行发挥
```

继续保持：

```text
IBM Blue #0f62fe
IBM Plex Sans 字体栈
0px radius
1px hairline
Surface / Canvas
4px spacing grid
紧凑表格
```

禁止：

- 大圆角
- 大阴影
- 渐变
- 玻璃拟态
- AI / SaaS 营销卡
- 假 KPI
- 过多图表
- 每个金额一张大卡片
- 为视觉完整制造假数据

---

# 5. Gate 4 数据模型总览

推荐新增四张核心表：

```text
expense_types
expense_records
expense_distributions
recurring_expense_rules
```

关系：

```text
ExpenseType
    ↓
ExpenseRecord
    ↓
ExpenseDistribution
   ↙        ↘
Project    Employee

ExpenseRecord
    ↓ optional
ResourceAccount

RecurringExpenseRule
    ↓ generates
ExpenseRecord
```

---

# 6. 为什么不能只在 resource_accounts 加 price

禁止直接把：

```text
price
monthly_cost
amount
```

作为 Gate 4 的唯一费用事实。

原因：

同一个资源可能存在：

```text
月订阅
一次性购买
超额用量
API 按量
续费
服务器流量
人工调整
```

而且一个费用可能要：

```text
跨项目分摊
多人分摊
```

所以：

> ResourceAccount 是“资源资产”
> ExpenseRecord 才是“真实费用事实”

---

# 7. expense_types

费用类型由管理员维护。

建议字段：

```text
id
code
name
category
description
is_active
created_at
updated_at
```

category 建议固定枚举：

```text
SUBSCRIPTION
ONE_TIME
API_USAGE
SERVER
DOMAIN
CLOUD_SERVICE
SOFTWARE
HARDWARE
OTHER
```

示例：

```text
CURSOR_SUBSCRIPTION
CHATGPT_SUBSCRIPTION
OPENAI_API_USAGE
ALIYUN_SERVER
DOMAIN_RENEWAL
SOFTWARE_PURCHASE
```

`code` 唯一。

---

# 8. expense_records

这是 Gate 4 的核心事实表。

建议字段：

```text
id
expense_type_id
resource_account_id      nullable
billing_mode
source
expense_date
billing_period_start     nullable
billing_period_end       nullable

amount
currency

usage_quantity           nullable
usage_unit               nullable
unit_price               nullable

description
external_reference       nullable
created_by
created_at
updated_at
```

---

# 9. 金额数据类型

金额必须使用：

```text
NUMERIC / DECIMAL
```

禁止使用：

```text
FLOAT
DOUBLE
```

推荐：

```text
NUMERIC(18, 4)
```

或至少：

```text
NUMERIC(14, 2)
```

API / usage 可能需要更高精度。

---

# 10. Currency

Gate 4 第一版至少支持：

```text
CNY
USD
```

数据库必须保存：

```text
currency
```

但 Gate 4 不做：

```text
实时汇率
跨币种自动换算
```

不同币种统计不得简单相加为一个“总金额”。

Gate 5 如需要统一展示，再增加汇率策略。

---

# 11. billing_mode

建议：

```text
RECURRING
ONE_TIME
USAGE
MANUAL
```

含义：

```text
RECURRING -> 周期订阅
ONE_TIME  -> 一次性费用
USAGE     -> 按量费用
MANUAL    -> 普通人工费用
```

SERVER 可以根据真实计费方式使用：

```text
RECURRING
USAGE
ONE_TIME
```

不要把“服务器”既当 billing_mode 又当 expense category。

---

# 12. source

费用来源必须明确。

建议：

```text
MANUAL
RECURRING_RULE
IMPORT
API_SYNC
```

Gate 4 实现：

```text
MANUAL
RECURRING_RULE
```

Gate 6 再实现：

```text
IMPORT
API_SYNC
```

---

# 13. expense_distributions

费用归属不能只写在 `expense_records.project_id / employee_id`。

因为共享资源可能出现：

```text
1000 元
→ 新华项目 600
→ 佳悦项目 400
```

或者：

```text
1000 元
→ 张三 500
→ 李四 500
```

因此必须用独立分摊表。

建议字段：

```text
id
expense_record_id
project_id              nullable
employee_id             nullable

allocation_method
allocation_ratio        nullable
allocated_amount

created_at
updated_at
```

约束：

```text
project_id 与 employee_id 不能同时为空
allocated_amount >= 0
```

---

# 14. allocation_method

建议：

```text
DIRECT
EQUAL
RATIO
MANUAL
```

含义：

```text
DIRECT  -> 单一归属
EQUAL   -> 平均分摊
RATIO   -> 按比例
MANUAL  -> 手工金额
```

---

# 15. 分摊总额约束

每条 ExpenseRecord 必须满足：

```text
SUM(expense_distributions.allocated_amount)
==
expense_records.amount
```

允许由于小数产生极小差异时：

使用 Decimal 统一舍入规则。

禁止出现：

```text
记录金额 1000
分摊金额合计 900
```

保存成功。

必须在 Service 层做强校验。

---

# 16. 项目 + 成员一致性

如果 Distribution 同时有：

```text
project_id
employee_id
```

必须验证：

```text
employee 是该 project 的 active project_member
```

与 Gate 3 ResourceAllocation 规则保持一致。

---

# 17. Expense 与 Resource 的关系

费用可以：

## A. 关联 ResourceAccount

例如：

```text
Cursor-开发01
ChatGPT-Team-01
阿里云 ECS
OpenAI API
```

## B. 不关联 ResourceAccount

例如：

```text
一次性硬件采购
临时软件服务
域名注册
项目咨询费
```

因此：

```text
resource_account_id nullable
```

---

# 18. 周期订阅费用

例如：

```text
Cursor Pro
140 元 / 月
```

不要每个月手工录入。

新增：

```text
recurring_expense_rules
```

---

# 19. recurring_expense_rules

建议字段：

```text
id
expense_type_id
resource_account_id        nullable

frequency
amount
currency

start_date
end_date                   nullable
next_run_date
is_active

default_distribution_mode
created_by
created_at
updated_at
```

frequency 第一版：

```text
MONTHLY
QUARTERLY
YEARLY
```

---

# 20. 周期费用分摊模板

周期规则必须知道生成 Expense 后怎么归属。

推荐增加：

```text
recurring_expense_rule_distributions
```

如果不想新增第五张表，也可以将规则和 Distribution Template 拆为 JSON，但不推荐。

更推荐新增第五张表：

```text
recurring_rule_distributions
```

字段：

```text
id
rule_id
project_id nullable
employee_id nullable
allocation_method
allocation_ratio nullable
allocated_amount nullable
```

这样：

> 每次生成费用时，把规则分摊模板复制成真实 expense_distributions。

---

# 21. 周期费用生成要求

生成周期费用必须保证幂等。

必须有唯一约束或业务 Key：

```text
recurring_rule_id
billing_period_start
```

防止重复运行两次产生两条相同月费。

示例：

```text
Cursor Rule #10
2026-09
只能生成一次
```

---

# 22. 自动生成方式

Gate 4 第一版不强制引入 Celery / 定时任务框架。

可先实现命令：

```bash
python -m app.scripts.generate_recurring_expenses
```

以及 API：

```http
POST /api/expenses/recurring/generate
```

仅 ADMIN。

要求：

```text
可重复执行
不会重复生成
```

Gate 6 再接自动调度。

---

# 23. 一次性费用

例如：

```text
软件买断
硬件设备
域名购买
临时采购
```

直接创建：

```text
billing_mode = ONE_TIME
source = MANUAL
```

---

# 24. API 按量费用

例如：

```text
OpenAI
DeepSeek
Claude
OCR
ASR
短信
```

建议支持：

```text
usage_quantity
usage_unit
unit_price
amount
```

例如：

```text
usage_quantity = 15.4
usage_unit = "M tokens"
unit_price = 8.2
amount = 126.28
```

Gate 4 不要求自动从供应商拉账单。

管理员人工录入即可。

---

# 25. 服务器费用

服务器不单独建一套费用表。

统一使用：

```text
expense_type.category = SERVER
```

然后按真实情况：

```text
RECURRING
USAGE
ONE_TIME
```

例如：

```text
阿里云 ECS 月租
阿里云流量费用
云盘扩容
公网 IP
```

全部进入 expense_records。

---

# 26. 共享资源费用分摊

Gate 3 已经支持共享 Resource。

Gate 4 必须支持：

## 模式 A：全部归属项目

例如：

```text
ChatGPT Team 1000
全部归新华
```

## 模式 B：平均分摊项目

例如：

```text
新华 500
佳悦 500
```

## 模式 C：按成员平均

例如三人：

```text
张三 333.34
李四 333.33
王五 333.33
```

## 模式 D：手工比例

例如：

```text
新华 60%
佳悦 40%
```

---

# 27. 自动从 ResourceAllocation 生成分摊建议

Gate 4 可以提供：

```text
suggested distributions
```

例如资源有 3 个 active allocation：

```text
新华/张三
新华/李四
佳悦/王五
```

可以建议：

```text
EQUAL BY ALLOCATION
```

但：

> 只能是建议
> 不自动覆盖管理员确认结果

---

# 28. Expense Scope 总原则

必须继续复用：

```text
ProjectScope
ResourceScope
```

不得重新写第三套权限体系。

---

# 29. ADMIN

```text
GLOBAL + WRITE
```

可以：

- 查看全部费用
- 新增费用
- 修改费用
- 作废费用
- 管理费用类型
- 管理周期规则
- 生成周期费用
- 调整分摊

---

# 30. BOSS

```text
GLOBAL + READ
```

可以查看：

- 全部费用
- 全部分摊
- 全部周期规则
- 公司级费用

禁止写操作。

---

# 31. PROJECT_MANAGER

只读自己负责项目的费用。

判断依据：

```text
expense_distributions.project_id
IN
managed_project_ids
```

如果一个 Expense 分摊到多个项目：

PM 只能看到：

```text
自己的 distribution
```

不应看到其他项目的人员/分摊细节。

API 可以返回：

```text
original_expense_amount
```

还是只返回：

```text
allocated_amount
```

推荐最小披露：

> PM 默认以“自己项目分摊金额”为可见金额。

---

# 32. MEMBER

普通成员采用最小披露：

可以查看：

```text
直接分摊给自己的费用
```

不查看：

```text
同项目其他成员个人费用
```

对于项目级公共费用：

Gate 4 第一版不向 MEMBER 展示明细。

项目总费用汇总留 Gate 5 设计。

这样可避免：

```text
通过费用明细推断其他员工软件成本
```

---

# 33. Expense Scope Service

新增：

```text
permissions/expense_scope.py
```

推荐能力：

```text
readable_expenses(current_user)
readable_distributions(current_user)
can_read_expense(expense_id, current_user)
```

ADMIN/BOSS：

```text
GLOBAL
```

PM：

```text
managed project distributions
```

MEMBER：

```text
employee_id == current_user.employee_id
```

---

# 34. 费用详情的最小披露

同一 Expense：

```text
1000 元
新华 600
佳悦 400
```

新华 PM 查看时：

不要返回：

```text
佳悦 400
佳悦成员
```

建议返回：

```text
visible_allocated_amount = 600
```

以及自己项目的 distributions。

ADMIN / BOSS 才能看完整 1000 分摊结构。

---

# 35. Expense Type API

建议：

```http
GET    /api/expense-types
POST   /api/expense-types
GET    /api/expense-types/{id}
PUT    /api/expense-types/{id}
POST   /api/expense-types/{id}/disable
POST   /api/expense-types/{id}/enable
```

写：

```text
ADMIN
```

---

# 36. Expense API

建议：

```http
GET    /api/expenses
POST   /api/expenses
GET    /api/expenses/{id}
PUT    /api/expenses/{id}
POST   /api/expenses/{id}/void
```

不建议物理删除。

新增状态：

```text
ACTIVE
VOIDED
```

作废后：

```text
保留历史
不计入有效统计
```

---

# 37. Expense List Filters

支持：

```text
keyword
expense_type_id
category
billing_mode
source
resource_account_id
project_id
employee_id
currency
date_from
date_to
billing_period
status
page
page_size
```

筛选不得扩大 Scope。

---

# 38. Recurring Rule API

建议：

```http
GET    /api/recurring-expense-rules
POST   /api/recurring-expense-rules
GET    /api/recurring-expense-rules/{id}
PUT    /api/recurring-expense-rules/{id}
POST   /api/recurring-expense-rules/{id}/disable
POST   /api/recurring-expense-rules/{id}/enable
POST   /api/expenses/recurring/generate
```

写：

```text
ADMIN
```

BOSS：

```text
只读
```

PM/MEMBER：

第一版不显示周期规则管理。

---

# 39. Audit Log

新增：

```text
EXPENSE_TYPE_CREATE
EXPENSE_TYPE_UPDATE
EXPENSE_TYPE_DISABLE
EXPENSE_TYPE_ENABLE

EXPENSE_CREATE
EXPENSE_UPDATE
EXPENSE_VOID

EXPENSE_DISTRIBUTION_UPDATE

RECURRING_RULE_CREATE
RECURRING_RULE_UPDATE
RECURRING_RULE_DISABLE
RECURRING_RULE_ENABLE

RECURRING_EXPENSE_GENERATE
```

金额修改必须保留 before / after。

---

# 40. Alembic

新增：

```text
0005_gate4_expenses
```

如包含 5 张表：

```text
expense_types
expense_records
expense_distributions
recurring_expense_rules
recurring_rule_distributions
```

必须验证：

```text
0001
→ 0002
→ 0003
→ 0004
→ 0005
```

空库完整迁移。

---

# 41. 前端页面

Gate 4 允许新增：

```text
/expenses
/expenses/:id
```

ADMIN / BOSS 可进入周期规则管理。

可以选择：

```text
/expenses/recurring
```

或在费用页中使用独立 Tab。

推荐清晰路由：

```text
/expenses
/expenses/:id
/recurring-expenses
```

---

# 42. 左侧菜单

新增：

```text
费用管理
```

ADMIN：

```text
费用管理
周期规则
```

BOSS：

```text
费用管理
周期规则（只读）
```

PM：

```text
费用管理
```

MEMBER：

```text
费用管理
```

但数据均由后端 Scope 裁剪。

---

# 43. 费用列表页

建议：

```text
ExpenseListView.vue
```

PageHeader：

```text
费用管理
```

ADMIN：

```text
新增费用
费用类型
```

其他角色：

```text
无写按钮
```

---

# 44. 费用筛选

紧凑筛选：

```text
关键字
费用类型
计费方式
资源
项目
成员
日期范围
币种
状态
查询
重置
```

MEMBER：

隐藏：

```text
成员筛选
```

默认本人。

---

# 45. 费用表格

建议列：

```text
费用日期
费用类型
资源
计费方式
可见归属
金额
币种
来源
状态
操作
```

PM / MEMBER 的“金额”必须是：

```text
visible allocated amount
```

不要直接泄露全局 Expense 原始金额。

---

# 46. 费用详情页

建议 Tab：

```text
概览
费用归属
```

ADMIN / BOSS：

可见完整分摊。

PM：

仅自己项目可见分摊。

MEMBER：

仅自己个人分摊。

---

# 47. 新增费用

ADMIN Dialog / Drawer 字段：

```text
费用类型 *
资源账号
计费方式 *
费用日期 *
账期
金额 *
币种 *
用量
单位
单价
说明
```

然后第二部分：

```text
费用归属 / 分摊
```

支持：

```text
项目
成员
分摊方式
比例
分摊金额
```

保存前实时检查：

```text
分摊金额合计 == 总金额
```

---

# 48. 周期规则 UI

字段：

```text
规则名称
费用类型
资源账号
频率
金额
币种
开始日期
结束日期
下次生成日期
启用状态
分摊模板
```

支持：

```text
月
季度
年
```

---

# 49. Resource Detail 的 Gate 4 扩展

Gate 3 资源详情只有：

```text
概览
分配记录
```

Gate 4 完成后才允许增加第三个真实 Tab：

```text
费用记录
```

只显示真实 API 数据。

权限跟随 Expense Scope。

---

# 50. Project Detail 的 Gate 4 扩展

Gate 2 项目详情只有：

```text
概览
成员
```

Gate 4 完成后可增加：

```text
费用
```

但暂时以：

```text
费用列表
```

为主。

大图表留 Gate 5。

---

# 51. IBM UI Gate 4

继续禁止：

```text
大数字 KPI 墙
渐变金额卡
绿色/红色大面积金额状态
圆角账单卡片
财务 SaaS 模板风格
```

推荐：

```text
PageHeader
FilterBar
DataTable
Descriptions
Tabs
Hairline
Surface
```

金额对齐：

```text
右对齐
tabular-nums
```

币种必须显式显示。

---

# 52. Gate 4 自动测试

原 92 tests 不得回归。

---

# 53. Expense Type Tests

至少：

```text
ADMIN CRUD
code 唯一
disable / enable
非 ADMIN 写 403
```

---

# 54. Expense Record Tests

至少：

```text
人工订阅费用创建成功
一次性费用创建成功
API usage 创建成功
SERVER category 创建成功
resource 可空
currency 必填
amount Decimal
void 后不再计入 active 查询
```

---

# 55. Distribution Tests

至少：

```text
单项目 DIRECT
单成员 DIRECT
项目+成员 DIRECT
多人 EQUAL
多项目 RATIO
MANUAL amount
分摊总额不等于总额时失败
项目+成员不匹配失败
```

---

# 56. Recurring Tests

至少：

```text
MONTHLY 规则创建
QUARTERLY 规则创建
YEARLY 规则创建
生成真实 Expense
生成真实 Distribution
重复执行不重复生成
disabled rule 不生成
过 end_date 不生成
next_run_date 正确推进
```

---

# 57. Scope Tests

准备：

```text
Expense A -> Project A / member
Expense B -> Project B / other member
Expense C -> 公司级未分摊? 禁止：Expense 必须有至少一条 distribution
Expense D -> Project A / another member
Expense E -> shared resource, A 60% / B 40%
```

注意：

Gate 4 建议强制：

> 每条有效 Expense 至少存在一条 distribution。

这样不会产生“费用存在但没人知道归哪”的孤儿费用。

---

# 58. ADMIN Scope

```text
全部费用
全部分摊
可写
```

---

# 59. BOSS Scope

```text
全部费用
全部分摊
只读
```

---

# 60. PM Scope

Project A PM：

```text
看到 A
看到 D 的 Project A 分摊
看到 E 中 A 的 60%
看不到 B
看不到 E 的 Project B 40% 明细
写 403
```

---

# 61. MEMBER Scope

member：

```text
看到直接分摊给自己的 A
看不到同项目其他成员 D
如果 shared expense E 没有直接分摊给 member，则看不到
写 403
```

---

# 62. 越权测试

必须验证：

```text
PM project_id=其他项目不能扩大
MEMBER employee_id=其他人不能扩大
猜 expense id 不能越权
猜 distribution id 不能越权
非 ADMIN 修改 amount 403
非 ADMIN 修改 distribution 403
```

---

# 63. 金额精度测试

必须验证：

```text
0.1 + 0.2
```

不会出现 float 精度问题。

测试：

```text
1000 / 3
```

平均分摊最终必须精确等于：

```text
1000.00
```

例如：

```text
333.34
333.33
333.33
```

---

# 64. 周期费用幂等运行态取证

不能只做自动测试。

真实执行：

```bash
generate recurring expenses
generate recurring expenses
```

连续两次。

必须证明：

```text
第二次没有产生重复账单
```

---

# 65. 四角色真实运行态取证

必须用：

```text
admin
boss
pm
member
```

真实调用：

```text
GET /api/expenses
GET /api/expenses/{id}
```

并记录：

```text
全局费用
Project A
Project B
共享费用 60/40
成员费用
```

---

# 66. Gate 4 前端验收

ADMIN：

```text
费用菜单
新增费用
费用类型
分摊
作废
周期规则
生成周期费用
```

BOSS：

```text
全部只读
```

PM：

```text
只见负责项目费用
共享费用只显示自己项目份额
```

MEMBER：

```text
只见自己直接归属费用
不见同项目他人个人费用
```

---

# 67. Gate 4 开发顺序

严格按照：

```text
G4-00 扫描真实 Gate 3 代码与报告
G4-01 ExpenseType Model
G4-02 ExpenseRecord Model
G4-03 ExpenseDistribution Model
G4-04 RecurringExpenseRule Model
G4-05 RecurringRuleDistribution Model
G4-06 Alembic 0005
G4-07 Expense Schemas
G4-08 Expense Repository
G4-09 Distribution Service
G4-10 Expense Service
G4-11 Expense Scope Service
G4-12 Expense Type API
G4-13 Expense API
G4-14 Recurring Rule API
G4-15 Recurring Generator
G4-16 Distribution Validation
G4-17 Decimal / Rounding
G4-18 Audit
G4-19 Backend CRUD Tests
G4-20 Distribution Tests
G4-21 Recurring Idempotency Tests
G4-22 Scope / Security Tests
G4-23 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS
G4-24 Frontend Expense API
G4-25 Router / Menu
G4-26 ExpenseListView
G4-27 新增/编辑 Expense
G4-28 ExpenseDetailView
G4-29 Distribution UI
G4-30 RecurringRule UI
G4-31 Resource Detail 费用 Tab
G4-32 Project Detail 费用 Tab
G4-33 IBM UI Review
G4-34 npm run build
G4-35 pytest 全量回归
G4-36 周期费用幂等运行态取证
G4-37 四角色真实 Scope 取证
G4-38 Gate 4 报告
```

---

# 68. Gate 4 验收标准

只有全部通过才允许：

```text
Gate 4: PASS
```

Database：

```text
expense_types
expense_records
expense_distributions
recurring_expense_rules
recurring_rule_distributions
Alembic 0005
空库迁移 PASS
test DB 隔离 PASS
```

Billing：

```text
Recurring PASS
One-time PASS
Usage PASS
Server PASS
```

Distribution：

```text
Project PASS
Employee PASS
Shared PASS
Equal PASS
Ratio PASS
Manual PASS
总额校验 PASS
```

Security：

```text
ADMIN 全局读写
BOSS 全局只读
PM 管理项目份额只读
MEMBER 本人费用只读
越权拒绝
```

Recurring：

```text
MONTHLY / QUARTERLY / YEARLY
Idempotency PASS
```

Frontend：

```text
真实 API
IBM UI
无假 Dashboard
Project / Resource 费用 Tab 真实
```

Tests：

```text
原 92 tests 不退化
Gate 4 新测试全部 PASS
pytest 连续两次 PASS
npm run build PASS
```

---

# 69. Gate 4 输出报告

必须生成：

```text
docs/GATE4-IMPLEMENTATION-REPORT.md
docs/GATE4-TEST-REPORT.md
docs/GATE4-EXPENSE-SCOPE-VERIFICATION.md
docs/GATE4-DISTRIBUTION-VERIFICATION.md
docs/GATE4-RECURRING-IDEMPOTENCY-VERIFICATION.md
docs/GATE4-IBM-UI-REVIEW.md
docs/GATE4-CLOSURE-REPORT.md
```

---

# 70. Gate 4 完成后的能力

Gate 4 CLOSED 后系统应该真正具备：

```text
项目
↓
成员
↓
资源
↓
资源分配
↓
费用
↓
费用分摊
↓
周期生成
```

此时系统已经可以回答：

> 谁，在什么项目，使用了什么资源，花了多少钱。

这是 V1.0 的核心业务闭环第一次完整形成。

---

# 71. Next Gate

Gate 4 CLOSED 后进入：

```text
Gate 5：统计与 Dashboard
```

Gate 5 才做：

- 公司费用总览
- 项目费用趋势
- 成员费用
- 资源类型费用
- 月度费用
- 闲置资源
- 即将到期资源
- 项目/人员/资源排行

---

# 72. 给 Cursor / Codex 的直接执行提示词

你现在位于“企业项目资源与费用管理系统”真实仓库。

当前已确认：

```text
Gate 0 PASS
Gate 1 PASS
Gate 2 PASS
Gate 3 PASS
92 tests passed
Alembic head = 0004_gate3_resources
test DB = project_cost_hub_test
```

请先完整读取：

```text
企业项目资源与费用管理系统_Gate4_费用与计费管理_开发执行文档.md

docs/GATE3-IMPLEMENTATION-REPORT.md
docs/GATE3-TEST-REPORT.md
docs/GATE3-RESOURCE-SCOPE-VERIFICATION.md
docs/GATE3-SHARED-RESOURCE-VERIFICATION.md
docs/GATE3-IBM-UI-REVIEW.md
docs/GATE3-CLOSURE-REPORT.md

IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

先扫描真实仓库并输出：

```text
GATE4 CURRENT STATE
```

至少包括：

- 当前 Models
- 当前 Alembic head
- 当前 Project Scope
- 当前 Resource Scope
- ResourceAllocation 结构
- 当前 API
- 当前前端 Router / Menu
- 当前测试数量
- IBM UI 基础
- Gate 4 需要修改的真实文件
- 与 Gate 4 文档存在的差异

然后严格执行：

```text
G4-00 → G4-38
```

最高级要求：

1. 不回改 Gate 0/1/2/3 已冻结业务语义。
2. ResourceAccount 继续代表资源资产，不直接增加 price/monthly_cost 作为唯一费用事实。
3. 真实费用必须进入 ExpenseRecord。
4. 费用归属必须通过 ExpenseDistribution。
5. 支持项目、成员、项目+成员分摊。
6. 支持共享资源跨项目分摊。
7. 分摊金额合计必须严格等于 ExpenseRecord.amount。
8. 所有金额使用 Decimal / NUMERIC，禁止 Float。
9. 支持周期订阅、一次性、API 按量、服务器费用。
10. 周期费用必须通过 RecurringExpenseRule。
11. 自动生成必须幂等，重复执行不能重复出账。
12. ADMIN 全局读写。
13. BOSS 全局只读。
14. PM 只读自己负责项目的费用份额。
15. MEMBER 只读直接分摊给自己的费用。
16. PM/MEMBER 不得看到无权限分摊细节。
17. 后端 Scope 才是真实权限边界。
18. 筛选参数不得扩大 Scope。
19. 所有费用修改进入 Audit Log。
20. 作废费用保留历史，不物理删除。
21. 数据库变化使用 Alembic `0005`。
22. 测试继续强制使用 `project_cost_hub_test`。
23. Gate 3 原 92 项测试不得回归。
24. 前端编码前必须读取 `IBM-DESIGN.md`。
25. 禁止大圆角、大阴影、渐变、财务 SaaS KPI 卡。
26. Gate 4 只增加真实费用列表/详情/周期规则。
27. Resource Detail 和 Project Detail 只有真实 API 完成后才增加“费用”Tab。
28. Dashboard 统一留 Gate 5。
29. 必须做周期费用连续两次生成的幂等运行态取证。
30. 必须使用 admin / boss / pm / member 做真实 Expense Scope 取证。
31. 不要只输出方案，直接修改真实代码并测试。

最终必须生成：

```text
docs/GATE4-IMPLEMENTATION-REPORT.md
docs/GATE4-TEST-REPORT.md
docs/GATE4-EXPENSE-SCOPE-VERIFICATION.md
docs/GATE4-DISTRIBUTION-VERIFICATION.md
docs/GATE4-RECURRING-IDEMPOTENCY-VERIFICATION.md
docs/GATE4-IBM-UI-REVIEW.md
docs/GATE4-CLOSURE-REPORT.md
```

最终输出：

```text
Gate 4: PASS / FAIL

Alembic:
Expense Types:
Expense Records:
Distributions:
Recurring Rules:
Recurring Generator:
Idempotency:
Subscription:
One-time:
API Usage:
Server Cost:
GLOBAL Scope:
MANAGED_PROJECT Expense Scope:
MEMBER Expense Scope:
Decimal Precision:
Audit:
Frontend:
IBM UI:
Build:
Tests:

Known Issues:
Next Gate:
```

只有全部真实验收通过后，才能宣告 Gate 4 CLOSED。

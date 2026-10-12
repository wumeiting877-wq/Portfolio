# 企业项目资源与费用管理系统
# Gate 5 统计与 Dashboard 开发执行文档

版本：V1.0  
阶段：Gate 5  
前置状态：Gate 0 PASS / Gate 1 PASS / Gate 2 PASS / Gate 3 PASS / Gate 4 PASS  
Gate 4 回归：133 passed  
目标：在不破坏既有 Scope 的前提下，完成公司级 / 项目级 / 个人级统计、费用趋势、资源状态、排行榜和角色化 Dashboard。

---

# 一、Gate 5 进入条件

当前已确认：

```text
Gate 0: PASS
Gate 1: PASS
Gate 2: PASS
Gate 3: PASS
Gate 4: PASS

Auth: PASS
RBAC: PASS
Project Scope: PASS
Resource Scope: PASS
Expense Scope: PASS
Distribution: PASS
Recurring Idempotency: PASS
Decimal Precision: PASS
IBM UI Review: PASS

Tests: 133 passed
Alembic head: 0005_gate4_expenses
Test DB: project_cost_hub_test
```

Gate 4 已形成真实业务闭环：

```text
Project
→ Employee
→ Resource
→ ResourceAllocation
→ ExpenseRecord
→ ExpenseDistribution
→ RecurringExpenseRule
```

Gate 5 只在上述真实数据基础上做统计，不制造第二套业务事实。

---

# 二、Gate 5 核心目标

Gate 5 需要让不同角色真正回答以下问题。

## 老板 / ADMIN

- 本月公司各币种分别花了多少钱？
- 本年累计各币种分别花了多少钱？
- 哪些项目花费较高？
- 哪些成员花费较高？
- 哪些资源类型花费较高？
- 最近几个月费用趋势如何？
- 周期订阅 / 一次性 / API / 服务器分别花了多少？
- 当前多少资源使用中？
- 当前多少资源闲置？
- 哪些资源即将到期？
- 哪些资源已到期？
- 哪些资源当前没有分配？

## 项目负责人

- 自己负责项目本月费用是多少？
- 最近几个月项目费用趋势如何？
- 自己项目资源类型费用结构如何？
- 自己项目成员费用如何？
- 自己项目有哪些即将到期资源？
- 自己项目有哪些闲置 / 未分配资源？

## 普通成员

- 我本月直接归属费用是多少？
- 我最近几个月费用趋势如何？
- 我正在使用哪些资源？
- 我的资源哪些即将到期？
- 我的费用主要来自哪些资源类型？

---

# 三、Gate 5 不做

本阶段禁止提前开发：

```text
预算审批
预算预警
邮件提醒
Excel 大批量导入
供应商账单自动同步
实时汇率
AI 财务分析
成本预测
异常检测模型
采购流程
报销流程
发票管理
```

这些留 Gate 6+。

---

# 四、最高级统计原则

所有统计数字必须来自：

```text
真实数据库
+
真实 Scope
+
真实有效 Expense / Distribution
```

禁止：

- 前端本地拼总费用
- 前端拉全量再统计
- Statistics API 绕过 ExpenseScope
- 将 VOIDED 费用计入有效统计
- 将 released allocation 当 active
- 将 disabled resource 当 active resource
- 将不同币种直接相加

---

# 五、多币种规则

Gate 4 已支持：

```text
CNY
USD
```

Gate 5 禁止：

```text
CNY 1000 + USD 100 = 1100
```

所有金额类统计必须按 `currency` 分组。

示例：

```json
{
  "amounts_by_currency": {
    "CNY": "12800.00",
    "USD": "540.00"
  }
}
```

趋势也必须按：

```text
period + currency
```

分组。

Gate 5 不实现实时汇率和跨币种自动换算。

---

# 六、Gate 5 是否新增表

原则：

> 不新增统计事实表。

优先基于现有：

```text
projects
project_members
resource_accounts
resource_allocations
expense_records
expense_distributions
expense_types
resource_types
```

直接聚合。

如果性能需要，可以通过 Alembic `0006` 增加真实必要索引，例如：

```text
expense_records(expense_date, status, currency)
expense_distributions(project_id, employee_id)
resource_allocations(project_id, employee_id, is_active)
resource_accounts(status, expires_at)
```

如果现有索引已经足够，可不创建 `0006`，但必须在报告中说明。

禁止为了“每 Gate 必须有迁移”而创建无意义 migration。

---

# 七、Statistics Service

新增：

```text
backend/app/services/statistics_service.py
```

可配套：

```text
backend/app/repositories/statistics_repository.py
```

统计 Scope 必须复用：

```text
ProjectScope
ResourceScope
ExpenseScope
```

禁止复制第四套 Scope。

---

# 八、Statistics Scope

## ADMIN

```text
GLOBAL
```

统计全局。

## BOSS

```text
GLOBAL + READ
```

统计范围与 ADMIN 相同。

## PROJECT_MANAGER

只统计：

```text
自己负责项目
自己项目可见费用份额
自己项目可见资源
```

共享费用必须使用：

```text
自己项目 ExpenseDistribution.allocated_amount
```

不能使用 ExpenseRecord 原额。

## MEMBER

只统计：

```text
本人直接 ExpenseDistribution
本人直接 ResourceAllocation
```

不统计：

```text
同项目其他成员
项目公共费用
项目总费用
公司总费用
```

Gate 5 不得放宽 Gate 4 已冻结的最小披露规则。

---

# 九、时间范围

所有统计接口统一支持：

```text
date_from
date_to
```

前端提供：

```text
本月
近3个月
近6个月
今年
自定义
```

Gate 5 默认时间维度：

```text
expense_date
```

暂不混用 `billing_period_start`。

---

# 十、Overview API

建议：

```http
GET /api/statistics/overview
```

参数：

```text
date_from
date_to
```

ADMIN / BOSS 可返回：

```json
{
  "amounts_by_currency": {
    "CNY": "12800.00",
    "USD": "540.00"
  },
  "project_count": 8,
  "employee_count": 36,
  "resource_count": 72,
  "active_resource_count": 60,
  "idle_resource_count": 8,
  "unassigned_active_resource_count": 3,
  "expired_resource_count": 4,
  "expiring_soon_count": 6
}
```

PM 返回其负责项目范围。

MEMBER 只返回：

```text
amounts_by_currency
my_project_count
my_resource_count
my_expiring_resource_count
```

不要返回公司总人数、总资源、项目排行等。

---

# 十一、Expense Trend API

建议：

```http
GET /api/statistics/expense-trend
```

返回：

```json
{
  "series": [
    {
      "period": "2026-07",
      "currency": "CNY",
      "amount": "9800.00"
    },
    {
      "period": "2026-07",
      "currency": "USD",
      "amount": "220.00"
    }
  ]
}
```

统计必须基于：

```text
当前用户可见 ExpenseDistribution.allocated_amount
```

而不是全局 ExpenseRecord.amount。

---

# 十二、Project Cost API

建议：

```http
GET /api/statistics/project-costs
```

统计：

```text
project_id
project_name
currency
allocated_amount
```

权限：

```text
ADMIN / BOSS -> 全项目
PM -> 仅自己负责项目
MEMBER -> 禁止
```

MEMBER 调用建议直接 403。

---

# 十三、Employee Cost API

建议：

```http
GET /api/statistics/employee-costs
```

权限：

```text
ADMIN / BOSS -> 全员工
PM -> 自己负责项目中的员工 Distribution
MEMBER -> 禁止
```

重要：

如果费用 Distribution 为：

```text
project_id != null
employee_id = null
```

这是项目公共费用。

不得为了排行榜把它强行分摊给项目成员。

可以单独返回：

```text
project_public_cost
```

---

# 十四、Resource Type Cost API

建议：

```http
GET /api/statistics/resource-type-costs
```

链路：

```text
ExpenseRecord.resource_account_id
→ ResourceAccount
→ ResourceType
```

未绑定 Resource 的费用必须归入：

```text
UNBOUND / 未关联资源
```

不能丢失。

---

# 十五、Billing Cost API

建议：

```http
GET /api/statistics/billing-costs
```

按：

```text
billing_mode
expense_type.category
currency
```

聚合。

例如：

```text
RECURRING
ONE_TIME
USAGE
MANUAL
```

以及：

```text
SUBSCRIPTION
API_USAGE
SERVER
SOFTWARE
OTHER
```

---

# 十六、Resource Status API

建议：

```http
GET /api/statistics/resource-status
```

统计：

```text
ACTIVE
IDLE
EXPIRED
DISABLED
EXPIRING_SOON
UNASSIGNED_ACTIVE
```

注意：

`EXPIRING_SOON` 是动态计算，不写回 ResourceStatus。

---

# 十七、闲置与未分配定义

必须区分：

## 显式闲置

```text
resource.status == IDLE
```

## 未分配但仍 ACTIVE

```text
resource.status == ACTIVE
AND active allocation count == 0
```

API 分开返回：

```text
explicit_idle_count
unassigned_active_count
```

不要偷偷合成一个数字。

---

# 十八、Expiring Resource API

建议：

```http
GET /api/statistics/expiring-resources
```

默认：

```text
30 days
```

支持：

```text
days
```

建议最大：

```text
365
```

Scope 必须复用 ResourceScope。

---

# 十九、Dashboard 请求策略

首页不要一次请求十几个接口。

推荐首屏最多：

```text
1. overview
2. expense-trend
3. project-costs 或 member breakdown
4. resource-status
5. expiring-resources
```

完整排行放 `/statistics`。

---

# 二十、Dashboard 与 Statistics 分离

建议：

```text
/            -> Dashboard
/statistics  -> 详细统计
```

Dashboard：

```text
看重点
```

Statistics：

```text
做分析
```

不要复制两份一模一样的页面。

---

# 二十一、ADMIN / BOSS Dashboard

建议结构：

```text
PageHeader
时间范围

紧凑指标带
- 本期费用（按币种）
- 项目数
- 活跃资源
- 闲置 / 未分配
- 即将到期

费用趋势

项目费用 Top 5
资源类型费用 Top 5

即将到期资源
闲置 / 未分配资源
```

BOSS 与 ADMIN 数据范围相同，但无任何写操作入口。

---

# 二十二、PM Dashboard

建议：

```text
我的负责项目
本期费用（按币种）
费用趋势
项目成员费用
资源类型费用
项目资源状态
即将到期资源
```

PM 负责多个项目时提供项目筛选。

不能看其他项目。

---

# 二十三、MEMBER Dashboard

保持极简：

```text
我参与的项目
我的资源
我的本期费用（按币种）
我的费用趋势
我的资源类型费用
我的即将到期资源
```

禁止：

```text
员工排行
项目排行
公司总费用
他人费用
项目公共费用
```

---

# 二十四、Statistics 页面

建议 `/statistics`。

ADMIN / BOSS：

```text
项目
成员
资源类型
费用类型
资源状态
```

PM：

```text
我的项目
项目成员
资源类型
资源状态
```

MEMBER：

如需要保留 Statistics，只允许：

```text
我的费用
我的资源
```

---

# 二十五、图表库

如 ECharts 已存在则复用。

如未安装，可在 Gate 5 正式引入 ECharts。

图表要求：

- 不使用 3D
- 不使用渐变
- 不使用大面积高饱和颜色
- 优先折线图 / 横向条形图
- 图例清晰
- IBM Blue 为主序列
- 多序列使用克制的 Carbon 邻近语义色

如 IBM-DESIGN 未定义完整 chart palette：

只新增最小必要 chart token，并在 IBM UI Review 中记录。

---

# 二十六、金额显示

统一：

```text
右对齐
font-variant-numeric: tabular-nums
币种显式
```

例如：

```text
CNY 12,800.00
USD 540.00
```

禁止显示一个混合总额：

```text
13,340.00
```

---

# 二十七、空数据

无数据时必须显示真实 Empty State：

```text
当前时间范围暂无费用数据
当前没有即将到期资源
当前没有闲置资源
```

禁止生成模拟曲线、假 Top5、假金额。

---

# 二十八、排行榜规则

默认：

```text
Top 5
```

Statistics 页面允许：

```text
10 / 20
```

后端限制最大：

```text
100
```

防止无界聚合。

---

# 二十九、项目费用口径

项目费用：

```text
SUM(
  expense_distributions.allocated_amount
  WHERE project_id = target_project
)
```

只统计：

```text
ACTIVE ExpenseRecord
```

如果 Distribution 只有：

```text
employee_id
project_id = null
```

不得因为 Employee 当前属于某项目，就自动推断费用归项目。

Distribution 才是费用事实归属。

---

# 三十、成员费用口径

成员费用：

```text
SUM(
  expense_distributions.allocated_amount
  WHERE employee_id = target_employee
)
```

纯项目公共费用不进入员工费用。

---

# 三十一、资源费用口径

资源费用通过：

```text
ExpenseRecord.resource_account_id
```

聚合。

无资源关联的 Expense：

```text
UNBOUND
```

---

# 三十二、性能与 N+1

统计优先使用 SQL：

```text
SUM
COUNT
GROUP BY
JOIN
CASE
```

禁止：

```text
查询全表
→ Python 循环
→ 每行再查关联
```

必须重点检查：

```text
project ranking
employee ranking
resource type ranking
```

是否出现 N+1。

---

# 三十三、Gate 5 自动测试

Gate 4 原：

```text
133 tests
```

不得回归。

---

# 三十四、Overview Tests

至少：

```text
ADMIN 全局按币种统计
BOSS 与 ADMIN 同范围
PM 只统计负责项目
MEMBER 只统计本人直接费用
VOIDED 不计入
CNY/USD 不合并
```

---

# 三十五、Trend Tests

至少：

```text
按月聚合
按 currency 分组
跨月正确
PM 只自己项目份额
MEMBER 只本人份额
```

---

# 三十六、Project Ranking Tests

至少：

```text
ADMIN/BOSS 全项目
PM 仅负责项目
MEMBER 403
共享费用按 Distribution 计入
employee-only 且无 project 的费用不自动计入项目
```

---

# 三十七、Employee Ranking Tests

至少：

```text
ADMIN/BOSS 全员工
PM 仅自己项目的 Employee Distribution
项目公共费用不伪造到员工
MEMBER 403
```

---

# 三十八、Resource Type Cost Tests

至少：

```text
绑定 Resource 的 Expense 正确归类
未绑定 Resource 的 Expense -> UNBOUND
Scope 不扩大
currency 分组正确
```

---

# 三十九、Resource Status Tests

至少：

```text
ACTIVE
IDLE
EXPIRED
DISABLED
EXPIRING_SOON
ACTIVE + 0 allocation -> UNASSIGNED_ACTIVE
```

---

# 四十、安全测试

必须验证：

```text
PM 传 project_id=其他项目不能扩大统计
MEMBER 传 employee_id=其他人不能扩大
MEMBER 不能请求 employee ranking
MEMBER 不能请求 project ranking
无权限 project/resource filter 不能泄露数量
```

---

# 四十一、多币种专项测试

准备：

```text
CNY 100
USD 100
```

Overview 必须：

```text
CNY = 100
USD = 100
```

不能：

```text
total = 200
```

趋势、项目排行、资源类型费用也必须按币种分组。

---

# 四十二、真实运行态取证

必须使用：

```text
admin
boss
pm
member
```

准备：

```text
Project A
Project B
CNY Expense
USD Expense
共享 A/B Expense
成员直接 Expense
项目公共 Expense
绑定资源 Expense
未绑定资源 Expense
闲置资源
未分配资源
即将到期资源
```

逐角色验证：

```text
/
 /statistics
统计 API
```

---

# 四十三、ADMIN 真实验收

可见：

```text
全局费用按币种
全部项目
全部资源
全局趋势
项目排名
员工排名
资源类型
闲置
即将到期
```

---

# 四十四、BOSS 真实验收

数据范围同 ADMIN。

但：

```text
无管理员写入口
```

---

# 四十五、PM 真实验收

只能看到：

```text
自己负责项目
自己项目费用份额
自己项目资源
自己项目成员费用
自己项目即将到期资源
```

不能看到 Project B。

---

# 四十六、MEMBER 真实验收

只能看到：

```text
本人直接费用
本人资源
本人费用趋势
本人资源类型费用
本人即将到期资源
```

不能看到：

```text
其他成员
项目公共费用
员工排行
项目排行
公司总费用
```

---

# 四十七、IBM Dashboard 设计规则

Gate 5 允许指标区，但必须是 IBM 风格的紧凑指标带。

推荐：

```text
白底 / Surface
1px hairline
0px radius
无阴影
数字 24~32px
标题 12~14px
紧凑间距
```

禁止：

```text
彩色背景大卡
渐变
玻璃拟态
大面积品牌蓝
圆角 12/16/20
3D 图表
花哨动效
```

---

# 四十八、Dashboard 布局

桌面建议：

```text
PageHeader
时间范围

[紧凑指标带 4~5 格]

[费用趋势 2/3] [资源状态 1/3]

[项目 Top5 1/2] [资源类型 Top5 1/2]

[即将到期资源]
```

MEMBER：

```text
PageHeader
时间范围

[我的费用] [我的资源] [即将到期]

[我的费用趋势]

[我的资源类型]
```

---

# 四十九、图表高度

建议：

```text
趋势图 280~320px
横向排行 260~320px
资源状态 240~280px
```

避免单张图占满整屏。

---

# 五十、响应式

至少：

```text
1280px
1024px
768px
```

正常使用。

窄屏：

- 指标带 2 列
- 图表上下堆叠
- 表格横向滚动

不要强行做移动端卡片墙。

---

# 五十一、首页升级原则

当前 Home 只有身份 / 健康检查。

Gate 5 可以正式升级 `/` 为 Dashboard。

要求：

- 保留系统健康信息入口
- 不删除已有真实能力
- 不做纯视觉展示页
- 不展示假 KPI

---

# 五十二、Drill-down

统计项点击后：

```text
项目 -> /projects/:id?tab=expenses
资源 -> /resources/:id?tab=expenses
成员 -> /expenses?employee_id={id}
```

后端 Scope 继续生效。

---

# 五十三、Gate 5 开发顺序

严格按照：

```text
G5-00 扫描 Gate 4 真实代码与报告
G5-01 明确统计口径与多币种规则
G5-02 Statistics Repository
G5-03 Statistics Service
G5-04 Overview API
G5-05 Expense Trend API
G5-06 Project Cost API
G5-07 Employee Cost API
G5-08 Resource Type Cost API
G5-09 Billing Cost API
G5-10 Resource Status API
G5-11 Expiring Resource API
G5-12 Statistics Scope 校验
G5-13 Query 性能 / N+1 检查
G5-14 后端统计自动测试
G5-15 多币种专项测试
G5-16 Scope / Security 测试
G5-17 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS
G5-18 Frontend Statistics API
G5-19 Dashboard HomeView
G5-20 Role-specific Dashboard
G5-21 Expense Trend Chart
G5-22 Project Ranking
G5-23 Employee / Resource Type Ranking
G5-24 Resource Status / Expiring
G5-25 StatisticsView
G5-26 Drill-down
G5-27 IBM UI Review
G5-28 npm run build
G5-29 pytest 全量回归
G5-30 四角色真实 Dashboard 取证
G5-31 多币种运行态取证
G5-32 Gate 5 报告
```

---

# 五十四、Gate 5 验收标准

只有全部通过才允许：

```text
Gate 5: PASS
```

Backend：

```text
Overview PASS
Trend PASS
Project Cost PASS
Employee Cost PASS
Resource Type Cost PASS
Billing Cost PASS
Resource Status PASS
Expiring Resource PASS
```

Scope：

```text
ADMIN GLOBAL
BOSS GLOBAL READ
PM managed projects only
MEMBER self only
```

Currency：

```text
CNY / USD 分开
无跨币种直接合计
```

Resources：

```text
ACTIVE / IDLE / EXPIRED / DISABLED
EXPIRING_SOON
UNASSIGNED_ACTIVE
```

Frontend：

```text
Role-based Dashboard
真实 Statistics API
无假数据
IBM UI PASS
Dashboard / Statistics 职责分离
```

Tests：

```text
原 133 tests 不退化
Gate 5 新 tests PASS
pytest 连续两次 PASS
npm run build PASS
```

---

# 五十五、Gate 5 输出报告

必须生成：

```text
docs/GATE5-IMPLEMENTATION-REPORT.md
docs/GATE5-TEST-REPORT.md
docs/GATE5-STATISTICS-SCOPE-VERIFICATION.md
docs/GATE5-MULTI-CURRENCY-VERIFICATION.md
docs/GATE5-DASHBOARD-RUNTIME-VERIFICATION.md
docs/GATE5-IBM-UI-REVIEW.md
docs/GATE5-CLOSURE-REPORT.md
```

---

# 五十六、GATE5-STATISTICS-SCOPE-VERIFICATION

必须记录真实数据：

```text
Project A
Project B

A CNY Expense
A USD Expense
B CNY Expense
Shared A/B Expense
Member direct Expense
Project public Expense
```

使用：

```text
admin
boss
pm
member
```

调用真实 Statistics API。

禁止只写：

```text
代码正确
```

必须记录实际返回数值。

---

# 五十七、GATE5-MULTI-CURRENCY-VERIFICATION

至少准备：

```text
CNY 100
USD 100
```

验证：

```text
Overview
Trend
Project Ranking
Resource Type Cost
```

均按币种分开。

不得出现：

```text
200 总额
```

---

# 五十八、GATE5-DASHBOARD-RUNTIME-VERIFICATION

浏览器验证：

```text
ADMIN Dashboard
BOSS Dashboard
PM Dashboard
MEMBER Dashboard
Statistics 页面
```

记录：

- 可见模块
- 不可见模块
- 实际金额
- 实际项目
- 实际资源
- Scope 是否正确
- 是否出现假数据
- 是否出现越权信息

---

# 五十九、Gate 5 完成后的能力

Gate 5 CLOSED 后：

```text
项目
→ 成员
→ 资源
→ 费用
→ 分摊
→ 统计
→ 管理决策
```

系统第一次具备完整的管理驾驶舱能力。

---

# 六十、Next Gate

Gate 5 CLOSED 后进入：

```text
Gate 6：企业化能力收口
```

建议包括：

- Excel 导入
- Excel 导出
- 到期提醒
- 数据清理
- 操作日志查询
- 系统设置
- 真实数据导入准备
- 备份恢复
- 发布验收

---

# 六十一、给 Cursor / Codex 的直接执行提示词

你现在位于“企业项目资源与费用管理系统”真实仓库。

当前已确认：

```text
Gate 0 PASS
Gate 1 PASS
Gate 2 PASS
Gate 3 PASS
Gate 4 PASS

133 tests passed
Alembic head = 0005_gate4_expenses
test DB = project_cost_hub_test
```

请先完整读取：

```text
企业项目资源与费用管理系统_Gate5_统计与Dashboard_开发执行文档.md

docs/GATE4-IMPLEMENTATION-REPORT.md
docs/GATE4-TEST-REPORT.md
docs/GATE4-EXPENSE-SCOPE-VERIFICATION.md
docs/GATE4-DISTRIBUTION-VERIFICATION.md
docs/GATE4-RECURRING-IDEMPOTENCY-VERIFICATION.md
docs/GATE4-IBM-UI-REVIEW.md
docs/GATE4-CLOSURE-REPORT.md

IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

先扫描真实仓库并输出：

```text
GATE5 CURRENT STATE
```

至少包括：

- 当前 Models
- 当前 Alembic head
- Project / Resource / Expense Scope
- ExpenseDistribution 真实结构
- 当前统计能力是否存在
- 当前 API
- 当前 HomeView
- 当前 Router / Menu
- 当前测试数量
- 当前 IBM UI 基础
- Gate 5 实际需要修改的文件
- 与 Gate 5 文档存在的差异

然后严格执行：

```text
G5-00 → G5-32
```

最高级要求：

1. 不回改 Gate 0–4 已冻结业务语义。
2. 所有统计必须基于真实 ExpenseDistribution / ResourceAllocation。
3. ADMIN / BOSS 统计全局。
4. PM 只统计自己负责项目。
5. MEMBER 只统计本人直接费用与本人资源。
6. MEMBER 不得看到项目排行、员工排行、公司总费用。
7. Statistics Scope 必须后端实现。
8. 禁止前端拉全量再统计。
9. VOIDED 费用不得进入有效统计。
10. Released allocation 不得作为 active 资源关系。
11. CNY / USD 必须分开统计。
12. 禁止跨币种直接相加。
13. Gate 5 不实现实时汇率。
14. Project Cost 只基于 `distribution.project_id`。
15. Employee Cost 只基于 `distribution.employee_id`。
16. 不得根据员工当前项目反推费用项目归属。
17. Resource Cost 基于 `ExpenseRecord.resource_account_id`。
18. 未绑定 Resource 的费用必须保留为 UNBOUND。
19. “闲置”和“未分配 active resource”必须区分。
20. “即将到期”动态计算，不修改数据库状态。
21. 聚合优先使用 SQL GROUP BY，不全表加载到 Python 再 sum。
22. 检查 N+1。
23. Dashboard 只显示真实数据。
24. 无数据使用 Empty State，不生成假图表。
25. Dashboard KPI 使用 IBM 紧凑指标带。
26. 禁止彩色 SaaS KPI 卡、大圆角、大阴影、渐变、3D 图表。
27. 所有前端继续遵守 `IBM-DESIGN.md`。
28. 金额统一 tabular-nums、右对齐、显式币种。
29. Dashboard 和 Statistics 页面职责必须区分。
30. Gate 4 原 133 项测试不得回归。
31. 必须增加多币种专项自动测试和运行态取证。
32. 必须使用 admin / boss / pm / member 四角色浏览器真实取证。
33. 不要只输出方案，直接修改真实项目并测试。

最终必须生成：

```text
docs/GATE5-IMPLEMENTATION-REPORT.md
docs/GATE5-TEST-REPORT.md
docs/GATE5-STATISTICS-SCOPE-VERIFICATION.md
docs/GATE5-MULTI-CURRENCY-VERIFICATION.md
docs/GATE5-DASHBOARD-RUNTIME-VERIFICATION.md
docs/GATE5-IBM-UI-REVIEW.md
docs/GATE5-CLOSURE-REPORT.md
```

最终输出：

```text
Gate 5: PASS / FAIL

Statistics:
Overview:
Expense Trend:
Project Cost:
Employee Cost:
Resource Type Cost:
Billing Cost:
Resource Status:
Expiring Resources:
Multi Currency:
GLOBAL Statistics Scope:
MANAGED_PROJECTS Statistics Scope:
MEMBER Statistics Scope:
Dashboard:
Statistics Page:
IBM UI:
Build:
Tests:

Known Issues:
Next Gate:
```

只有全部真实验收通过后，才能宣告 Gate 5 CLOSED。

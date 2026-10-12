# 分角色看板重构执行任务
## BOSS / PROJECT_MANAGER / MEMBER

你现在正在修改【项目费用中枢】真实项目中的登录后首页 / Dashboard。

本轮目标：

基于当前真实项目、当前权限体系、当前统计 API、当前路由，以及现有三种角色看板设计稿，正式重构：

1. BOSS —— 经营总览
2. PROJECT_MANAGER —— 项目看板
3. MEMBER —— 我的工作台

注意：

这不是重新设计一套业务系统。

只允许重新组织已有数据与已有业务能力的前端展示形式。

---

# 一、最高级 UI 规则：必须先读取 IBM-DESIGN.md

任何新增或修改前端页面之前：

> 必须首先读取项目中的 `IBM-DESIGN.md`

并将其作为：

# UI Source of Truth

如果：

- 当前旧页面
- 设计参考图
- Element Plus 默认样式
- 当前 CSS
- 个人设计习惯

与 `IBM-DESIGN.md` 存在冲突：

一律以：

`IBM-DESIGN.md`

为准。

同时读取：

`PROJECT-UI-CONSTRAINTS.md`

优先级：

```text
真实业务
>
PROJECT-UI-CONSTRAINTS.md
>
IBM-DESIGN.md
>
现有前端实现
>
Element Plus 默认样式
```

在开始修改前，请先输出：

```text
IBM-DESIGN.md READ CONFIRMED
PROJECT-UI-CONSTRAINTS.md READ CONFIRMED
```

并简要列出本次 Dashboard 会遵守的：

- Typography
- Color
- Spacing
- Border
- Card
- Table
- Status
- Layout
- Button
- Chart

规范。

没有完成这一步：

禁止开始修改代码。

---

# 二、视觉目标

本次三个 Dashboard 参考已经提供的三张设计稿：

## BOSS

经营总览：

- 顶部 5 个 KPI
- 左侧费用趋势
- 右侧资源状态
- 项目成本
- 费用结构
- 底部需要关注

---

## PROJECT_MANAGER

项目看板：

- 时间筛选
- 负责项目筛选
- 顶部 5 个 KPI
- 项目费用趋势
- 资源状态
- 项目费用
- 资源类型费用
- 项目成员费用
- 项目公共费用
- 资源关注

---

## MEMBER

我的工作台：

- 顶部 4 个个人 KPI
- 我的项目
- 我的资源状态
- 我的费用趋势
- 我的资源类型费用
- 即将到期资源

---

设计稿只用于：

- 信息架构
- 区块顺序
- 页面密度
- 内容层级
- 左右布局关系

不要机械复制设计稿中与 `IBM-DESIGN.md` 冲突的视觉细节。

---

# 三、IBM 风格必须保持

根据当前项目 `IBM-DESIGN.md` 执行。

已知核心原则包括但不限于：

- IBM Blue：`#0f62fe`
- 页面主背景：白 / 浅灰
- 正文字色：`#161616`
- 次级文字：`#525252`
- Border：`#e0e0e0`
- 状态色仅使用既有绿色 / 黄色 / 红色
- 不允许额外发明品牌色
- 不允许渐变 Dashboard Card
- 不允许大面积蓝色 KPI 背景
- 不允许玻璃拟态
- 不允许毛玻璃
- 不允许营销型大圆角卡片
- 不允许夸张阴影
- 不允许 AI 风格发光效果
- 不允许视觉装饰压过数据本身

层级主要依赖：

```text
Typography
+
Spacing
+
1px Border
+
Surface
```

而不是：

```text
Shadow
+
Gradient
+
Rounded Card
```

整体目标：

> 正式、克制、企业级、数据清晰、IBM / Carbon 气质。

---

# 四、币种显示规则必须统一修改

这是本轮必改项。

目前系统中界面经常直接出现：

```text
CNY
USD
```

从本轮开始：

## 前端用户可见区域统一改为中文币种名称

映射：

```text
CNY → 人民币
USD → 美元
```

例如原来：

```text
CNY 7,232.50
USD 100.00
```

前端显示为：

```text
人民币 7,232.50
美元 100.00
```

原来：

```text
CNY 3,869.16
USD 100.00
```

显示：

```text
人民币 3,869.16
美元 100.00
```

---

## 图表图例

原来：

```text
● CNY
● USD
```

修改为：

```text
● 人民币
● 美元
```

---

## 表格

原来：

```text
Project A    CNY 3,856.66
Project A    USD 100.00
```

修改为：

```text
Project A    人民币 3,856.66
Project A    美元 100.00
```

---

## Tooltip

Chart tooltip 也必须显示：

```text
人民币
美元
```

不得继续暴露：

```text
CNY
USD
```

---

# 五、重要：只改“展示名称”，不能改底层币种代码

严禁：

把后端：

```text
CNY
USD
```

真正修改成：

```text
人民币
美元
```

数据库、API、Model、Type、Store 中：

仍然保持：

```text
CNY
USD
```

建议前端统一增加显示映射：

```ts
const CURRENCY_LABELS = {
  CNY: '人民币',
  USD: '美元',
}
```

或者统一 formatter：

```ts
currencyLabel(currency)
```

但是请优先检查项目现有 formatter / enum mapper。

如果已有：

- currency formatter
- label map
- enum display helper

直接复用。

不要重复造同类型工具。

---

# 六、禁止跨币种汇总

人民币与美元必须继续分别展示。

禁止：

```text
总费用：7332.50 + 100
```

禁止：

```text
总费用：7432.50
```

正确：

```text
本期费用

人民币 7,232.50
美元 100.00
```

这是现有真实业务约束，不允许为了 Dashboard 简洁而改变。

---

# 七、BOSS —— 经营总览

角色：

```text
BOSS
```

数据范围：

```text
GLOBAL
```

老板只看：

> 整体费用、项目、资源和需要关注的问题。

不要把所有系统数据都塞给老板。

---

## 7.1 页面标题

```text
经营总览
```

面包屑：

```text
首页 / 经营总览
```

---

## 7.2 时间筛选

保留：

```text
本月
近3个月
近6个月
今年
自定义
```

位置放 PageHeader 下方。

---

# 7.3 BOSS KPI

只展示 5 项：

### 1. 本期费用

示例：

```text
本期费用

人民币 7,232.50
美元 100.00
```

### 2. 项目数

```text
3
```

### 3. 使用中资源

```text
11
```

不要再叫：

```text
活跃资源
```

前端显示统一调整为：

```text
使用中资源
```

但不要修改后端字段：

`active_resource_count`

---

### 4. 闲置 / 未分配

例如：

```text
1 / 3
```

---

### 5. 即将到期

例如：

```text
1
```

---

# 7.4 BOSS —— 费用趋势

标题：

```text
费用趋势
```

折线图。

图例：

```text
人民币
美元
```

横轴：

```text
月份
```

不要加入：

- 同比
- 环比
- 预算线
- 预测
- AI 判断

当前没有这些真实业务能力。

---

# 7.5 BOSS —— 资源状态

右侧区域：

```text
资源状态
```

展示：

```text
使用中
闲置
未分配但仍使用中
即将到期
已到期
已停用
```

表现形式：

IBM 风格横向数据条 + 数量。

不要使用：

- 饼图
- 环形图
- 炫酷 Gauge

---

# 7.6 BOSS —— 项目成本

标题：

```text
项目成本
```

字段：

```text
项目名称
费用金额
```

例如：

```text
Project A     人民币 3,856.66
Project B     人民币 2,666.66
Project A     美元 100.00
校验项目       人民币 12.50
```

项目名称继续保留真实跳转。

---

# 7.7 BOSS —— 费用结构

标题：

```text
费用结构
```

如果真实接口支持：

使用 Tabs：

```text
按资源类型
按计费方式
```

默认：

```text
按资源类型
```

不要因为有资源类型数据就完全隐藏已有计费方式数据。

如果实现时发现现有业务逻辑不允许同时展示两个 Tab：

不要强行改后端。

先在报告中说明。

---

# 7.8 BOSS —— 需要关注

放页面底部。

只展示异常，不展示正常信息。

分三类：

### 即将到期

```text
1 个资源将在 30 天内到期
```

展示：

```text
资源名称
到期日期
```

---

### 未分配

```text
3 个使用中资源尚未分配
```

---

### 闲置

```text
1 个资源处于闲置状态
```

---

如果三个都是 0：

显示统一 Empty State：

```text
当前暂无需要关注的资源事项
```

---

# 八、BOSS 首页禁止新增

不要展示：

- 人员数
- 成员费用
- 系统账号
- 系统状态
- 后端健康
- 数据库健康
- 审计日志
- 系统设置
- 导入情况
- 项目预算
- 预算执行率
- 剩余预算
- 审批数量
- 风险评分
- AI 洞察
- 同比
- 环比

老板首页做减法。

---

# 九、PROJECT_MANAGER —— 项目看板

角色：

```text
PROJECT_MANAGER
```

数据范围：

```text
MANAGED_PROJECTS
```

核心问题：

> 我负责的项目现在费用怎么样、资源怎么样、钱落到了哪里。

---

## 9.1 标题

```text
项目看板
```

面包屑：

```text
首页 / 项目看板
```

---

# 9.2 筛选

左侧：

```text
本月
近3个月
近6个月
今年
自定义
```

右侧：

```text
我的负责项目
项目选择
```

如果负责人只有一个项目：

不需要强制显示多余筛选器。

沿用现有逻辑。

---

# 9.3 PROJECT_MANAGER KPI

顶部 5 项：

```text
本期费用
负责项目数
使用中资源
闲置 / 未分配
即将到期
```

费用示例：

```text
人民币 3,869.16
美元 100.00
```

---

# 9.4 我的项目费用

标题：

```text
我的项目费用
```

折线图：

```text
人民币
美元
```

只展示当前负责人数据范围。

项目筛选后：

所有区块同步刷新。

---

# 9.5 资源状态

与老板相同的表现形式。

但 Scope 必须是：

```text
MANAGED_PROJECTS
```

禁止显示其他负责人项目资源。

---

# 9.6 项目费用

标题：

```text
项目费用
```

字段：

```text
项目名称
金额
```

例如：

```text
Project A     人民币 3,856.66
Project A     美元 100.00
校验项目       人民币 12.50
```

---

# 9.7 资源类型费用

标题：

```text
资源类型费用
```

字段：

```text
资源类型
金额
```

例如：

```text
未关联资源    人民币 3,769.16
Gate5 AI      人民币 100.00
未关联资源    美元 100.00
```

---

# 9.8 项目成员费用

这是项目负责人核心区域。

标题：

```text
项目成员费用
```

字段：

```text
成员
金额
```

例如：

```text
普通成员          人民币 300.00
同项目另一成员    人民币 300.00
项目负责人        人民币 12.50
```

成员名保持已有跳转行为。

---

# 9.9 项目公共费用

标题：

```text
项目公共费用
```

字段：

```text
项目
金额
```

下方说明：

```text
项目公共费用单独列出，不摊入成员。
```

不能把公共费用强行分配到成员。

---

# 9.10 资源关注

页面底部。

只展示：

```text
即将到期
闲置
未分配
```

如果没有异常：

```text
当前暂无即将到期、闲置或未分配资源。
```

不要为了让页面看起来“丰富”而制造假数据。

---

# 十、PROJECT_MANAGER 不展示

禁止：

- 公司所有项目
- 全公司费用
- 公司人员
- 系统账号
- 审计日志
- 系统配置
- 其他负责人的成员费用
- 全局资源
- 老板经营数据

---

# 十一、MEMBER —— 我的工作台

角色：

```text
MEMBER
```

Scope：

```text
MEMBER_PROJECTS
```

正式统一页面名称：

```text
我的工作台
```

不要再出现：

```text
菜单：我的工作台
页面标题：我的资源
```

必须统一：

```text
菜单：我的工作台
PageHeader：我的工作台
Breadcrumb：首页 / 我的工作台
```

---

# 11.1 MEMBER KPI

只展示 4 个：

```text
我的本期费用
我参与的项目
我的资源
即将到期
```

例如：

```text
我的本期费用
人民币 330.00

我参与的项目
2

我的资源
4

即将到期
0
```

---

# 11.2 我的项目

这一块前移。

普通成员首先应该知道：

> 自己当前参与什么项目。

标题：

```text
我的项目
```

字段：

```text
项目名
状态
```

例如：

```text
Project A     进行中
校验项目       进行中
```

数据必须来自真实 MEMBER `/projects` Scope。

---

# 11.3 我的资源状态

标题：

```text
我的资源状态
```

只展示当前成员可见资源。

```text
使用中
闲置
未分配仍使用中
即将到期
已到期
已停用
```

---

# 11.4 我的费用趋势

标题：

```text
我的费用趋势
```

只展示自己的费用。

图例：

```text
人民币
美元
```

如果某币种无数据：

不要为了保持两条线伪造 0 数据。

遵循当前 IbmChart 空值逻辑。

---

# 11.5 我的资源类型费用

标题：

```text
我的资源类型费用
```

字段：

```text
资源类型
费用金额
占比
```

占比只有在：

同币种范围内可以正确计算时才显示。

不要把：

人民币 + 美元

混起来计算一个百分比。

如果当前真实数据不能正确支持多币种占比：

去掉占比列。

---

# 11.6 即将到期资源

标题：

```text
即将到期资源
```

字段可使用已有：

```text
资源名称
类型
状态
到期日期
剩余天数
```

没有：

显示 IBM 风格 Empty State：

```text
当前没有即将到期资源。
```

---

# 十二、MEMBER 不展示

不要显示：

- 所有项目费用
- 其他成员费用
- 项目公共费用
- 公司费用
- 公司资源
- 全局闲置
- 全局未分配
- 系统管理数据
- 人员管理
- 系统账号
- 审计日志
- 系统设置
- 公司项目排行

MEMBER 页面必须明显比：

BOSS / PROJECT_MANAGER

更简单。

---

# 十三、三个页面必须真正独立

目前现状是：

```text
BOSS
独立 Dashboard

ADMIN / PROJECT_MANAGER / MEMBER
共用 HomeView 条件渲染
```

本次至少要让：

```text
BOSS
PROJECT_MANAGER
MEMBER
```

形成真正独立的信息架构。

优先检查：

```text
frontend/src/views/home/HomeView.vue
frontend/src/views/home/shells/
```

建议最终形成：

```text
BossDashboardShell.vue
ProjectManagerDashboardShell.vue
MemberDashboardShell.vue
```

每一个组件具有自己的：

- Layout
- KPI
- Section
- Empty State

但公共组件必须复用。

不要复制三份：

- DateRange
- StatMetric
- IbmChart
- ResourceStatus
- MoneyFormatter

---

# 十四、公共组件复用

检查是否已有：

```text
PageHeader
StatusTag
IbmChart
DateRange
Money formatter
Empty state
Table component
```

已有：

直接复用。

没有：

只有在确实被两个以上 Dashboard 复用时才考虑抽公共组件。

不要过度组件化。

---

# 十五、布局密度

参照提供的三张设计图。

页面特点：

```text
紧凑
信息密度高
无大量空白
模块关系明确
表格优先
图表克制
```

不要出现：

- 一个指标占据半屏
- 过高 KPI 卡片
- 大面积上下留白
- 为视觉而视觉
- 过多 icon
- 大号 illustration
- 大量营销文案

---

# 十六、响应式

PC 为当前主要目标。

建议：

```text
> 1280
完整双列 Dashboard

980～1280
适当压缩列宽

< 980
双列 → 单列
```

但不要为了移动端重构现有业务。

只保持现有合理响应式能力。

---

# 十七、业务与权限严禁修改

本轮禁止：

- 修改后端 Scope
- 修改 RoleCode
- 修改 Permission
- 修改 JWT
- 修改数据库结构
- 修改费用计算方式
- 修改资源状态规则
- 修改项目归属
- 修改成员关系
- 修改币种代码
- 增加审批流
- 增加预算功能
- 增加风险算法

---

# 十八、不要新增当前系统不存在的指标

尤其不要新增：

```text
预算总额
预算执行率
剩余预算
同比
环比
风险项目
项目健康分
预测费用
AI 洞察
待审批
报销状态
```

除非代码审计发现这些能力实际上已经真实存在，并提供证据。

否则本轮禁止加入。

---

# 十九、实施顺序

按以下 Gate 执行。

## Gate 0：规范读取

读取：

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
ROLE-DASHBOARD-DESIGN-INPUT.md
```

输出：

```text
GATE 0 PASS
```

---

## Gate 1：当前代码审计

确认：

- HomeView
- 三个 Shell
- API
- formatter
- currency 展示逻辑
- DateRange
- IbmChart
- StatusTag

输出准备修改文件。

---

## Gate 2：币种中文化

完成统一：

```text
CNY → 人民币
USD → 美元
```

覆盖：

- KPI
- Chart legend
- Tooltip
- Table
- Label
- Empty / fallback
- Statistics display

但不改：

```text
API
DB
Enum
Raw value
```

---

## Gate 3：BOSS

按本任务结构完成：

```text
经营总览
```

---

## Gate 4：PROJECT_MANAGER

完成：

```text
项目看板
```

---

## Gate 5：MEMBER

完成：

```text
我的工作台
```

并统一：

```text
菜单
PageHeader
Breadcrumb
```

---

## Gate 6：回归

使用：

```text
boss
pm
member
```

三个真实账号分别登录检查。

确认：

### BOSS

只能看到 GLOBAL Dashboard。

### PM

只能看到 MANAGED_PROJECTS。

### MEMBER

只能看到 MEMBER_PROJECTS。

---

# 二十、必须验证

至少验证：

- [ ] `npm run build` 通过
- [ ] 无 TypeScript error
- [ ] 无 Vue console error
- [ ] 无 404 API
- [ ] 无新增 403
- [ ] BOSS 页面正常
- [ ] PM 页面正常
- [ ] MEMBER 页面正常
- [ ] 时间切换正常
- [ ] PM 项目筛选正常
- [ ] 图表正常
- [ ] 空态正常
- [ ] 项目链接正常
- [ ] 资源链接正常
- [ ] 成员链接正常
- [ ] 人民币显示正常
- [ ] 美元显示正常
- [ ] UI 不再显示 CNY
- [ ] UI 不再显示 USD
- [ ] API 原始 currency 仍为 CNY / USD
- [ ] 没有跨币种相加
- [ ] IBM-DESIGN.md 约束没有被破坏

---

# 二十一、视觉回归重点

逐个截图检查。

重点看：

1. PageHeader 是否过高
2. KPI 是否过高
3. 表格密度是否合理
4. 是否出现过多空白
5. 左右区域是否对齐
6. Border 是否统一
7. 是否出现未经允许的圆角
8. 是否出现 Shadow
9. 蓝色是否只用于重点
10. 状态颜色是否正确
11. 长项目名是否破版
12. 人民币 / 美元长文本是否影响布局

---

# 二十二、最终输出报告

完成后创建：

`docs/ROLE-DASHBOARD-IBM-REDESIGN-IMPLEMENTATION-REPORT.md`

报告必须说明：

## 1. IBM 规范读取结果

## 2. 修改文件

## 3. BOSS 新首页结构

## 4. PROJECT_MANAGER 新首页结构

## 5. MEMBER 新首页结构

## 6. 币种中文化方案

明确：

```text
DB / API：CNY、USD

UI：
CNY → 人民币
USD → 美元
```

## 7. 数据来源

每个 Dashboard 对应哪些真实 API。

## 8. 权限范围

说明：

```text
BOSS = GLOBAL
PROJECT_MANAGER = MANAGED_PROJECTS
MEMBER = MEMBER_PROJECTS
```

## 9. Build 与运行测试

## 10. 浏览器截图验证

## 11. 未实现内容

明确哪些需求因为：

```text
当前没有数据/API
```

而没有加入。

---

# 二十三、停止条件

完成三种 Dashboard：

```text
BOSS
PROJECT_MANAGER
MEMBER
```

及币种中文化以后：

停止。

不要继续：

- ADMIN 重构
- 后端开发
- 预算系统
- 审批系统
- 风险系统
- 新业务模块

等待人工验收。

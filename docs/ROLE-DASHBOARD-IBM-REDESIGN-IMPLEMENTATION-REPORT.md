# 分角色 Dashboard IBM 重构实施报告

实施日期：2026-09-24

## 1. IBM 规范读取结果

已完整读取：

- `IBM-DESIGN.md`
- `PROJECT-UI-CONSTRAINTS.md`
- `docs/ROLE-DASHBOARD-DESIGN-INPUT.md`

实现遵循 IBM Plex Sans、4px 间距网格、白/浅灰表面、`#161616` 正文、`#525252` 次级文字、`#0f62fe` 单一品牌强调色、1px `#e0e0e0` 边线及直角无阴影容器。Dashboard 未引入渐变、毛玻璃、发光、大圆角或营销式卡片。

## 2. 修改文件

Dashboard 与公共组件：

- `frontend/src/views/home/HomeView.vue`
- `frontend/src/views/home/shells/BossDashboardShell.vue`
- `frontend/src/views/home/shells/ProjectManagerDashboardShell.vue`
- `frontend/src/views/home/shells/MemberDashboardShell.vue`
- `frontend/src/views/home/components/DashboardDateFilter.vue`
- `frontend/src/views/home/components/ResourceStatusBars.vue`
- `frontend/src/components/charts/IbmChart.vue`
- `frontend/src/config/roleUi.ts`

币种展示：

- `frontend/src/utils/money.ts`
- `frontend/src/views/statistics/StatisticsView.vue`
- `frontend/src/views/expenses/ExpenseListView.vue`
- `frontend/src/views/expenses/ExpenseDetailView.vue`
- `frontend/src/views/expenses/RecurringExpenseListView.vue`
- `frontend/src/views/projects/ProjectDetailView.vue`
- `frontend/src/views/resources/ResourceDetailView.vue`
- `frontend/src/views/enterprise/ImportExportView.vue`
- `frontend/src/views/enterprise/SettingsView.vue`

## 3. BOSS 新首页结构

标题与面包屑为“经营总览”及“首页 / 经营总览”。页面包含日期筛选、5 个 KPI、费用趋势、资源状态横向数据条、项目成本、费用结构和底部“需要关注”。费用结构保留“按资源类型 / 按计费方式”两个真实数据 Tab；关注区只展示即将到期、未分配与闲置异常。

## 4. PROJECT_MANAGER 新首页结构

标题与面包屑为“项目看板”及“首页 / 项目看板”。页面形成独立信息架构，包含日期与负责项目筛选、5 个 KPI、我的项目费用、资源状态、项目费用、资源类型费用、项目成员费用、项目公共费用和资源关注。项目公共费用单独展示，不摊入成员。项目选择会把 `project_id` 同步传给所有统计区块。

## 5. MEMBER 新首页结构

菜单、PageHeader 与面包屑统一为“我的工作台”。页面包含 4 个个人 KPI、前置的“我的项目”、我的资源状态、我的费用趋势、我的资源类型费用和即将到期资源。资源类型占比按各自币种独立计算，没有人民币与美元混算。

## 6. 币种中文化方案

底层保持不变：

```text
DB / API：CNY、USD
```

前端在 `utils/money.ts` 统一增加 `currencyLabel()`：

```text
UI：
CNY → 人民币
USD → 美元
```

`formatMoney()`、Dashboard KPI、表格、下拉、图表图例及 SVG 数据点 Tooltip 均使用中文展示名称。金额仍按币种逐行/逐系列呈现，没有跨币种汇总。

## 7. 数据来源

公共 Dashboard 数据：

- `GET /api/statistics/overview`
- `GET /api/statistics/expense-trend`
- `GET /api/statistics/resource-type-costs`
- `GET /api/statistics/resource-status`
- `GET /api/statistics/expiring-resources`

BOSS 额外使用：

- `GET /api/statistics/project-costs`
- `GET /api/statistics/billing-costs`

PROJECT_MANAGER 额外使用：

- `GET /api/statistics/project-costs`
- `GET /api/statistics/employee-costs`
- `GET /api/projects`

MEMBER 的“我的项目”使用受 MEMBER scope 过滤的 `GET /api/projects`。

## 8. 权限范围

```text
BOSS = GLOBAL
PROJECT_MANAGER = MANAGED_PROJECTS
MEMBER = MEMBER_PROJECTS
```

本轮未修改后端 scope、角色 code、权限、JWT、路由业务语义、数据库结构或费用计算。

## 9. Build 与运行测试

- `npm run build`：通过。
- `vue-tsc -b`：通过，无 TypeScript error。
- Vite production build：通过；仅保留既有的大 chunk size 提示。
- 三角色实际 Dashboard 所需 API：全部返回 HTTP 200，无新增 403/404。
- 浏览器控制台 error：0。
- 时间范围：在 MEMBER 页面实际切换“本月 → 近3个月”，选中状态与数据请求正常。
- PM 项目筛选：实际切换到 `Project A`，KPI、项目费用和成员/公共费用同步刷新。

## 10. 浏览器截图验证

在运行中的 `http://127.0.0.1:5173` 使用 1440×1000 桌面视口，分别用真实 `boss`、`pm`、`member` 账号登录并截图核对。

- BOSS：5 KPI 正常；人民币/美元分行；趋势与资源状态并列；项目成本、费用结构与关注项内容正确。
- PM：负责项目下拉、人民币/美元数据、成员费用、公共费用与资源关注正确；没有越权出现 Project B。
- MEMBER：菜单/PageHeader/面包屑均为“我的工作台”；仅显示本人项目、资源和费用；人民币显示正常；无到期资源时空态正确。
- 三页均使用直角、1px 边线、无阴影/渐变；长金额文本未破版；980px 以下已保留单列降级。

## 11. 未实现内容

未加入当前系统没有真实数据或 API 支持的预算、预算执行率、同比、环比、预测费用、风险评分、AI 洞察、审批、系统健康等指标。未重构 ADMIN Dashboard，符合本轮停止条件。


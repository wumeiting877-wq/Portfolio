# Gate 4 IBM UI Review

日期：2026-09-22  
视觉 Source of Truth：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`

## 已读取

- [x] IBM-DESIGN.md
- [x] PROJECT-UI-CONSTRAINTS.md

前端编码前已读取上述文件。未新建第二套 token 文件，未改 `tokens.css` 色板。

## 修改 / 新增文件

```text
frontend/src/api/expenses.ts
frontend/src/router/index.ts
frontend/src/stores/auth.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/components/StatusTag.vue
frontend/src/style.css
frontend/src/views/expenses/ExpenseListView.vue
frontend/src/views/expenses/ExpenseDetailView.vue
frontend/src/views/expenses/RecurringExpenseListView.vue
frontend/src/views/resources/ResourceDetailView.vue
frontend/src/views/projects/ProjectDetailView.vue
PROJECT-UI-CONSTRAINTS.md
```

## 各页面使用的 IBM Token

### 费用列表 `/expenses`

| 元素 | Token / 实现 |
| --- | --- |
| 页背景 | `--color-bg-page` = surface-1 `#f4f4f4` |
| 表格面板 | canvas `#ffffff` + 1px hairline `#e0e0e0` + radius 0 |
| 标题 | PageHeader，24px / 400 |
| 说明 | 16px / 400，「金额按当前权限范围显示」 |
| 主按钮「新增费用」 | IBM Blue `#0f62fe`，radius 0 |
| 「费用类型」 | charcoal secondary，radius 0 |
| 查询/重置 | 现有 secondary |
| 表格 | 14px，header surface-1，无阴影 |
| 金额 | `.amount-cell { font-variant-numeric: tabular-nums }` |
| 状态 | StatusTag：有效 success `#24a148`；已作废 error |
| 分页 | 圆角 0；当前页 IBM Blue |

无 KPI 色卡，无渐变，无总费用仪表盘。

### 新增/编辑 Dialog 与费用类型 Dialog

| 元素 | Token / 实现 |
| --- | --- |
| 容器 | canvas，1px hairline，radius 0，无 box-shadow |
| 输入 | surface-1 底，Carbon 底线 focus |
| 主按钮 | IBM Blue |
| 分摊区 | 同一 hairline 表，金额右对齐 |

### 费用详情 `/expenses/:id`

| 元素 | Token / 实现 |
| --- | --- |
| Tab | IBM product-tab：选中 2px Blue 底线 |
| 概览 | descriptions：label surface-1，content canvas，1px hairline |
| 费用归属 | 与列表同一 list-panel |
| 作废 | semantic-error 实心，radius 0 |

浏览器实测 GATE4-E-SHARED：概览金额 1000.0000 CNY；归属 Tab 两行 RATIO 600 / 400。

### 周期规则 `/recurring-expenses`

| 元素 | Token / 实现 |
| --- | --- |
| 主按钮「新增规则」 | IBM Blue |
| 「生成周期费用」 | charcoal secondary |
| 表格 | 规则名 / 类型 / 频率 / 金额 tabular-nums / 下次生成 / 状态 |

浏览器实测：一条 `GATE4-CURSOR-MONTHLY`，140.0000 CNY，下次生成 2026-10-01。

### Resource / Project 详情费用 Tab

仅在真实 `GET /api/expenses` 完成后增加。  
GATE3-A 费用记录 Tab 为空表（该资源未绑定费用事实，符合「无假数据」）。  
Project A 费用 Tab 列出真实分摊到该项目的记录。

### 首页

仍为身份与健康检查 descriptions，**无费用 KPI**。Dashboard 留 Gate 5。

## IBM-DESIGN 未覆盖场景及处理

| 场景 | IBM-DESIGN | 处理 |
| --- | --- | --- |
| 后台 Sidebar | 营销站只有 top-nav | 保持已校准 Sidebar |
| 数据表格 | 营销提取无 data table | 沿用 hairline table |
| 分页器 | 未定义 | 圆角压到 0；active 用 IBM Blue |
| Dialog | 未定义后台 modal | 无阴影、0 radius、hairline |
| 金额列 | 未定义 tabular nums | 仅 `font-variant-numeric`，不改色板 |

原则：IBM 没规定 → 保持稳定结构 → 用现有 IBM Token → 不创造第三套视觉。

## 是否新增自定义视觉规则

没有新色板、新圆角体系、新阴影体系。  
仅扩展 StatusTag 的 `expense` / `billing` / `source` 文案映射，以及 `.amount-cell` 等宽数字。

## 大圆角 / 阴影 / 渐变

- 大圆角：无
- 大阴影：无
- 渐变：无
- 财务 SaaS KPI 卡片：无
- 假 Dashboard：无

## ADMIN 与只读角色按钮差异

浏览器实测：

- ADMIN：菜单含费用管理 + 周期规则 + 人员管理 + 系统账号；列表有「费用类型 / 新增费用」；行内「查看 / 编辑 / 作废」；周期规则有「生成周期费用 / 新增规则 / 编辑 / 停用」
- MEMBER（本轮更早会话）：菜单有费用管理，**无**周期规则；列表无新增/费用类型；无成员筛选；仅 1 条本人 100 CNY；仅「查看」

BOSS / PROJECT_MANAGER 前端隐藏写按钮；后端 403 才是边界。四角色 API 取证见 `GATE4-EXPENSE-SCOPE-VERIFICATION.md`。

## npm build

```text
vue-tsc -b && vite build  成功（7.36s）
```

## 清单

```text
[x] 已读取 IBM-DESIGN.md
[x] 已读取 PROJECT-UI-CONSTRAINTS.md
[x] IBM Blue 仅作主要强调
[x] IBM Plex Sans 字体栈
[x] 默认 0px radius
[x] 无大圆角
[x] 无大阴影
[x] 无渐变
[x] Surface / Canvas 使用正确
[x] 1px Hairline 表达层级
[x] 4px spacing grid
[x] 表格紧凑
[x] 金额 tabular-nums
[x] 没有 KPI 假数据
[x] Dashboard 留 Gate 5
[x] 费用 Tab 走真实 API
[x] PageHeader 已复用
[x] StatusTag 已复用
[x] ADMIN 写按钮可见
[x] 只读角色无写按钮
[x] 后端才是权限边界
```

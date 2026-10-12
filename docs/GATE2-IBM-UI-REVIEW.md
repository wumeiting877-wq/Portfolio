# Gate 2 IBM UI Review

日期：2026-09-22  
视觉 Source of Truth：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`

## 已读取

- [x] IBM-DESIGN.md
- [x] PROJECT-UI-CONSTRAINTS.md

## 修改文件

```text
frontend/src/api/projects.ts
frontend/src/router/index.ts
frontend/src/stores/auth.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/components/StatusTag.vue
frontend/src/views/projects/ProjectListView.vue
frontend/src/views/projects/ProjectDetailView.vue
frontend/src/style.css
PROJECT-UI-CONSTRAINTS.md
```

未新建第二套 token 文件，未改 `tokens.css` 色板。

## 各页面使用的 IBM Token

### 项目列表 `/projects`

| 元素 | Token / 实现 |
| --- | --- |
| 页背景 | `--color-bg-page` = surface-1 `#f4f4f4` |
| 表格面板 | canvas `#ffffff` + 1px hairline `#e0e0e0` + radius 0 |
| 标题 | PageHeader，24px / 400，对应 card-title |
| 说明 | 16px / 400 / 1.5 / 0.16px body |
| 主按钮「新建项目」 | IBM Blue `#0f62fe`，padding 12px 16px，radius 0 |
| 查询/重置 | 现有 secondary：炭黑实心，radius 0 |
| 表格 | 14px，header surface-1，无阴影 |
| 状态 | StatusTag：ACTIVE 用 success `#24a148`，不用 IBM Blue 当所有状态色 |
| 筛选间距 | 8px gap，4px grid |

### 新建/编辑 Dialog

| 元素 | Token / 实现 |
| --- | --- |
| 容器 | canvas，1px hairline，radius 0，无 box-shadow |
| 输入 | surface-1 底，Carbon 底线 focus |
| 主按钮 | IBM Blue |
| 取消 | charcoal secondary |
| 字段 | 编码、名称、负责人、状态、日期、说明；无装饰图标卡 |

### 项目详情 `/projects/:id`

| 元素 | Token / 实现 |
| --- | --- |
| Tab | IBM product-tab：16px 20px padding，选中 2px Blue 底线 |
| 概览 | 复用 Home 的 descriptions：label surface-1，content canvas，1px hairline |
| 成员表 | 与列表同一 list-panel |
| 仅两个 Tab | 概览、成员。无资源/费用 Tab |

## IBM-DESIGN 未覆盖场景及处理

| 场景 | IBM-DESIGN | 处理 |
| --- | --- | --- |
| 后台 Sidebar | 营销站只有 top-nav | 保持 Gate 1 已校准 Sidebar，不创造新宽度/颜色 |
| 数据表格 | 营销提取无 data table | 沿用 Batch B 的 hairline table，不另做卡片墙 |
| 分页器 | 未定义 | 紧凑 pager；圆角压到 0；active 用 IBM Blue。不做成 pill 营销组件 |
| Date picker | 无独立组件 | Element Plus DatePicker + 现有 input 底线视觉 |
| Dialog 遮罩 | 未定义后台 modal | 保持 Gate 1 Dialog：无阴影、0 radius、hairline |
| 成员角色标签 | 无 membership 组件 | 复用 StatusTag，0 radius、1px 边 |

原则：IBM 没规定 → 保持稳定结构 → 用现有 IBM Token → 不创造第三套视觉。

## 是否新增自定义视觉规则

没有新色板、新圆角体系、新阴影体系。  
仅扩展 StatusTag 的 `project` / `membership` 文案映射，形状仍是 0 radius hairline tag。

## 大圆角 / 阴影 / 渐变

- 大圆角：无（按钮、卡片、输入、Dialog 均为 0）
- 大阴影：无
- 渐变：无
- KPI 假卡片：无
- 资源/费用假 Tab：无

Element Plus 分页默认 active 页码偏圆，已在 `.list-pagination` 中压成直角。这是实现层覆盖，不是新设计系统。

## ADMIN 与只读角色按钮差异

浏览器实测：

- ADMIN：菜单含项目管理 / 人员管理 / 系统账号；列表有「新建项目」；行内「查看 / 编辑 / 成员 / 归档」；详情成员 Tab 有「添加成员 / 移除」（负责人行移除禁用）
- MEMBER：菜单仅首页 + 项目管理；列表只有 GATE2-A 和「查看」；详情无添加/移除

BOSS / PROJECT_MANAGER 的写按钮与 MEMBER 相同（前端隐藏）；后端 403 才是边界。四角色 API 取证见 `GATE2-SCOPE-VERIFICATION.md`。

## npm build

```text
vue-tsc -b && vite build  成功
```

## 浏览器实测

- `http://localhost:5173/login`：白底、方正登录板、IBM Blue 主按钮
- MEMBER `/projects`：一条 GATE2-A，只读
- MEMBER `/projects/1`：概览 + 成员，无写按钮
- ADMIN `/projects`：GATE2-A 与 GATE2-B，写操作可见
- ADMIN 新建项目 Dialog：方正、无阴影、IBM 输入底线
- ADMIN 成员页：添加成员 + 移除

## 清单

```text
[x] 已读取 IBM-DESIGN.md
[x] 已读取 PROJECT-UI-CONSTRAINTS.md
[x] IBM Blue 仅作主要强调
[x] IBM Plex Sans 字体栈（沿用现有实现，未新增第二套字体方案）
[x] 默认 0px radius
[x] 无大圆角
[x] 无大阴影
[x] 无渐变
[x] Surface / Canvas 使用正确
[x] 1px Hairline 表达层级
[x] 4px spacing grid
[x] 表格紧凑
[x] 没有 KPI 假数据
[x] 没有资源/费用假 Tab
[x] PageHeader 已复用
[x] StatusTag 已复用
[x] ADMIN 写按钮可见
[x] 只读角色无写按钮
[x] 后端才是权限边界
```

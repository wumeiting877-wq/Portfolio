# Gate 3 IBM UI Review

日期：2026-09-22  
视觉 Source of Truth：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`

## 已读取

- [x] IBM-DESIGN.md
- [x] PROJECT-UI-CONSTRAINTS.md

前端编码前已读取上述文件。未新建第二套 token 文件，未改 `tokens.css` 色板。

## 修改文件

```text
frontend/src/api/resources.ts
frontend/src/router/index.ts
frontend/src/stores/auth.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/components/StatusTag.vue
frontend/src/views/resources/ResourceListView.vue
frontend/src/views/resources/ResourceDetailView.vue
PROJECT-UI-CONSTRAINTS.md
```

## 各页面使用的 IBM Token

### 资源列表 `/resources`

| 元素 | Token / 实现 |
| --- | --- |
| 页背景 | `--color-bg-page` = surface-1 `#f4f4f4` |
| 表格面板 | canvas `#ffffff` + 1px hairline `#e0e0e0` + radius 0 |
| 标题 | PageHeader，24px / 400 |
| 说明 | 16px / 400 / 1.5 / 0.16px body |
| 主按钮「新建资源」 | IBM Blue `#0f62fe`，padding 12px 16px，radius 0 |
| 查询/重置 | 现有 secondary：炭黑实心，radius 0 |
| 表格 | 14px，header surface-1，无阴影 |
| 状态 | StatusTag：ACTIVE 用 success `#24a148`；即将到期用 warning；EXPIRED 用 error |
| 筛选间距 | 8px gap，4px grid |

无费用列，无 KPI 色卡，无平台 Logo 墙。

### 新建/编辑 Dialog 与资源类型 Dialog

| 元素 | Token / 实现 |
| --- | --- |
| 容器 | canvas，1px hairline，radius 0，无 box-shadow |
| 输入 | surface-1 底，Carbon 底线 focus |
| 主按钮 | IBM Blue |
| 取消 | charcoal secondary |
| 字段 | 名称、类型、平台、标识、套餐、状态、日期、备注；无价格 |

### 资源详情 `/resources/:id`

| 元素 | Token / 实现 |
| --- | --- |
| Tab | IBM product-tab：16px 20px padding，选中 2px Blue 底线 |
| 概览 | 复用 descriptions：label surface-1，content canvas，1px hairline |
| 分配表 | 与列表同一 list-panel |
| 仅两个 Tab | 概览、分配记录。无费用/账单/成本 Tab |

## IBM-DESIGN 未覆盖场景及处理

| 场景 | IBM-DESIGN | 处理 |
| --- | --- | --- |
| 后台 Sidebar | 营销站只有 top-nav | 保持已校准 Sidebar |
| 数据表格 | 营销提取无 data table | 沿用 hairline table |
| 分页器 | 未定义 | 圆角压到 0；active 用 IBM Blue |
| Dialog | 未定义后台 modal | 无阴影、0 radius、hairline |
| 即将到期 Tag | 无独立 token | 复用 StatusTag warning，0 radius |

原则：IBM 没规定 → 保持稳定结构 → 用现有 IBM Token → 不创造第三套视觉。

## 是否新增自定义视觉规则

没有新色板、新圆角体系、新阴影体系。  
仅扩展 StatusTag 的 `resource` / `allocation` 文案映射。

## 大圆角 / 阴影 / 渐变

- 大圆角：无
- 大阴影：无
- 渐变：无
- KPI 假卡片：无
- 费用 Tab：无

## ADMIN 与只读角色按钮差异

浏览器实测：

- ADMIN：菜单含资源账号 / 人员管理 / 系统账号；列表有「新建资源 / 资源类型」；行内「查看 / 编辑 / 分配 / 停用」；详情分配 Tab 有「新增分配 / 释放」
- MEMBER：菜单仅首页 + 项目管理 + 资源账号；列表只有直接分配给自己的 3 条和「查看」；无使用人筛选；无写按钮

BOSS / PROJECT_MANAGER 的写按钮与 MEMBER 相同（前端隐藏）；后端 403 才是边界。四角色 API 取证见 `GATE3-RESOURCE-SCOPE-VERIFICATION.md`。

## npm build

```text
vue-tsc -b && vite build  成功
```

## 浏览器实测

- `http://localhost:5173/` ADMIN：白底、方正 Sidebar、IBM Blue 选中条，菜单含「资源账号」
- ADMIN `/resources`：7 条资源，写操作可见，无费用列
- ADMIN `/resources/7`：仅概览 / 分配记录；分配记录 3 条跨项目共享
- MEMBER `/resources`：3 条，只读，无写按钮，无使用人筛选

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
[x] 没有 KPI 假数据
[x] 没有费用/账单/成本 Tab
[x] PageHeader 已复用
[x] StatusTag 已复用
[x] ADMIN 写按钮可见
[x] 只读角色无写按钮
[x] 后端才是权限边界
```

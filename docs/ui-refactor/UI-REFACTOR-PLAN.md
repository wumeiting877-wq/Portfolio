# UI 改造计划 — IBM Carbon Enterprise Light

日期：2026-09-21  
前置文档：`DESIGN.md`、`docs/ui-refactor/UI-CURRENT-STATE-AUDIT.md`  
原则：只改前端视觉与布局表达；不改数据库、API、后端、权限语义、路由业务、Store 结构、不删页面字段、不替换 Element Plus。

建议在正式改代码时使用独立分支 `feat/ui-carbon-enterprise`。当前仓库根目录尚无 `.git`，初始化仓库并确认无未提交业务改动后再建分支。

---

## 策略

1. 用 Design Token 覆盖 Element Plus CSS 变量。
2. 先壳层（Layout / Header / Sidebar），再基础控件，再已有业务页。
3. 菜单只保留真实路由：首页、人员管理、系统账号。
4. 项目 / 资源 / 费用页面等模块 API 出现后再做 P1 扩展，不预建空菜单。
5. 每一批改完应能在浏览器走通：登录 → 首页 → 人员（若有权限）→ 系统账号（若有权限）→ 改密 → 退出。

改造顺序（与总提示词一致，结合真实代码裁剪）：

```text
01 Design Token
02 App Layout
03 Header
04 Sidebar
05 Page Header
06 Button / Input / Select
07 Table
08 Filter Bar
09 Status Tag
10 Modal / Drawer（仅统一现有 Dialog；不引入无业务的 Drawer）
11 登录页
12 首页（现有 Dashboard 替代物）
13–18 未建模块延期；人员 / 系统账号作为已有核心页提前纳入 P0 末 / P1 初
```

---

## P0 — 设计系统与壳层（第一批正式改造）

目标：任何人打开后台，第一眼是浅灰页 + 白面板 + IBM Blue，而不是深色模板 + Element 默认蓝。

| ID | 工作项 | 文件 | 验收 |
| --- | --- | --- | --- |
| P0-01 | 新增唯一 Token，映射 `--el-*` | 新建 `frontend/src/styles/tokens.css`；改 `main.ts` 导入顺序 | Primary 为 `#0F62FE`；页面背景 `#F4F4F4` |
| P0-02 | 全局字体与基础 reset | `frontend/src/style.css` | IBM Plex Sans 回退栈；去掉 `#f5f7fa` / Segoe 作为规范色 |
| P0-03 | App Layout 主区 | `AdminLayout.vue` | 主区灰底；内容不贴边；padding 24px 级 |
| P0-04 | Header 48–56px | `AdminLayout.vue` | 白底、底边 `#E0E0E0`；用户 + 角色中文；退出非 Primary |
| P0-05 | Sidebar Light | `AdminLayout.vue` | 去掉 `#1f2a44`；宽 220px；选中态蓝/浅底；菜单仍为三项 |
| P0-06 | Button / Input / Select 高度与圆角 | tokens + 少量全局覆盖 | 主按钮/输入约 40px；圆角 2–4px |
| P0-07 | Table 基础视觉 | tokens + 全局 `.el-table` 覆盖 | 表头 `#F4F4F4`；行高 44–48px；hover 浅灰 |
| P0-08 | Dialog 基础视觉 | tokens | 现有 420/520 弹窗标题与 footer 对齐 DESIGN.md |
| P0-09 | StatusTag | 新建 `frontend/src/components/StatusTag.vue` | 人员/账号状态中文 + 统一色，禁止页面私设 |
| P0-10 | PageHeader | 新建 `frontend/src/components/PageHeader.vue` | 标题 20px + 右侧主操作槽 |

P0 明确不做：新路由、新菜单、分页 API、Drawer、金额组件（尚无费用字段）、安装新 UI 库。

---

## P1 — 已有核心页面 + 登录（视觉统一）

在 P0 token 生效后，按页替换「大 Card + 英文状态」为「Page Header + 白面板 + Table/Filter」。

| ID | 工作项 | 文件 | 验收 |
| --- | --- | --- | --- |
| P1-01 | 登录页 Carbon Light 面板 | `LoginView.vue` | 灰底、20px 标题、全宽主按钮、无 Hero |
| P1-02 | 改密页与登录同语言 | `ChangePasswordView.vue` | 同宽面板、同控件高度 |
| P1-03 | 首页去「假 Dashboard 感」 | `HomeView.vue` | Page Header；真实用户/健康信息；不编造费用 KPI |
| P1-04 | 人员列表 | `EmployeeListView.vue` | Filter Bar 对齐；StatusTag；保留搜索/新建/编辑/停用 |
| P1-05 | 系统账号列表 | `UserListView.vue` | 状态 Tag；角色仍可改（逻辑不变）；创建/重置弹窗视觉统一 |
| P1-06 | 弱化 el-card 阴影或改为普通面板 | 上述 views | 无大阴影、无卡片套卡片 |

P1 仍不创建：项目管理、资源账号、费用记录等页面。

---

## P1 延期（业务模块存在后再做）

以下条目写入计划，**等 Gate 2+ 有真实 API / 路由后再开工**。到时必须先读 `DESIGN.md`，Table 优先。

| ID | 模块 | 视觉要点 |
| --- | --- | --- |
| P1-F01 | 项目管理 | Table：名称、负责人、成员数、状态；禁止项目卡片墙 |
| P1-F02 | 资源账号 | Table + 到期状态 Tag；与系统账号导航文案分离 |
| P1-F03 | 费用记录 / 统计 | 金额只走 `¥ 1,280.00`；Dashboard 仅少量摘要 Card |
| P1-F04 | `formatMoney` | `frontend/src/utils/formatMoney.ts` 与费用页同期 |

---

## P2 — 细节与后续模块

| ID | 工作项 | 说明 |
| --- | --- | --- |
| P2-01 | 空状态 / Loading 文案统一 | 表格 empty 文案、按钮 loading，不引插画库 |
| P2-02 | 分页视觉 | 仅当列表 API 真正分页后 |
| P2-03 | 角色中文映射抽公共 | Header、首页、账号表共用，不改角色 code |
| P2-04 | 成员 / 人员文案 | 若产品确认「人员管理」更名「成员管理」，只改显示文案与菜单字，不改路由除非产品要求 |
| P2-05 | 权限 / 设置页 | 模块存在后再做；现在没有独立设置路由 |
| P2-06 | Drawer 规范落地 | 有详情长表单再引入 `el-drawer` |
| P2-07 | 表格操作列密度 | 32px text 按钮间距 8px 的逐页打磨 |
| P2-08 | 无障碍焦点 | 键盘焦点环使用 `--color-focus` |

---

## 批次建议（给下一轮执行）

**Batch A（建议第一批改这些文件）：**

```text
frontend/src/styles/tokens.css          （新建）
frontend/src/style.css
frontend/src/main.ts
frontend/src/layouts/AdminLayout.vue
```

**Batch B：**

```text
frontend/src/components/PageHeader.vue  （新建）
frontend/src/components/StatusTag.vue   （新建）
frontend/src/views/login/LoginView.vue
frontend/src/views/login/ChangePasswordView.vue
frontend/src/views/home/HomeView.vue
```

**Batch C：**

```text
frontend/src/views/employees/EmployeeListView.vue
frontend/src/views/users/UserListView.vue
```

每批结束后用真实角色回归：`admin` / `boss` / `pm` / `member` 的菜单可见性必须与现在一致。

---

## 风险与约束

| 风险 | 处理 |
| --- | --- |
| 覆盖 Element Plus 变量影响所有控件 | Token 只改色、半径、字体；不重写组件 JS |
| 侧栏改浅色后对比度不足 | 选中用 `#D0E2FF` + 明确当前项，不用浅灰字配浅灰底 |
| Warning 黄 `#F1C21B` 上白字不可读 | StatusTag 警告态用深字 `#161616` |
| 把营销站 0px 直角套到 Element | 采用 DESIGN.md 的 2–4px，避免控件裁切异常 |
| 无 git 仓库误覆盖本地改动 | 初始化 git 后先 `git status`；有用户改动则禁止覆盖 |

---

## 本轮（准备轮）完成定义

已完成即可停止：

- [x] 扫描真实前端
- [x] 拉取 `awesome-design-md`
- [x] 定位 IBM / Carbon 设计文件
- [x] 编写 `DESIGN.md`
- [x] 编写本审计与本计划
- [x] `.gitignore` 忽略 `design-reference/`
- [ ] **不**开始大规模改页面（本文件发布时仍未改 views/layouts 业务 UI）

下一轮入口：用户确认 `DESIGN.md` 与本计划后，从 P0-01 Token 开始。

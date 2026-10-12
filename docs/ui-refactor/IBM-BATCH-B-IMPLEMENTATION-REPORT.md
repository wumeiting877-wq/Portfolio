# IBM UI Batch B 实施报告

日期：2026-09-22  
范围：`PageHeader.vue`、`StatusTag.vue`、`LoginView.vue`、`ChangePasswordView.vue`、`HomeView.vue`，以及上述页面真正需要的少量全局样式。  
视觉来源：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`  
结论：完成；`npm run build` PASS；`/login`、`/change-password`、`/` 业务回归 PASS；未修改业务逻辑。

未读取、未引用 `DESIGN-PROJECT-ADAPTATION-ARCHIVE.md` 作为视觉规则。

---

## 1. 修改文件

- `frontend/src/views/login/LoginView.vue`
  - 保留登录校验、`auth.login`、成功跳转（含 `must_change_password`）与错误提示。
  - 去掉 `el-card` 与自定义 `#eef2f6` 背景。
  - 文案标签由「用户名」改为「系统账号」；绑定字段仍是 `form.username`。
- `frontend/src/views/login/ChangePasswordView.vue`
  - 保留原密码 / 新密码字段、至少 8 位校验、提交与返回首页逻辑。
  - 与登录页共用 `.auth-page` / `.auth-panel` 视觉容器。
- `frontend/src/views/home/HomeView.vue`
  - 保留现有用户、角色、scope、账号状态与健康检查数据。
  - 用 `PageHeader` 替换页面标题；用 `StatusTag` 展示角色、账号状态与健康结果。
  - 去掉外层 `el-card`，保留两列 `el-descriptions` 信息结构。
- `frontend/src/style.css`
  - 仅增加认证页容器、标题、说明、表单标签与全宽登录按钮样式。
  - 未改 Button / Input 的已校准 IBM 规则，未改 Layout。

未修改：

- `EmployeeListView.vue`
- `UserListView.vue`
- `AdminLayout.vue`
- `tokens.css`
- `backend/`、Router、Store、API、Axios、权限

---

## 2. 新增文件

- `frontend/src/components/PageHeader.vue`
- `frontend/src/components/StatusTag.vue`
- `docs/ui-refactor/IBM-BATCH-B-IMPLEMENTATION-REPORT.md`

---

## 3. 每个组件对应 IBM-DESIGN.md 的哪些规则

### PageHeader

IBM-DESIGN.md **没有**后台 PageHeader 组件。

最小结构：标题 + 可选说明 + 右侧 `actions` 插槽。

使用的已有规则：

| 部位 | IBM 规则 |
| --- | --- |
| 标题 | `typography.card-title`：24px / 400 / 1.33 / letter-spacing 0；`colors.ink` |
| 说明 | `typography.body`：16px / 400 / 1.50 / 0.16px；`colors.ink-muted` |
| 间距 | `spacing.xs` 8px、`spacing.md` 16px、`spacing.lg` 24px |
| 形状 | `rounded.none` 0px；无阴影、无装饰图标、无渐变、无大 Card |

### StatusTag

IBM-DESIGN.md **没有** Status Tag 组件。

最小实现：中文展示 + IBM Semantic Color + hairline + square。

使用的已有规则：

| 部位 | IBM 规则 |
| --- | --- |
| 成功 | `colors.semantic-success` `#24a148` |
| 警告 | `colors.semantic-warning` `#f1c21b` 作为描边；文字用 `colors.ink`，避免黄字对比不足 |
| 错误 | `colors.semantic-error` `#da1e28` |
| 中性 | `colors.hairline` + `colors.ink-muted` |
| 字体 | `typography.caption`：12px / 400 / 1.33 / 0.32px |
| 形状 | `rounded.none` 0px；`canvas` 白底；1px hairline |
| 禁止项 | 未做大胶囊、高饱和实心填色、阴影、渐变 |

角色映射使用中性色，不使用 success / error / IBM Blue。

### LoginView / ChangePasswordView

| 部位 | IBM 规则 |
| --- | --- |
| 页面底 | `colors.surface-1` `#f4f4f4` |
| 容器 | `colors.canvas` 白底、1px `hairline`、`rounded.none`、无 drop shadow |
| 标题 | `typography.card-title` + `colors.ink` |
| 说明 | `typography.body` + `colors.ink-muted` |
| 输入框 | `text-input`：Surface 1、0px radius、16px body、11px 16px padding |
| Focus | 2px IBM Blue 底线（沿用已校准全局 Input） |
| 主按钮 | `button-primary`：`#0f62fe`、0px radius、12px 16px padding、14px button |
| 次按钮 | `button-secondary`：Charcoal 实心（改密页「返回」） |

### HomeView

| 部位 | IBM 规则 |
| --- | --- |
| 页面 | 沿用 Layout 的 Surface 1 |
| 标题 | PageHeader / `card-title` / ink，不用 IBM Blue |
| 信息区 | 1px hairline；label 用 Surface 1 + `body-sm` 14px；value 用 Canvas + `body` 16px |
| 层级 | Elevation：hairline + surface change；无 box-shadow |
| 状态 | StatusTag；IBM Blue 不作为 Tag 主色 |

---

## 4. LoginView 改动

业务逻辑未改。视觉改动：

- 去掉圆角 Card 和大阴影。
- 登录容器改为 420px、`max-width: 100%` 的方形 hairline 面板。
- 只保留真实内容：系统名、已有说明「请使用系统账号登录」、系统账号、密码、登录。
- 未增加 IBM Logo、Hero、渐变背景、注册、忘记密码。
- 运行时计算值（浏览器）：
  - Input background `rgb(244, 244, 244)`，radius `0px`，padding `11px 16px`
  - Primary button background `rgb(15, 98, 254)`，radius `0px`，padding `12px 16px`
  - Panel background `rgb(255, 255, 255)`，radius `0px`，`box-shadow: none`

---

## 5. ChangePasswordView 改动

与 LoginView 使用同一套 `.auth-page` / `.auth-panel`。

保留：

- 原密码、新密码
- 新密码至少 8 位
- `auth.changePassword`
- 成功后 `router.push({ name: "home" })`
- 「返回」到首页

未创建第二套认证页风格。未提交真实改密，避免污染开发账号。

---

## 6. HomeView 改动

未制造假 Dashboard（无项目 / 费用 / 资源统计）。

保留并重新组织的真实信息：

| 项 | 展示 |
| --- | --- |
| 当前用户 | `username` 原文 |
| 姓名 | `employee_name`，空则为 `-` |
| 当前角色 | StatusTag 中文 + 真实 role code |
| 数据范围 | `scope` 原文 |
| 账号状态 | StatusTag：`ACTIVE` → 启用 |
| 系统状态 | 后端 / 数据库健康，StatusTag：`正常` / `不可用` / `检查中...` |

未把后台信息做成 Marketing Feature Card 网格。

---

## 7. 是否出现 IBM-DESIGN.md 未覆盖的场景

是。明确未覆盖：

1. 后台 PageHeader
2. Status Tag / Badge 组件规格
3. 产品后台 Dashboard / Descriptions 信息表
4. 认证页整体构图（营销站没有本系统登录页）
5. 角色 Tag 的语义色（任务已规定角色不是 success / error）
6. `LEFT`（离职）是否属于 error
7. 警告黄 `#f1c21b` 作为文字色时的对比度

---

## 8. 对于未覆盖场景如何处理

按最高级规则第 6 条：**IBM 没有明确规则 → 保持当前稳定结构，不创造第三套设计体系。**

- PageHeader：只做标题 / 说明 / 操作槽，字体与颜色全部取自已有 Typography / Color。
- StatusTag：只做映射与最小 hairline 标签；角色与 `LEFT` 使用中性色，不用绿/红表示角色或离职。
- 警告色：黄用作 1px 描边，文字保持 ink，避免不可读黄字。
- 首页：保留两列 descriptions，只统一颜色、字体、hairline。
- 认证页：用 Canvas + hairline + Surface 1 输入 + Primary Button 组合，不引入 Hero / CTA Banner。

---

## 9. Build 结果

命令：

```text
npm run build
```

结果：PASS。

- `vue-tsc -b` 通过
- Vite 生产构建通过
- 1710 modules transformed
- 构建耗时约 5.13s
- IDE 对本轮 Vue / CSS 文件未报告 lint error

非阻塞警告（原有问题，本批未扩大处理）：

- 主 JS chunk 约 1,114.25kB（gzip 约 369.19kB），超过 Vite 500kB 阈值
- npm 报告本机未知 `devdir` 配置

---

## 10. 业务回归结果

在当前 Docker 服务（frontend / backend / PostgreSQL 均运行）中，用真实 `admin` 账号走浏览器：

| 项 | 结果 |
| --- | --- |
| `/login` 渲染 | PASS。系统名、系统账号、密码、登录按钮可见；方形白面板 + Surface 1 输入 + IBM Blue 主按钮 |
| 登录 | PASS。成功进入 `/` |
| `/` 渲染 | PASS。PageHeader「首页」；用户 / 角色 / scope / 账号状态 / 系统健康均在；无假 KPI |
| `/change-password` 访问 | PASS。从 Header「修改密码」进入；原密码 / 新密码 / 保存 / 返回可见 |
| 未登录访问 `/change-password` | PASS。守卫仍重定向到 `/login` |
| 退出 | PASS。返回 `/login` |
| 权限 / Router | 未改文件；ADMIN 菜单仍为首页、人员管理、系统账号 |

本轮未修改任何账号的 `must_change_password` 数据，也未提交改密表单。

---

## 11. 是否修改业务逻辑

否。

未修改：

- backend / database / API
- Axios
- Router 定义、守卫与业务语义
- Pinia Store
- 权限、role code
- 登录逻辑、`must_change_password`、退出逻辑
- 人员字段、系统账号字段

未新增：

- 项目管理、资源管理、费用管理、费用统计、角色权限、系统设置

---

## 12. 下一批建议

等待下一轮明确指令后再执行，建议范围：

```text
frontend/src/views/employees/EmployeeListView.vue
frontend/src/views/users/UserListView.vue
```

在这两页接入本轮已完成的 `PageHeader` 与 `StatusTag`，统一表格 / 筛选 / 对话框的 IBM 视觉，仍不得改人员字段、账号字段、权限与 API。

本轮到此停止，不进入人员列表、系统账号列表、项目、资源或费用。

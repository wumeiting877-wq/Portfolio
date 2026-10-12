# UI 现状审计

日期：2026-09-21  
范围：只读扫描当前仓库前端，不改业务代码。  
对照基线：IBM Carbon Enterprise Light（见仓库根目录 `DESIGN.md`）  
参考提取：`design-reference/awesome-design-md/design-md/ibm/DESIGN.md`

---

## 1. 项目根目录与前后端位置

```text
F:\XM\X_10 project\
  frontend\                 前端（独立 Vite 工程）
  backend\                  FastAPI
  docs\                     Gate 交付报告
  docker-compose.yml
  README.md
  DESIGN.md                 本轮新建
  design-reference\         本轮克隆的设计参考（已加入 .gitignore）
```

前端目录：`frontend/`  
API 目录：`frontend/src/api/`  
页面目录：`frontend/src/views/`

---

## 2. 前端技术栈

| 项 | 现状 |
| --- | --- |
| 框架 | Vue 3.5（Composition API + `<script setup>` + TypeScript） |
| 构建 | Vite 6 |
| 语言 | TypeScript |
| 路由 | Vue Router 4（`createWebHistory`） |
| 状态 | Pinia 3（`auth`、`user`） |
| HTTP | Axios |
| UI 库 | Element Plus 2.9（全量注册 + 中文 locale） |
| CSS | 原生 CSS；无 Tailwind、无 Sass 工程化、无 CSS Modules 体系 |
| 图表 | 无 |
| 原子化 / 第二组件库 | 无 |

结论：后续用 **Element Plus + Carbon Token + 全局 CSS**，禁止再装 `@carbon/react` 或 Ant Design。

---

## 3. 前端结构

```text
frontend/src/
  main.ts                   入口：Pinia + Router + Element Plus + style.css
  App.vue                   仅 <RouterView />
  style.css                 全局：margin 0、背景 #f5f7fa、Segoe UI
  vite-env.d.ts
  router/index.ts           路由与登录守卫
  layouts/AdminLayout.vue   后台壳层
  stores/auth.ts            token、profile、权限 getter
  stores/user.ts            displayName
  api/http.ts               Axios 拦截器
  api/auth.ts
  api/users.ts
  api/employees.ts
  api/health.ts
  views/login/LoginView.vue
  views/login/ChangePasswordView.vue
  views/home/HomeView.vue
  views/employees/EmployeeListView.vue
  views/users/UserListView.vue
  components/               仅 .gitkeep，无公共组件
  utils/                    仅 .gitkeep，无 formatter
```

没有 `src/styles/`，没有 Design Token 文件。

---

## 4. 路由

| path | name | 组件 | 权限 | 公共 |
| --- | --- | --- | --- | --- |
| `/login` | login | LoginView | 未登录 | 是 |
| `/change-password` | change-password | ChangePasswordView | 已登录；`must_change_password` 时强制进入 | 否 |
| `/` | home | AdminLayout → HomeView | 已登录 | 否 |
| `/employees` | employees | EmployeeListView | `ADMIN`、`BOSS` | 否 |
| `/users` | users | UserListView | `ADMIN` | 否 |

守卫逻辑：无 token 去登录；拉 `/api/auth/me`；必须改密则打断；角色不匹配回首页。  
本轮审计 **禁止修改** 该业务逻辑。

未实现路由：项目、资源、费用、设置、角色配置页。

---

## 5. Layout

`AdminLayout.vue`：

- `el-container` 全高
- `el-aside width="220px"`，背景 **`#1f2a44`**，菜单 `background-color="#1f2a44"`，字 `#dbe4f0`，激活白字
- 品牌区高度 **60px**，文案「项目费用中枢」
- `el-header` 白底，底边 `#ebeef5`，左右：`姓名 / role_name`、修改密码、退出（退出为 `type="primary" plain`）
- `el-main` 未自定义 padding（走 Element Plus 默认，通常 20px）
- 菜单仅三项：首页、人员管理、系统账号（按权限 v-if）

这是常见深色模板壳，不是 Carbon Light。侧栏宽度 220px 符合目标，颜色与字色不符合。

---

## 6. 页面清单与形态

| 页面 | 形态 | 主要组件 |
| --- | --- | --- |
| 登录 | 居中 `el-card` 420px，背景 `#eef2f6`，h1 22px | Form + Input + Primary Button |
| 改密 | 居中 `el-card` 460px，无后台壳 | Form |
| 首页 | 一张 `el-card` + `h2` + `el-descriptions` | 无统计图、无 Table |
| 人员 | 一张 `el-card` 包工具条 + Table + Dialog | 搜索、查询、新建、行内编辑/停用 |
| 系统账号 | 一张 `el-card` 包工具条 + Table + 两个 Dialog | 创建、改角色、重置密码、启停 |

列表页方向正确（Table，不是卡片流）。问题是整页包在默认可阴影 Card 里，没有 Page Header，状态是英文枚举原文。

---

## 7. 样式结构

| 层 | 内容 |
| --- | --- |
| Element Plus 默认主题 | Primary `#409EFF`（rgb 64,158,255），圆角 4px / 2px，成功绿 `#67C23A` 系 |
| `frontend/src/style.css` | 页面背景 `#f5f7fa`，字体 `"Segoe UI", "PingFang SC", sans-serif` |
| 页面 scoped | 登录/改密/Layout/工具条少量硬编码 |
| Token | **不存在** |

当前主色实际是 **Element Plus 蓝 `#409EFF`**，不是 IBM Blue `#0F62FE`。  
当前页面背景是 **`#f5f7fa` / `#eef2f6`**，不是 Carbon `#F4F4F4`。

---

## 8. 公共组件

无。状态、页头、金额、空状态都在页面内联。

---

## 9. 当前视觉参数（实测自源码，非猜测官网）

| 参数 | 当前值 |
| --- | --- |
| 主色 | Element Plus `#409EFF`；侧栏另用 `#1f2a44` |
| 页面背景 | `#f5f7fa`（全局）、`#eef2f6`（登录） |
| 面板 | `el-card` 默认白 + 默认阴影/圆角 |
| 主文字 | 浏览器/Element 默认，登录说明 `#606266` |
| 边框 | Header `#ebeef5`；其余 Element 默认 |
| 圆角 | Element `--el-border-radius-base: 4px` |
| 间距 | 工具条 `gap: 8px`、`margin-bottom: 16px`（人员页较好）；页面级未统一 24px |
| Header 高 | Element 默认 60px |
| Sidebar 宽 | 220px |
| 品牌区高 | 60px |
| 按钮 | 默认尺寸；退出误用 Primary plain |
| Input | 默认约 32px，未拉到 40px |
| Table 行高 | Element 默认（偏 40–48，未锁定 44–48 token） |
| Table 表头 | 默认白/浅底，未用 `#F4F4F4` 结构化表头 |
| 状态 | 纯文本 `ACTIVE` 等，无 Tag |
| Modal | `el-dialog` 420 / 520px，有 footer |
| Drawer | **未使用** |
| Pagination | **未使用** |
| Filter | 人员页有简单工具条；账号页只有「创建账号」 |
| 金额 | **无**（业务尚未有费用字段） |

---

## 10. Store / API（只记录，不改）

Store：`auth`（token、profile、canViewEmployees、canWriteEmployees、canManageUsers）、`user`（displayName）。  
API：`/api/auth/*`、`/api/employees`、`/api/users`、`/api/roles`、`/health`、`/health/db`。  
后端角色：`ADMIN` / `BOSS` / `PROJECT_MANAGER` / `MEMBER`。

---

## 11. 对照 Carbon：已符合

1. **列表用 Table，而不是记录级大 Card** — 人员、系统账号已是表格。
2. **侧栏宽度 220px** — 落在 220–240 建议区间。
3. **后台信息架构扁平、菜单少** — 与当前真实业务匹配，没有假的炫酷导航。
4. **弹窗短表单 + footer 取消/保存** — 接近企业后台习惯。
5. **中文后台、无营销 Hero、无玻璃拟态、无图表大屏** — 没有走 SaaS 官网或 Crypto 风。
6. **工具条 gap 8px、表格上边距 16px** — 人员页密度已经接近目标，不是 40–60px 大留白。
7. **无 Tailwind 营销组件、无第二套 UI 库** — 改造成本可控。

---

## 12. 对照 Carbon：需要修改（下一轮，非本轮）

1. 建立 `frontend/src/styles/tokens.css`，把 Element Plus `--el-color-primary` 等映射到 IBM Blue / Gray。
2. Layout：侧栏改为 Light，去掉 `#1f2a44`；Header 压到 48–56px；主区背景 `#F4F4F4`。
3. 字体改为 IBM Plex Sans 栈；去掉 Segoe UI 作为品牌声。
4. 登录/改密：背景与标题尺寸按 DESIGN.md 收敛。
5. 列表页：Page Header + 白面板，弱化 `el-card` 阴影；统一 Filter Bar。
6. Table：表头底、行高、hover、空状态。
7. `StatusTag`：人员/账号状态中文 + 统一色。
8. 角色展示中文，避免 Header 里只丢 `role_name` 与英文 code 混排（首页目前 `role_name / role`）。
9. Header「退出」改为次要按钮。
10. Button/Input 高度与主色。

---

## 13. 禁止修改（本阶段与后续 UI 轮次默认遵守）

| 禁止 | 原因 |
| --- | --- |
| 改数据库 / Alembic / 模型 | 非 UI 范围 |
| 改 FastAPI、权限、Scope、审计 | 非 UI 范围 |
| 改登录守卫业务语义、删路由、改 Store 结构 | 会破坏 Gate 1 |
| 删页面或字段（工号、绑定人员、角色下拉等） | 业务完整性 |
| 为「设计菜单」创建项目/资源/费用空页面 | 业务尚不存在 |
| `npm install @carbon/react` 或再装 Ant Design | 双框架 |
| 把 `awesome-design-md` 打进前端产物 | 仅设计参考 |
| 复制 IBM 官网 Hero、深色 Footer、76px 标题 | 营销站 ≠ 后台 |
| 把列表改成卡片流 | 违反 Table 核心原则 |

---

## 14. 当前 UI 最大的不统一问题（Top 5）

1. **双套主色**：侧栏海军蓝模板 + Element Plus `#409EFF`，没有 IBM Blue，也没有全局 Token。
2. **壳层是 Dark Admin Template，内容是默认 Element 浅色**，和 Carbon Light（灰页 + 白面板）不是同一语言。
3. **状态与角色裸奔**：表格和首页直接渲染 `ACTIVE`、`DISABLED`、`ADMIN` 等枚举，没有 StatusTag，也没有全站中文状态色板。
4. **列表容器与页头不统一**：每页一个 `el-card` + 随意 `h2`，没有 Page Header / Filter Bar 规范；登录另用 22px 标题和第三种背景色。
5. **控件尺寸未按后台密度锁定**：Header 60px、Input 默认高度、退出按钮 Primay、无统一 40px 控件、无表格行高约定。

---

## 15. 建议第一批修改的文件（下一轮 P0，本轮不动）

仅视觉与布局 CSS，不改 API 调用语义：

1. `frontend/src/styles/tokens.css`（新建）
2. `frontend/src/style.css`
3. `frontend/src/main.ts`（增加 token 导入顺序）
4. `frontend/src/layouts/AdminLayout.vue`
5. `frontend/src/views/login/LoginView.vue`
6. `frontend/src/views/home/HomeView.vue`
7. `frontend/src/views/employees/EmployeeListView.vue`
8. `frontend/src/views/users/UserListView.vue`
9. `frontend/src/components/StatusTag.vue`（新建，只做展示映射）
10. `frontend/src/components/PageHeader.vue`（新建，可选与 6–8 同期）

改密页 `ChangePasswordView.vue` 可紧随登录页一起做，仍属壳层/基础视觉，不碰密码 API 逻辑。

---

## 16. Git 与设计参考

扫描时工作区 **不是 git 仓库**（根目录无 `.git`），无法 `git checkout -b feat/ui-carbon-enterprise`。  
`design-reference/` 已写入根目录 `.gitignore`，避免将来初始化仓库时把第三方设计仓库提交进去。  
`DESIGN.md` 与 `docs/ui-refactor/` 应进入业务仓库。

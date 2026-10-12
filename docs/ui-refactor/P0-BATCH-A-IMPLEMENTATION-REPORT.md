# P0 / Batch A 实施报告

日期：2026-09-22  
范围：IBM Carbon Enterprise Light Token、全局基础样式、应用 Layout / Header / Sidebar。  
结论：完成；业务逻辑、权限语义和路由定义未修改。

## 1. 修改文件

- `frontend/src/main.ts`
  - 保持 Element Plus、Pinia、Router、locale 与 mount 逻辑不变。
  - CSS 顺序调整为：Element Plus 原始 CSS → `tokens.css` → `style.css`。
- `frontend/src/style.css`
  - 增加全局 `box-sizing`。
  - 统一根节点高度、页面背景、文字、14px 正文与 IBM Plex Sans 字体栈。
  - Default / Primary Button 与默认 Input / Select 的基础高度统一到约 40px。
  - Text Button 未强制放大，保留表格行内操作后续压缩空间。
- `frontend/src/layouts/AdminLayout.vue`
  - 将深色后台壳层改为 Carbon Light。
  - 保留原菜单、路由跳转、权限判断与退出流程。
  - 增加纯展示层角色中文 fallback，不修改 Store 或角色 code。

构建验证同时生成了已忽略的 `frontend/dist/` 产物，不属于源代码改造。

## 2. 新增文件

- `frontend/src/styles/tokens.css`
- `docs/ui-refactor/P0-BATCH-A-IMPLEMENTATION-REPORT.md`

未创建 `PageHeader.vue`、`StatusTag.vue`，未进入 Batch B。

## 3. Token 内容

`tokens.css` 是当前前端唯一 Design Token 来源，包含：

- IBM Blue：Primary、Hover、Active、Pressed
- Surface：Page、Panel、Subtle、Hover、Selected
- Text：Primary、Secondary、Muted、Placeholder、Disabled、On Primary
- Border / Focus
- Success / Warning / Danger / Info 及语义浅色背景
- Link / Link Hover
- 2px / 4px / 6px 圆角
- 4px–32px 间距网格
- 两级弱阴影
- IBM Plex Sans 字体栈

主色为 `#0F62FE`，页面背景为 `#F4F4F4`，面板为 `#FFFFFF`。

## 4. Element Plus 覆盖项

覆盖范围保持精简：

- `--el-color-primary` 及必要的 Primary light / dark 交互色
- Success / Warning / Danger / Error / Info
- Primary / Regular / Secondary / Placeholder / Disabled 文字
- Border、Light Border、Lighter Border
- Page / Panel / Light Fill
- Base / Small Radius
- Font Family / Base Font Size

运行时计算结果：

- `--el-color-primary`: `#0f62fe`
- Sidebar: `rgb(255, 255, 255)`、宽 `220px`
- Header: 白色、`52px`、无阴影
- Main: `rgb(244, 244, 244)`、padding `24px`
- Active Menu: `rgb(208, 226, 255)` + IBM Blue 左边线

未复制整套 Element Plus Theme，未安装新 UI 框架。

## 5. Layout 改动

- Sidebar 仍为 220px。
- 工作区增加 `min-width: 0`，避免内容溢出破坏横向布局。
- Header 固定 52px。
- Main 使用 `#F4F4F4` 与 24px padding。
- 所有尺寸和颜色引用 Design Token。

现有 View 结构未修改，因此当前仍是“灰色 Main + 原有 el-card”的 Batch A 中间状态。

## 6. Header 改动

- 高度：52px。
- 背景：白色。
- 底边：1px `#E0E0E0`。
- 阴影：无。
- 保留用户、角色、修改密码、退出。
- 退出从 Primary Plain 改为 Text 次级操作。
- 优先显示后端已有 `role_name`；缺失时在 Layout 展示层映射：
  - `ADMIN` → 管理员
  - `BOSS` → 老板
  - `PROJECT_MANAGER` → 负责人
  - `MEMBER` → 成员

未新增通知、搜索、主题切换或消息中心。

## 7. Sidebar 改动

- 背景从 `#1f2a44` 改为白色。
- 右边增加 1px `#E0E0E0` 分隔线。
- 品牌区保留「项目费用中枢」，高度 52px、16px / 600。
- 菜单项高度 44px。
- 默认文字 `#525252`。
- Hover 使用 `#E8E8E8`。
- Active 使用 `#D0E2FF` + 3px IBM Blue 左边线。
- 菜单仍只有首页、人员管理、系统账号；可见性判断保持原样。

## 8. 是否修改业务逻辑

否。

未修改：

- `backend/`
- 数据库 / Alembic / API
- Axios
- Router 定义与守卫
- Pinia Store
- 登录、强制改密、退出业务逻辑
- 角色 code 与权限 getter
- 人员 / 系统账号字段和业务状态
- 任何业务 View

## 9. Build 结果

命令：

```text
npm run build
```

结果：PASS。

- `vue-tsc -b` 通过
- Vite 生产构建通过
- 1705 modules transformed
- 构建耗时约 9.43s

非阻塞警告：

- 主 JS chunk 超过 Vite 默认 500kB 阈值（约 1,114kB，gzip 约 369kB）
- 该问题在改造前的全量 Element Plus 注册架构下存在，本批不扩大范围处理
- npm 报告本机存在未知 `devdir` 配置，该配置不属于项目代码

## 10. Lint / Test 结果

`frontend/package.json` 只有：

- `dev`
- `build`
- `preview`

没有 lint、test 或独立 typecheck 脚本，因此未执行不存在的命令。TypeScript 检查已由 `npm run build` 中的 `vue-tsc -b` 完成。

## 11. 路由回归结果

在当前 Docker 服务（frontend / backend / PostgreSQL 均运行）中通过真实浏览器验证：

- `/login`: PASS，登录表单可访问
- `/`: PASS，登录后首页可访问
- `/employees`: PASS，ADMIN 可访问并加载人员列表
- `/users`: PASS，ADMIN 可访问并加载系统账号列表
- `/change-password`: PASS，原密码 / 新密码表单正常渲染
- 退出：PASS，返回 `/login`

强制改密相关 Router 与 Store 代码未修改；`/change-password` 路由可访问。本轮未修改任何账号的 `must_change_password` 数据来制造测试场景，避免测试污染真实数据。

## 12. 权限回归结果

使用当前真实开发账号登录验证：

- ADMIN：显示首页、人员管理、系统账号；`/employees`、`/users` 均可访问。
- BOSS：显示首页、人员管理；不显示系统账号；直接访问 `/users` 被守卫重定向到 `/`。
- PROJECT_MANAGER：只显示首页；直接访问 `/employees` 被守卫重定向到 `/`。
- MEMBER：只显示首页；直接访问 `/users` 被守卫重定向到 `/`。

四类角色 code 和权限 getter 均未修改。

## 13. Git / 文件保护

执行 `git status` 返回：

```text
fatal: not a git repository (or any of the parent directories): .git
```

按要求只记录，未执行 `git init`，未创建分支。

## 14. 剩余问题

- 登录、改密、首页、人员、系统账号仍保留原 View 内局部视觉；这是 Batch A 的预期中间状态。
- 页面 Card、Page Header、StatusTag、表格状态枚举尚未统一。
- IBM Plex Sans 未打包字体文件；当前按规范使用字体栈，未安装额外依赖。
- 主 bundle 较大，后续可单独评估 Element Plus 按需引入，但不应与 UI 批次混做。
- 当前项目无前端自动化测试和 lint 脚本。

## 15. 下一步 Batch B 建议

等待下一轮明确指令后再执行：

1. 新建 `PageHeader.vue`
2. 新建 `StatusTag.vue`
3. 统一 `LoginView.vue`
4. 统一 `ChangePasswordView.vue`
5. 统一 `HomeView.vue`

本轮不自动进入 Batch B。

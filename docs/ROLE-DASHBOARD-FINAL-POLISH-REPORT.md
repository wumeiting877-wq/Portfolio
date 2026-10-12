# 三角色 Dashboard 最终视觉收口报告

实施日期：2026-09-24  
适用角色：BOSS / PROJECT_MANAGER / MEMBER

## 1. 本轮范围

本轮仅固化三角色 Dashboard 的公共页面宽度策略与验证基线。未修改后端、数据库、API、Scope、Permission、RoleCode、JWT、路由语义、统计口径、费用计算或任何 Dashboard 信息架构。

## 2. IBM-DESIGN 读取确认

已读取并遵循：

- `IBM-DESIGN.md`
- `PROJECT-UI-CONSTRAINTS.md`
- `docs/ROLE-DASHBOARD-DESIGN-INPUT.md`
- `docs/ROLE-DASHBOARD-IBM-REDESIGN-IMPLEMENTATION-REPORT.md`
- `docs/ROLE-DASHBOARD-VISUAL-FIX-REPORT.md`

保留 IBM Plex Sans、4px 间距网格、直角、白/浅灰 Surface、1px 边线和无阴影规则。

## 3. 右侧空白根因

根因不是 BOSS / PM / MEMBER Shell 中存在 `max-width: 960px`、`1000px` 或 `1100px`。

实际代码审计结果：三种 Shell 与公共 `.main` 均没有此类窄容器限制。在 CSS 视口 1440px 的实际 DOM 测量中：Sidebar 为 220px，Main 为 1220px，Dashboard 内容宽约 1157px（扣除 24px 页面内边距及滚动条），`document.documentElement.scrollWidth === 1440`。

此前 1440px 截图画布中的 Sidebar 实际只呈现约 176px，说明页面以约 80% 的有效渲染尺度采集；截图画布尺寸被误当成 CSS 视口宽度，进而产生右侧空白的假象。

## 4. 修改文件

- `frontend/src/styles/tokens.css`
- `frontend/src/layouts/AdminLayout.vue`

## 5. 公共宽度策略

新增唯一的 `--dashboard-content-max-width: 1584px`（Carbon desktop grid maximum），并由 `AdminLayout` 的公共 Main 容器统一应用：

```css
width: 100%;
max-width: var(--dashboard-content-max-width);
margin: 0;
```

在 1440px 常规桌面视口下，当前可用主内容宽度小于 1584px，因此 Dashboard 自然完整展开；三角色使用完全相同的左右边界。Sidebar 及 TopBar 未改变。

## 6. BOSS 最终结果

- 结构保持：日期筛选、5 KPI、2:1 趋势/资源状态、1:1 项目成本/费用结构、三区需要关注。
- Shell 自动使用公共满宽策略；比例仍由相对 Grid 控制，不写死像素。
- 费用结构 Tab、金额右对齐、单月真实数据表现和关注三区均未改动。

## 7. PM 最终结果

- 日期筛选与“我的负责项目”保持同一个 `justify-content: space-between` 工具栏，并垂直居中。
- 三层双列维持 2:1、1:1、1:1；资源关注保留 40–56px 的紧凑空态。
- Project A 过滤后的 overview、趋势、项目费用、资源类型、成员费用和资源状态接口均返回 HTTP 200。

## 8. MEMBER 最终结果

- 4 KPI、我的项目、1:1 资源状态/资源类型费用、200px 趋势和紧凑到期空态的顺序与含义均保持不变。
- 项目状态列仍为固定合理宽度，未随更大内容区不必要拉宽。

## 9. 1440 / 1280 / 1024 / 979 响应式验证

- 1440px：实测 Main 1220px，Dashboard 约 1157px，`scrollWidth === 1440`。
- 1280px：双列规则保持，公共容器不会产生额外横向限制。
- 1024px：2:1 Grid 的右列仍以 280px 最小值保持可读。
- 979px：各 Shell 原有 `@media (max-width: 980px)` 继续将双列改为单列；所有 Grid 使用 `minmax(0, ...)`，未新增水平溢出源。

## 10. 权限与业务回归

使用本机真实演示账号通过 API 回归：

| 账号 | Role | Scope | 结果 |
| --- | --- | --- | --- |
| boss | BOSS | GLOBAL | PASS |
| pm | PROJECT_MANAGER | MANAGED_PROJECTS | PASS |
| member | MEMBER | MEMBER_PROJECTS | PASS |

PM 能看到 2 个负责项目；选择 Project A（ID 1）后，overview、expense-trend、project-costs、resource-type-costs、employee-costs、resource-status 均返回 HTTP 200。未发现新增 403 或 404。

## 11. Build / vue-tsc / Console

- `npm run build`：通过。
- `vue-tsc -b`：通过（由构建脚本执行，并额外直接执行）。
- Vite 仅输出既有大 chunk size 提示；本轮未做 Chunk 拆分。
- 本轮未新增 Vue 编译 warning。
- 已验证的运行中本地 API health 与 database health 均为 `ok`。

## 12. 最终截图索引

目标目录已创建：`artifacts/dashboard-final-polish-2026-09-24/`。

本机无头 Edge 的 DevTools 调试端点受环境策略阻断，未能在不泄露演示账号凭据的前提下写出受控的 1440×1000 PNG。因此以下三张图需要在已登录浏览器会话中按 CSS 视口 1440×1000 重新采集；不得复用此前有效视口约 1152px 的截图：

- `boss-dashboard-final.png`
- `pm-dashboard-final.png`
- `member-dashboard-final.png`

## 13. 剩余技术债

- Vite 大 chunk size 提示为既有问题，按本轮停止条件未处理。
- 最终三张截图受当前本机无头浏览器调试端点限制尚未落盘；代码、宽度测量、构建和真实角色 API 回归已完成。

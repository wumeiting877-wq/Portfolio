# 分角色 Dashboard 第二轮视觉收口报告

实施日期：2026-09-24  
适用角色：BOSS / PROJECT_MANAGER / MEMBER

## 1. 修改范围

本轮只调整三个角色 Dashboard 的前端布局、密度、图表高度、链接、Tab 和空态，不修改后端、数据库、API、角色、权限、Scope、费用计算或币种原始值。

## 2. IBM 规范读取结果

已完整读取：

- `IBM-DESIGN.md`
- `PROJECT-UI-CONSTRAINTS.md`
- `docs/ROLE-DASHBOARD-DESIGN-INPUT.md`
- `docs/ROLE-DASHBOARD-IBM-REDESIGN-IMPLEMENTATION-REPORT.md`

实现继续使用 IBM Plex Sans、4px 间距网格、IBM Blue 链接与焦点、直角容器、1px 边线、白/浅灰表面，无阴影、渐变、发光或胶囊式 Tab。

## 3. 修改文件

- `frontend/src/views/home/shells/BossDashboardShell.vue`
- `frontend/src/views/home/shells/ProjectManagerDashboardShell.vue`
- `frontend/src/views/home/shells/MemberDashboardShell.vue`
- `frontend/src/views/home/components/ResourceStatusBars.vue`
- `frontend/src/components/charts/IbmChart.vue`
- `docs/ROLE-DASHBOARD-VISUAL-FIX-REPORT.md`

## 4. 公共视觉修正

- Dashboard 折线图默认高度由 300px 收紧为 220px；BOSS 与 PM 使用 240px，MEMBER 使用 200px。
- 数据导航统一为无边框 IBM Blue 文本链接，补充 hover 下划线与键盘焦点轮廓。
- Dashboard 表格单元格保持 6px 纵向 padding，空表区域压缩到 48px。
- BOSS 费用结构 Tab 使用无边框文字、底部分隔线与 2px IBM Blue 选中线，并补充 `role=tab` / `aria-selected`。
- 资源状态行距由 12px 收紧为 8px；MEMBER 的零值状态使用灰色低权重显示。

## 5. BOSS 修正前后

- 费用趋势与资源状态保持 2:1 双列并统一顶部、底部对齐。
- 项目成本与费用结构双列等高排列。
- “需要关注”改为即将到期、尚未分配、闲置三列；数量、说明、资源链接与日期使用明确 Grid，不再出现资源名和日期粘连。
- 费用结构的按资源类型/按计费方式切换保持原业务行为。

## 6. PM 修正前后

- 日期范围与负责项目筛选保持同一工具区。
- 第一层：我的项目费用趋势 + 资源状态。
- 第二层：项目费用 + 资源类型费用。
- 第三层：项目成员费用 + 项目公共费用。
- 资源关注移至页面底部；无异常时只显示一行紧凑说明。
- 项目名与成员名均为蓝色文本链接，不使用按钮边框。

## 7. MEMBER 修正前后

- 四项 KPI 后立即展示“我的项目”，保持成员任务优先级。
- “我的资源状态”与“我的资源类型费用”并列；五个零值状态保留但降低视觉权重。
- “我的费用趋势”降为 200px，置于资源信息之后。
- 无到期资源时使用紧凑文本空态，不渲染高空表格区。

## 8. 币种检查

- `money.ts` 未修改。
- API / DB 原始币种仍为 `CNY`、`USD`。
- UI 继续显示“人民币”“美元”。
- 各币种按行、按系列独立展示，未增加跨币种汇总。

## 9. 权限检查

- 未修改 RoleCode、Permission、JWT、Router 业务语义或任何后端 Scope。
- 实际登录 PM 后只看到负责项目；选择 Project A 后项目数变为 1，所有统计区块同步刷新。
- 实际登录 MEMBER 后只看到“校验项目”“Project A”，未出现 Project B 或管理角色区块。

## 10. Build / Browser 回归

- `npm run build`：通过（包含 `vue-tsc -b` 与 Vite production build）。
- 浏览器视口：1440×1000。
- BOSS：数据、费用结构 Tab、资源链接和关注区正常。
- PM：负责项目筛选正常；Project A 筛选联动正常；成员费用与公共费用并列正常。
- MEMBER：项目优先、零状态弱化、200px 趋势和紧凑到期空态正常。
- 979px：三个 PM 双列 Grid 实测均降为单列；`scrollWidth === viewport`，无页面横向溢出。
- 浏览器控制台 error：0。

## 11. Before / After 截图索引

Before（保留原文件）：

- `artifacts/dashboard-visual-evidence-2026-09-24/01-boss-dashboard-top.png`
- `artifacts/dashboard-visual-evidence-2026-09-24/02-project-manager-dashboard-top.png`
- `artifacts/dashboard-visual-evidence-2026-09-24/03-member-dashboard-top.png`

After：

- `artifacts/dashboard-visual-fix-2026-09-24/boss-dashboard-after.png`
- `artifacts/dashboard-visual-fix-2026-09-24/pm-dashboard-after.png`
- `artifacts/dashboard-visual-fix-2026-09-24/member-dashboard-after.png`

## 12. 仍存在的问题

- Vite 仍有既有的大 chunk size 警告，本轮未做构建拆包重构。
- Element Plus 开发模式仍输出 radio 旧 API 的 warning，但浏览器 console error 为 0；该 warning 不影响本轮 Dashboard 功能与视觉验收。

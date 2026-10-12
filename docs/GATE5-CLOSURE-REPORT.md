# Gate 5 Closure Report

阶段：Gate 5  
日期：2026-09-22  
结论：CLOSED / PASS

## 验收对照

### Backend

- [x] Overview PASS
- [x] Trend PASS
- [x] Project Cost PASS
- [x] Employee Cost PASS
- [x] Resource Type Cost PASS
- [x] Billing Cost PASS
- [x] Resource Status PASS
- [x] Expiring Resource PASS

### Scope

- [x] ADMIN GLOBAL
- [x] BOSS GLOBAL READ（同范围，无 Dashboard 写入口）
- [x] PM managed projects only
- [x] MEMBER self only
- [x] MEMBER 项目/员工排行 403

### Currency

- [x] CNY / USD 分开
- [x] 无跨币种直接合计
- [x] 无实时汇率

### Resources

- [x] ACTIVE / IDLE / EXPIRED / DISABLED
- [x] EXPIRING_SOON 动态计算，不写库
- [x] UNASSIGNED_ACTIVE 与显式 IDLE 分开
- [x] Released allocation 不作为 active

### Frontend

- [x] Role-based Dashboard
- [x] 真实 Statistics API，无前端本地拼总费用
- [x] 无假数据
- [x] IBM UI PASS
- [x] Dashboard / Statistics 职责分离
- [x] `npm run build` PASS

### Tests

- [x] Gate 4 原 133 tests 不退化
- [x] Gate 5 新 30 tests PASS
- [x] pytest 连续两次 163 passed
- [x] 测试库 `project_cost_hub_test`

## 交付物

- Statistics Repository / Service / API
- Dashboard HomeView + StatisticsView
- `docs/GATE5-IMPLEMENTATION-REPORT.md`
- `docs/GATE5-TEST-REPORT.md`
- `docs/GATE5-STATISTICS-SCOPE-VERIFICATION.md`
- `docs/GATE5-MULTI-CURRENCY-VERIFICATION.md`
- `docs/GATE5-DASHBOARD-RUNTIME-VERIFICATION.md`
- `docs/GATE5-IBM-UI-REVIEW.md`
- `docs/GATE5-CLOSURE-REPORT.md`

## 已知问题

- 开发库仍有 Gate 1 时期测试人员及既有 9 月费用，故浏览器「本月」总额大于隔离日 `2026-09-22` 的 Gate 5 专项金额。清理仍需单独 `DEV-DATA-CLEANUP-PLAN.md`。
- 未创建 Alembic `0006`：现有单列索引已覆盖统计过滤。
- 图表使用 SVG 而非 ECharts（避免新增前端依赖）；视觉仍为 IBM 折线 / 横条，无 3D / 渐变。
- IBM Plex Sans 仍是 CSS 字体栈声明（Gate 1 既有状态）。
- 单月趋势仅一个真实数据点，不补假月份。

## Next Gate

Gate 6：企业化能力收口（导入导出、到期提醒、操作日志、系统设置、发布验收）。

# Gate 5 IBM UI Review

日期：2026-09-22  
视觉 Source of Truth：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`

## 已读取

- [x] IBM-DESIGN.md
- [x] PROJECT-UI-CONSTRAINTS.md

前端编码前已读取。未新建第二套 Design System 文件。`tokens.css` 仅追加最小 chart token。

## 修改 / 新增文件

```text
frontend/src/api/statistics.ts
frontend/src/views/home/HomeView.vue
frontend/src/views/statistics/StatisticsView.vue
frontend/src/components/KpiStrip.vue
frontend/src/components/MoneyText.vue
frontend/src/components/EmptyState.vue
frontend/src/components/charts/IbmChart.vue
frontend/src/components/charts/chartTheme.ts
frontend/src/utils/money.ts
frontend/src/utils/dateRange.ts
frontend/src/router/index.ts
frontend/src/layouts/AdminLayout.vue
frontend/src/styles/tokens.css
frontend/src/views/expenses/ExpenseListView.vue
PROJECT-UI-CONSTRAINTS.md
```

## Chart token（IBM UI 未定义完整 palette 时的最小补充）

```text
--chart-series-1: #0f62fe   IBM Blue 主序列
--chart-series-2: #525252   ink-muted
--chart-series-3: #0043ce   blue-60
--chart-series-4: #24a148   semantic-success（克制）
--chart-series-5: #8c8c8c   ink-subtle
--chart-axis: #8c8c8c
--chart-split: #e0e0e0      hairline
```

图表实现为 SVG 折线 / 横向条形，未使用 3D、渐变、阴影、圆角柱。未引入 ECharts 依赖。

## Dashboard `/`

| 元素 | Token / 实现 |
| --- | --- |
| 页背景 | surface-1 `#f4f4f4` |
| 指标带 | canvas + 1px hairline + radius 0 + 无阴影 |
| 指标数字 | 24px / 400，tabular-nums |
| 指标标题 | 12px / ink-muted |
| 主序列 | IBM Blue `#0f62fe` |
| 金额 | 显式 `CNY` / `USD` 分行 |
| 面板 | 1px hairline，padding 16px |
| 空状态 | 文案 Empty State，不造假点 |

禁止项未出现：彩色背景大卡、大圆角 12/16/20、大阴影、玻璃拟态、3D。

## Statistics `/statistics`

与 Dashboard 共用指标带与图表 token。增加 product-tab（选中 2px Blue 底线，既有 `.product-tab`）。表格金额右对齐 + `MoneyText`。

## 金额

统一：

```text
font-variant-numeric: tabular-nums
显式币种
右对齐
```

浏览器实测 ADMIN：`CNY 7,220.00` 与 `USD 100.00` 分行。

## 响应式

KpiStrip `auto-fit` minmax(160px)；1024px 以下图表网格单列。未做移动端卡片墙。

## 结论

IBM UI Review：PASS

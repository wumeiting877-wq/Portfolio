# Gate 5 Dashboard Runtime Verification

日期：2026-09-22  
浏览器：`http://localhost:5173/` 与 `/statistics`  
账号：admin / boss / pm / member，密码为当前 `.env` 示例值，未写入本报告。  
时间范围：本月（2026-09）。本月金额含开发库既有有效费用；Gate 5 隔离日 `2026-09-22` 的 API 数值见 Scope 报告。

## ADMIN

可见模块：

- 菜单：首页、统计分析、项目管理、资源账号、费用管理、周期规则、人员管理、系统账号
- 紧凑指标带：本期费用 CNY 7,220.00 / USD 100.00；项目数 2；活跃资源 10；闲置/未分配 1/3；即将到期 1
- 费用趋势（CNY / USD 分系列）
- 资源状态表
- 项目费用 Top 5：Project A、Project B
- 资源类型费用 Top 5
- 即将到期：GATE5-EXPIRING
- 闲置：GATE5-IDLE
- 未分配但仍使用中：GATE5-UNASSIGNED、GATE5-EXPIRING、GATE3-C

不可见：彩色 KPI 卡、渐变、假曲线。健康检查保留在页头。

`/statistics`：标题「统计分析」；Tab 费用趋势 / 项目 / 成员 / 资源类型 / 费用类型 / 资源状态；Top 10/20。职责与 Dashboard 分离。

无假数据。无越权。

## BOSS

数据范围与 ADMIN 相同：CNY 7,220.00 / USD 100.00，项目 A+B。

菜单无「系统账号」。Dashboard 无写按钮。周期规则、人员管理只读入口仍在（与 Gate 4 菜单语义一致）。

## PM

可见：

- 菜单：首页、统计分析、项目管理、资源账号、费用管理（无周期规则 / 人员 / 系统账号）
- 本期费用 CNY 3,856.66 / USD 100.00
- 项目数 1
- 「我的项目费用」仅 Project A，无 Project B
- 项目成员费用：普通成员、同项目另一成员；公共费用单独列出
- 资源类型费用
- 闲置/未分配 0/0（看不到全局未分配资源）

不可见：Project B 排行、公司总人数、系统账号写入口。

## MEMBER

可见：

- 菜单：首页、统计分析、项目管理、资源账号、费用管理
- 我的本期费用 **仅 CNY 330.00**
- 我参与的项目 1
- 我的资源 4
- 我的资源类型费用
- 即将到期 0

不可见：

- 项目费用 Top 5 / Project B
- 员工排行
- 公司总费用 / USD 公司额
- 周期规则、人员管理、系统账号
- 项目公共费用

## 假数据检查

无模拟曲线填充缺失月份；单月真实点。无数据表格使用 Empty State 文案（即将到期 / 闲置）。

## Drill-down

项目名 → `/projects/:id?tab=expenses`  
资源名 → `/resources/:id?tab=expenses`  
成员名 → `/expenses?employee_id=`（列表读取 query，后端 Scope 仍生效）

## 结论

| 角色 | Dashboard | Statistics | Scope | 假数据 |
| --- | --- | --- | --- | --- |
| ADMIN | PASS | PASS | GLOBAL | 无 |
| BOSS | PASS | 同范围只读 | GLOBAL | 无 |
| PM | PASS | 仅负责项目 | MANAGED | 无 |
| MEMBER | PASS | 仅本人 | SELF | 无 |

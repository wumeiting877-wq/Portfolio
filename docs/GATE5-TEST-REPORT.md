# Gate 5 Test Report

日期：2026-09-22  
命令：`docker compose exec backend pytest`  
结果：163 passed（连续两次）

## 测试库隔离

pytest 仍强制 `project_cost_hub_test`。session 开始 DROP SCHEMA + Alembic upgrade head + bootstrap。不写入开发库 `project_cost_hub`。

连续运行：

```text
第一次：163 passed
第二次：163 passed
```

Gate 4 原 133 项全部保留。新增 30 项。

## 新增测试文件

| 文件 | 项数 |
| --- | --- |
| `test_statistics_overview.py` | 5 |
| `test_statistics_trend.py` | 3 |
| `test_statistics_project_costs.py` | 5 |
| `test_statistics_employee_costs.py` | 3 |
| `test_statistics_resource_type.py` | 3 |
| `test_statistics_resource_status.py` | 4 |
| `test_statistics_security.py` | 4 |
| `test_statistics_multi_currency.py` | 2 |
| `test_statistics_nplusone.py` | 1 |

## Overview

- ADMIN 按币种：本世界 2025-09 CNY 1450 / USD 140，无 `total`
- BOSS 与 ADMIN 同范围
- PM 仅负责项目份额：CNY 1050 / USD 140
- MEMBER 仅本人：CNY 130，无公司 `project_count` / `employee_count` / `resource_count`
- VOIDED 999 不出现在任一角色 Overview

## Trend

- 按 `YYYY-MM` + `currency` 分组
- 跨月：07 / 08 / 09 正确
- PM 不见 Project B 的 8 月 200
- MEMBER 仅本人 9 月 100 + 7 月 30

## Project ranking

- ADMIN/BOSS：A CNY 1050、A USD 140、B CNY 600
- PM 仅 Project A
- MEMBER 403
- 仅 `employee_id`、无 `project_id` 的 88 不反推到员工当前项目

## Employee ranking

- ADMIN：member_a 130、member_d 300
- 项目公共费用单独 `project_public_costs`（A CNY 650 / A USD 140），不摊入员工
- PM 不见 Project B 的 PM002
- MEMBER 403

## Resource type / billing

- 绑定资源 → 对应 ResourceType
- 未绑定 → `UNBOUND` / 未关联资源
- billing_mode + category + currency 分组
- MEMBER 不扩大到他人 USD

## Resource status

- ACTIVE / IDLE / EXPIRED / DISABLED
- EXPIRING_SOON 动态计算，不改库状态
- ACTIVE + 0 active allocation → UNASSIGNED_ACTIVE
- 显式 IDLE 与 UNASSIGNED_ACTIVE 分开
- Released allocation 视为未分配

## Security

- PM `project_id=B` 不能扩大，Overview 金额为空
- MEMBER `employee_id=他人` 不能扩大
- MEMBER project/employee ranking 403
- 无权限 project filter 不泄露资源数量

## 多币种

- CNY 100 + USD 100 → 仍为 100 / 100，不是 200
- Overview / Trend / Project / Resource Type 均按币种分组

## N+1

项目排行在项目数从 3 增到 8 后，SELECT 次数增幅 ≤ 2。聚合走 SQL `GROUP BY / SUM`。

## Alembic

head 仍为 `0005_gate4_expenses`。未创建无意义 `0006`。

## Frontend build

```text
docker compose exec frontend npm run build
vue-tsc -b && vite build
PASS
```

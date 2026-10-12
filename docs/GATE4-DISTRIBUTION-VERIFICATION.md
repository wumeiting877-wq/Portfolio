# Gate 4 Distribution Verification

日期：2026-09-22  
方式：对运行中的后端使用真实 ADMIN 调用 API  
脚本：`backend/app/scripts/verify_gate4_distribution.py`

验证分摊合计必须严格等于 `ExpenseRecord.amount`，金额走 Decimal / NUMERIC。

## 等额 1000 / 3

`POST /api/expenses`，`allocation_method=EQUAL`，三个目标（成员 + Project A + Project B）。

HTTP 200。落库金额：

```json
{
  "status": 200,
  "amounts": ["333.34", "333.33", "333.33"]
}
```

合计 `1000.00`。余数 `0.01` 加在第一份。

## 合计不等

一条 MANUAL 分摊 `900` 对费用 `1000`。

HTTP **400**：

```json
{
  "status": 400,
  "detail": "分摊金额合计必须等于费用金额"
}
```

记录未创建。

## 跨项目 RATIO 60 / 40

HTTP 200：

```json
{
  "status": 200,
  "amounts": ["600.00", "400.00"]
}
```

合计 `1000.00`。对应共享费用场景：同一 `ExpenseRecord` 分摊到 Project A 与 Project B。

## 其他自动测试覆盖

见 `backend/tests/test_expense_distributions.py`：

- 项目级 DIRECT
- 成员级 DIRECT
- 项目+成员 DIRECT（须为 active project_member）
- 项目+成员不匹配失败
- 无目标失败
- MANUAL 指定金额
- RATIO 跨项目

## 浏览器对照

ADMIN 打开 `http://localhost:5173/expenses/4?tab=distributions`（GATE4-E-SHARED）：

| 项目 | 成员 | 分摊方式 | 比例 | 分摊金额 |
| --- | --- | --- | --- | --- |
| Project A | - | RATIO | 0.600000 | 600.0000 |
| Project B | - | RATIO | 0.400000 | 400.0000 |

## 结论

| 规则 | 结果 |
| --- | --- |
| 项目 / 成员 / 项目+成员 | PASS |
| 共享资源跨项目分摊 | PASS |
| EQUAL | PASS |
| RATIO | PASS |
| MANUAL | PASS |
| SUM = amount | PASS |
| Decimal / NUMERIC | PASS |

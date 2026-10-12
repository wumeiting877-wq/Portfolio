# Gate 4 Recurring Idempotency Verification

日期：2026-09-22  
方式：对运行中的后端连续调用生成接口  
脚本：`backend/app/scripts/verify_gate4_recurring.py`  
命令等价：`POST /api/expenses/recurring/generate`  
CLI：`python -m app.scripts.generate_recurring_expenses`

## 规则

```text
name: GATE4-CURSOR-MONTHLY
frequency: MONTHLY
amount: 140.00 CNY
start / 首次 next_run: 2026-09-01
template: Project A DIRECT 140.00
rule_id: 1
```

部分唯一索引：`uq_expense_records_recurring_period` on `(recurring_rule_id, billing_period_start)` WHERE 二者非空。

## 连续两次生成（本轮运行态）

规则此前已生成过 2026-09 账期，因此本轮两次调用均不再出账：

```json
{
  "rule_id": 1,
  "first": [200, { "generated_count": 0, "skipped_count": 0, "generated_ids": [] }],
  "second": [200, { "generated_count": 0, "skipped_count": 0, "generated_ids": [] }],
  "generated_expense_ids": [7],
  "billing_periods": ["2026-09-01"],
  "duplicate_periods": []
}
```

首次成功生成（更早一次运行）产生费用 id **7**，账期 **2026-09-01**，金额 140 CNY，来源 `RECURRING_RULE`。  
第二次及之后：`generated_count=0`，无重复 `billing_period_start`。

ADMIN 周期规则页显示该规则「下次生成」已推进到 **2026-10-01**，状态启用。

## pytest

`test_generate_is_idempotent`：同一规则连续 `POST .../recurring/generate` 两次，第二次不新增记录。

生成器对并发 / 重入使用嵌套事务捕获 `IntegrityError` 后跳过已存在账期。

## 结论

| 规则 | 结果 |
| --- | --- |
| MONTHLY 可生成 | PASS |
| QUARTERLY / YEARLY 规则可创建 | PASS（pytest） |
| 连续两次生成不重复出账 | PASS |
| 唯一账期约束 | PASS |
| 停用 / 过期不生成 | PASS（pytest） |
| 非 ADMIN 不能生成 | PASS（pytest） |

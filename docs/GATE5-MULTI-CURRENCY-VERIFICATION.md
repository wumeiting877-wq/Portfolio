# Gate 5 Multi-Currency Verification

日期：2026-09-22  
禁止：`CNY 1000 + USD 100 = 1100`  
Gate 5 不实现实时汇率。

## pytest

`test_equal_cny_usd_remain_separate`：同一项目同一天

```text
CNY 100.00
USD 100.00
```

`GET /api/statistics/overview?project_id={id}&date_from=2026-03-15&date_to=2026-03-15`：

```json
{
  "amounts_by_currency": {
    "CNY": "100.00",
    "USD": "100.00"
  }
}
```

不存在 `200.00`，不存在 `total`。

`test_cny_and_usd_are_never_summed`：隔离年份世界中

```text
CNY 1450.00
USD 140.00
```

Trend / Project ranking / Resource type 均带 `currency` 字段，无混合总额。

## 运行态（2026-09-22）

脚本：`python -m app.scripts.verify_gate5_statistics`

准备：`GATE5-A-CNY` 100 + `GATE5-A-USD` 100。

ADMIN Overview：

```json
{ "CNY": "1380.00", "USD": "100.00" }
```

1380 含同日其他 CNY 分摊（B 200 + shared 1000 + member-direct 30 + public 50 + A 100），**不是** 1380+100 合成一笔。

Trend：

```json
[
  { "period": "2026-09", "currency": "CNY", "amount": "1380.00" },
  { "period": "2026-09", "currency": "USD", "amount": "100.00" }
]
```

Project A：CNY 750.00 与 USD 100.00 两行。

浏览器 ADMIN / BOSS 工作台「本期费用」：

```text
CNY 7,220.00
USD 100.00
```

本月含开发库既有 9 月有效费用；两币种分行，未显示 `7,320.00`。

MEMBER 工作台仅：

```text
CNY 330.00
```

无 USD 混合总额。

## 结论

| 检查 | 结果 |
| --- | --- |
| Overview 分币种 | PASS |
| Trend 分币种 | PASS |
| Project ranking 分币种 | PASS |
| Resource type 分币种 | PASS |
| 无跨币种合计 | PASS |
| 无实时汇率 | PASS |

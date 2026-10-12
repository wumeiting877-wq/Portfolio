# Pilot Release Smoke Report

日期：2026-09-23  
目标：空白 Pilot `http://127.0.0.1:8011`  
结果：10 / 10 PASS

`release_smoke_test.py` 按以下顺序解析地址：`--base-url`、位置参数、`BASE_URL`、`SMOKE_BASE`。未设置时才回退到容器内默认端口，Pilot 本次没有使用写死的 `8010`。

本次从宿主机执行，`BASE_URL=http://127.0.0.1:8011`，账号 `admin`，密码为已轮换的 Pilot 管理员密码（未写入本报告）。

```text
PASS health
PASS health/db
PASS version version=1.0.0
PASS login
PASS projects
PASS resources
PASS expenses
PASS statistics
PASS export
PASS notifications
{"passed": true, "count": 10}
```

`/version`：

```json
{"name":"project-cost-hub","version":"1.0.0","environment":"production"}
```

业务列表允许为空。Smoke 之后 Pilot 计数仍为 employees 1、users 1、projects 0、resource_accounts 0、expense_records 0、notifications 0、audit_logs 0。

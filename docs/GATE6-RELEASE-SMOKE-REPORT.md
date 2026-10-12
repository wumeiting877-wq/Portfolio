# Gate 6 Release Smoke Report

日期：2026-09-22  
命令：`docker compose exec backend python -m app.scripts.release_smoke_test`  
BASE：`http://127.0.0.1:8010`  
结果：10 / 10 PASS

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

`/version` 返回：

```json
{"name":"project-cost-hub","version":"1.0.0","environment":"development"}
```

不含 password / secret / JWT。当前环境是 development，生产启动另由 `validate_runtime_config` 拦截占位密码、DEBUG 与 CORS `*`。

# Pilot Environment Preparation Report

日期：2026-09-23  
阶段：PILOT ENVIRONMENT PREPARATION  
结果：Pilot Environment READY

本阶段只准备空白 Pilot 环境。未导入真实业务数据，未清理开发库，未修改 Gate 0–6 业务语义。

## PILOT-ENV-PREPARATION-CURRENT-STATE

实施前记录（开发栈保持原样）：

| 项 | 实施前 |
| --- | --- |
| Compose project | `x_10project` |
| Frontend | `x_10project-frontend-1`，`5173`，Up |
| Backend | `x_10project-backend-1`，`8010`，healthy |
| PostgreSQL | `x_10project-postgres-1`，`55432`，healthy |
| 开发库 | `project_cost_hub` |
| 同实例其他库 | `project_cost_hub_test`、`project_cost_hub_restore_test` |
| Pilot 库 | 不存在 |
| `GET /version` | `1.0.0`，`environment=development` |
| `APP_ENV` | `development` |
| `.env` 占位 | `change_me` 出现 6 处，未改动 |
| `frontend/package.json` | `0.1.0` |
| 开发库行数 | employees 46，users 36，projects 2，resource_accounts 11，expense_records 17，notifications 4，audit_logs 154，roles 4 |

## 独立 Pilot Stack

新增：

- `.env.pilot`（已写入 `.gitignore`）
- `docker-compose.pilot.yml`（overlay，不改 `docker-compose.yml`）

启动：

```powershell
docker compose -p project-cost-hub-pilot --env-file .env.pilot -f docker-compose.yml -f docker-compose.pilot.yml up -d --build
```

原 Compose 没有硬编码 `container_name`。Pilot 使用独立 project name，因此容器名、网络和 volume 与开发栈分开。

| 资源 | 开发 | Pilot |
| --- | --- | --- |
| Project | `x_10project` | `project-cost-hub-pilot` |
| Frontend | `5173` | `5174` |
| Backend | `8010` | `8011`（容器内仍监听 `8010`） |
| PostgreSQL | `55432` | `55433` |
| Database | `project_cost_hub` | `project_cost_hub_pilot` |
| Network | `x_10project_default` | `project-cost-hub-pilot_default` |
| Postgres volume | `x_10project_postgres_data` | `project-cost-hub-pilot_postgres_data` |
| Frontend volume | `x_10project_frontend_node_modules` | `project-cost-hub-pilot_frontend_node_modules` |

实施后 `docker ps` 同时看到两组容器。开发容器未被删除或停止。

## Pilot 安全配置

运行中的 Pilot backend：

| 项 | 值 |
| --- | --- |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `POSTGRES_DB` | `project_cost_hub_pilot` |
| `BOOTSTRAP_DEMO_ACCOUNTS` | `false` |
| `CORS_ORIGINS` | `http://localhost:5174,http://127.0.0.1:5174` |
| `CORS *` | 拒绝。`Origin: http://evil.example` 无 `Access-Control-Allow-Origin` |
| `JWT_SECRET_KEY` / `POSTGRES_PASSWORD` / `INITIAL_ADMIN_PASSWORD` | 新生成，不是 `change_me`，未复用开发密码 |

密钥只在 gitignored `.env.pilot`。本报告、终端摘要和 Git 跟踪文件都不包含完整 secret。

开发 `.env` 仍保留 `change_me` 与 `APP_ENV=development`，未改成 Pilot。

## Demo 账号

`bootstrap.py` 增加 `BOOTSTRAP_DEMO_ACCOUNTS`。

- development / test：未设置该变量时仍创建 boss / pm / member。
- production / pilot：默认不创建这三个演示账号。
- 显式 `true` / `false` 覆盖环境默认值。

Pilot 启动日志：`Demo accounts skipped`。库内用户只有 `admin`。角色定义未改：ADMIN、BOSS、PROJECT_MANAGER、MEMBER。

## 版本

| 位置 | 版本 |
| --- | --- |
| `GET http://127.0.0.1:8011/version` | `1.0.0`，`environment=production` |
| `GET http://127.0.0.1:8010/version` | `1.0.0`，`environment=development` |
| `frontend/package.json` | `1.0.0` |
| README | V1.0.0 |
| `docs/V1.0-RELEASE-CHECKLIST.md` | `1.0.0` |

## Pilot Admin

只存在初始化管理员 `admin` / `ADMIN001` / 角色 `ADMIN` / scope `GLOBAL`。

首次登录后已修改初始化密码：

- 旧密码再次登录：`401`
- 新密码登录：`200`
- `password_hash` 为 Argon2，不是明文
- `audit_logs` 仍为 0 行，不含密码

当前可用密码只保存在 `.env.pilot` 的 `PILOT_ADMIN_CURRENT_PASSWORD`。初始化密码不再用于登录。未创建真实 BOSS / PM / MEMBER。

## 回归

- pytest：连续两次进程退出码 0，进度 100%，无失败。收集 208 项（原 196 项 + 本阶段 12 项：demo 开关 8，`BASE_URL` 4）。
- `npm run build`：PASS（`project-cost-hub-frontend@1.0.0`）。

## 最终验收

```text
Pilot Environment: READY

Development Stack: x_10project 5173 / 8010 / 55432 / project_cost_hub
Pilot Stack: project-cost-hub-pilot 5174 / 8011 / 55433 / project_cost_hub_pilot

Pilot Frontend: 5174
Pilot Backend: 8011
Pilot PostgreSQL: 55433
Pilot DB: project_cost_hub_pilot

Development DB Untouched: PASS
Pilot DB Empty Baseline: PASS
Alembic: 0006_gate6_enterprise
APP_ENV: production
DEBUG: false
CORS: explicit
Secrets: no placeholders
Demo Accounts Disabled: PASS
Initial Admin: admin / ADMIN，密码已轮换
Frontend Version: 1.0.0
Backend Version: 1.0.0

Release Smoke: 10/10 PASS
Backend Tests: PASS
Frontend Build: PASS

Real Data Imported: NO
Real Business Accounts Created: NO

Known Issues: 当前无 P0 / P1
Next Action: 开始第一小批真实数据 Preview → Commit
```

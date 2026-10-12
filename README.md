# 企业项目资源与费用管理系统

内部使用的项目资源与费用中枢。当前版本 **V1.0.0**（Gate 0–6 收口）。

定位：管理项目、资源账号、费用分摊与统计，并提供 Excel 导入导出、到期提醒、审计查询、系统设置与备份恢复。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、Axios
- 后端：Python 3.11、FastAPI、SQLAlchemy 2、Pydantic、Alembic
- 数据库：PostgreSQL 16
- 运行：Docker Compose

## 项目目录

```text
frontend/     Vue 应用
backend/      FastAPI 应用、Alembic、pytest
scripts/      start / stop / status / backup / restore
docs/         Gate 报告与发布清单
```

## 本地端口

| 服务 | 端口 |
| --- | --- |
| 前端 | 5173 |
| 后端 | 8010 |
| PostgreSQL | 55432（容器内 5432） |

## 启动

```powershell
Copy-Item .env.example .env
.\scripts\start.ps1
```

或：

```powershell
docker compose up -d --build
```

- 前端：http://localhost:5173
- 后端：http://localhost:8010/health
- 数据库：http://localhost:8010/health/db
- 版本：http://localhost:8010/version

## 停止

```powershell
.\scripts\stop.ps1
```

数据卷默认保留。清空数据库：`docker compose down -v`。

## 状态

```powershell
.\scripts\status.ps1
```

## 初始化管理员

后端启动会执行 `alembic upgrade head` 与 `python -m app.scripts.bootstrap`。也可：

```powershell
docker compose exec backend python -m app.scripts.create_admin
```

开发示例账号（密码来自 `.env`，不要写进源码）：admin / boss / pm / member。生产环境必须更换全部默认密码，且不要创建无必要的示例业务账号。

## 数据库迁移

```powershell
docker compose exec backend alembic upgrade head
```

当前 Alembic head：`0006_gate6_enterprise`。测试库：`project_cost_hub_test`。

## 测试

```powershell
docker compose exec backend pytest
```

pytest 强制使用 `project_cost_hub_test`，不会写入开发库。

## Excel 导入导出

- 导入仅 ADMIN；必须先 Preview 再 Commit；Commit 使用事务，失败整批回滚。
- 不允许导入 password / api_key / secret / token。
- 导出复用 Project / Resource / Expense / Statistics Scope。
- 金额与币种分列，不做跨币种合计。

模板：`GET /api/imports/templates/{type}`  
导入预检：`POST /api/imports/{type}/preview`  
正式导入：`POST /api/imports/{type}/commit`  
导出：`GET /api/exports/{type}`

## 备份

```powershell
.\scripts\backup.ps1
```

生成 `backups/project_cost_hub_YYYYMMDD_HHMMSS.backup`。`backups/` 已加入 `.gitignore`。

## 恢复

必须显式指定目标库，默认拒绝覆盖当前开发库：

```powershell
.\scripts\restore.ps1 -BackupFile .\backups\xxx.backup -TargetDatabase project_cost_hub_restore_test
```

## 权限模型

| 角色 | 范围 |
| --- | --- |
| ADMIN | 全局读写，可导入，可改设置 |
| BOSS | 全局只读，可导出，可查审计，设置只读 |
| PROJECT_MANAGER | 自己负责的项目 |
| MEMBER | 本人资源与费用 |

## 生产发布注意事项

- `APP_ENV=production`
- 禁止 `change_me` 作为 JWT / DB / 管理员密码
- 关闭 `DEBUG`
- CORS 必须是明确来源列表，不允许 `*`
- 生产 Compose 不以 `--reload` 启动
- 发布前执行：`docker compose exec backend python -m app.scripts.release_smoke_test`
- 详见 `docs/V1.0-RELEASE-CHECKLIST.md`

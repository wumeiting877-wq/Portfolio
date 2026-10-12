# START HERE

第一次把系统跑起来，并完成日常使用路径。

## 1. 环境要求

- Docker Desktop 已启动
- Docker Compose v2+

## 2. 准备环境变量

```powershell
Copy-Item .env.example .env
```

上线前必须修改：

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `INITIAL_ADMIN_PASSWORD`
- 各 `DEMO_*_PASSWORD`（生产可不创建示例账号）

## 3. 启动系统

```powershell
.\scripts\start.ps1
```

等待 backend healthy。打开 http://localhost:5173

## 4. 登录

使用 `.env` 中的管理员账号登录。如提示改密，先完成改密。

## 5. 创建人员

菜单「人员管理」→ 新增人员（工号唯一）。需要登录账号时，到「系统账号」为人员创建账号。

## 6. 创建项目

「项目管理」→ 指定在职负责人。

## 7. 创建资源

「资源账号」→ 选择资源类型、到期日。不要在系统中保存资源密码。

## 8. 分配资源

资源详情 → 分配到项目和/或成员。项目+成员时，成员必须已在该项目中。

## 9. 录入费用

「费用管理」→ 金额与币种分列；分摊合计必须等于费用金额。

## 10. 查看 Dashboard

首页是角色化 Dashboard。「统计分析」是详细报表。二者都走 Statistics API。

## 11. 导出数据

「导入导出」。ADMIN 可导入（先预检再提交）。其他角色仅能按范围导出。

## 常用运维

```powershell
.\scripts\status.ps1
.\scripts\backup.ps1
docker compose exec backend pytest
docker compose exec backend python -m app.scripts.generate_notifications
docker compose exec backend python -m app.scripts.cleanup_dev_data --dry-run
```

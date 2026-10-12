# Gate 1 Test Report

日期：2026-09-21  
命令：`docker compose exec backend pytest`  
结果：32 passed

## 后端自动测试

```text
32 passed, 1 warning in 4.33s
```

覆盖：

### Auth

- 正确账号密码登录成功
- 错误密码失败，提示统一为“用户名或密码错误”
- 未知用户同一提示
- 停用账号无法登录
- 无 token 访问 `/api/auth/me` 返回 401
- 有效 token 可访问 `/me`
- 修改密码必须提供正确旧密码，成功后旧密码失效

### Role / Permission

- ADMIN 可创建人员
- BOSS 不可创建人员，返回 403
- PROJECT_MANAGER 不可创建人员，返回 403
- MEMBER 不可创建人员，返回 403
- MEMBER 不可查询人员列表，返回 403
- 非 ADMIN 不可访问 `/api/users`，返回 403

### Users

- ADMIN 可创建系统账号
- 响应中不含 `password_hash`
- 用户名重复失败
- 重置密码后旧密码无法登录
- 停用后无法登录，启用后可再登录
- `DELETE /api/users/{id}` 不被允许（405）

### Employees

- 创建 / 查询 / 更新 / 逻辑停用
- 工号重复失败

### Security

- 数据库存储的是 Hash，不是明文
- 审计日志不含密码明文和 `password_hash`

### Seeded accounts

| 用户名 | 角色 | Scope |
| --- | --- | --- |
| admin | ADMIN | GLOBAL |
| boss | BOSS | GLOBAL |
| pm | PROJECT_MANAGER | MANAGED_PROJECTS |
| member | MEMBER | MEMBER_PROJECTS |

四类账号均可使用 `.env` 中的示例密码登录。

## 前端构建

```text
npm run build
vue-tsc -b && vite build  成功
```

## 运行时验收

Compose：

```text
backend   Up (healthy)   8010
frontend  Up             5173
postgres  Up (healthy)   55432
```

健康检查：

- `GET /health` 200 `{"status":"ok"}`
- `GET /health/db` 200 `{"status":"ok"}`

Alembic：

```text
0002_gate1_identity (head)
```

浏览器：

- 管理员可登录，菜单含首页 / 人员管理 / 系统账号
- 管理员人员页可新建、编辑、停用
- 管理员账号页可创建账号、改角色、重置密码、启用停用
- 老板可登录，菜单不含系统账号
- 老板人员页只读，无“新建人员”
- 老板调用 `/api/users` 返回 403
- 老板调用 `/api/employees` 返回 200

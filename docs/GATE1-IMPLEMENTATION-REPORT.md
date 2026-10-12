# Gate 1 Implementation Report

阶段：Gate 1  
日期：2026-09-21  
结果：PASS

## 实施范围

在 Gate 0 可运行骨架上完成登录、人员、系统账号、角色、权限、Scope 基础和审计。未实现项目、资源账号、费用、Dashboard。

## 完成项

| ID | 内容 | 状态 |
| --- | --- | --- |
| G1-01 | Employee 数据模型 | 完成 |
| G1-02 | Role 数据模型 | 完成 |
| G1-03 | User 数据模型 | 完成 |
| G1-04 | 初始化四类角色 | 完成 |
| G1-05 | Argon2 密码 Hash | 完成 |
| G1-06 | JWT Auth | 完成 |
| G1-07 | 登录 API | 完成 |
| G1-08 | `/api/auth/me` | 完成 |
| G1-09 | 权限依赖 | 完成 |
| G1-10 | Scope 基础 | 完成 |
| G1-11 | Employee CRUD（删除为逻辑停用） | 完成 |
| G1-12 | User 管理 | 完成 |
| G1-13 | 重置密码 | 完成 |
| G1-14 | 启用/停用账号 | 完成 |
| G1-15 | Audit Log | 完成 |
| G1-16 | 前端登录页 | 完成 |
| G1-17 | 前端后台壳层 | 完成 |
| G1-18 | 人员管理页 | 完成 |
| G1-19 | 系统账号页 | 完成 |
| G1-20 | 路由权限 | 完成 |
| G1-21 | 自动测试 | 完成 |
| G1-22 | 真实运行验收 | 完成 |

## 数据模型

Employee 与 User 分离。

角色：

- `ADMIN` → 全局读写，Scope `GLOBAL`
- `BOSS` → 全局只读，Scope `GLOBAL`
- `PROJECT_MANAGER` → 只读，Scope `MANAGED_PROJECTS`
- `MEMBER` → 只读，Scope `MEMBER_PROJECTS`

Gate 1 尚未建立 projects 表，Scope 枚举与 JWT/`/me` 已接入，真实项目过滤留到 Gate 2。

## API

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/change-password`
- `POST /api/auth/logout`
- `GET/POST /api/employees`
- `GET/PUT/DELETE /api/employees/{id}`（DELETE = 逻辑停用）
- `GET/POST /api/users`
- `GET/PUT /api/users/{id}`
- `POST /api/users/{id}/reset-password`
- `POST /api/users/{id}/disable`
- `POST /api/users/{id}/enable`
- `GET /api/roles`

没有物理删除账号接口。

## 初始化

容器启动：

```text
alembic upgrade head
python -m app.scripts.bootstrap
```

单独创建管理员：

```powershell
docker compose exec backend python -m app.scripts.create_admin
```

账号来自环境变量，不在源码中写死老板账号。日志不打印明文密码。

## 前端

- 登录页：用户名 + 密码，无注册
- 后台菜单：首页、人员管理、系统账号
- 不展示项目 / 资源 / 费用 / 统计
- ADMIN 可见人员与账号写操作
- BOSS 可见人员只读，不可见系统账号
- PROJECT_MANAGER / MEMBER 仅首页

## 安全

- 密码 Argon2
- JWT 含 `user_id` / `username` / `role` / `scope` / `exp`
- `JWT_SECRET_KEY` 来自环境变量
- API 不返回 `password_hash`
- 审计日志剔除密码字段
- 停用账号立即无法登录
- 修改密码需要旧密码
- 重置密码仅管理员

## 未完成项（有意留给后续 Gate）

- 项目表与真实 Scope 过滤
- 资源账号
- 费用
- Dashboard 大屏
- 独立测试库（当前 pytest 写入开发库）

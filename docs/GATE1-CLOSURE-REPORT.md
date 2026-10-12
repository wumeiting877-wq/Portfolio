# Gate 1 Closure Report

阶段：Gate 1  
日期：2026-09-21  
结论：CLOSED / PASS

## 验收对照

### 运行

- [x] `docker compose up -d` 成功
- [x] frontend 正常打开
- [x] backend healthy
- [x] PostgreSQL healthy
- [x] `/health` 200
- [x] `/health/db` 200

### 数据库

- [x] Alembic 正常，当前 head = `0002_gate1_identity`
- [x] 空库可完整迁移（Gate 0 baseline + Gate 1 identity）

### 登录

- [x] 管理员登录
- [x] BOSS 登录
- [x] PROJECT_MANAGER 登录
- [x] MEMBER 登录

### 权限

- [x] ADMIN 可写
- [x] BOSS 只能查看
- [x] PROJECT_MANAGER / MEMBER 写接口 403
- [x] 非管理员调用写接口 / 账号接口 403
- [x] 前端隐藏按钮只是辅助，后端才是权限边界

### 安全

- [x] 数据库无明文密码
- [x] API 不返回 password_hash
- [x] JWT secret 不写死源码
- [x] 禁用账号立即失效
- [x] 审计日志不记录密码

### 测试

- [x] pytest 全部通过（32 passed）

## 交付物

- 可运行前端、后端、PostgreSQL
- Alembic
- 登录与四类角色
- 人员管理、系统账号管理
- Role + Scope 双层权限底座
- 审计基础
- 自动测试
- README / START-HERE
- Gate 0 / Gate 1 报告

## 已知问题

- pytest 与开发库共用 PostgreSQL，测试会留下人员/账号数据。后续建议独立 test database。
- Windows Docker 绑定挂载下，Vite 文件监听不稳定，已开启 polling；必要时重启 frontend 容器。
- Scope 的真实项目过滤尚未接入，因为 Gate 1 没有 projects 表。

## Next Gate

Gate 2：项目管理，并把 `MANAGED_PROJECTS` / `MEMBER_PROJECTS` 接到真实项目关系。

在此之前不得开发资源账号、费用、Dashboard。

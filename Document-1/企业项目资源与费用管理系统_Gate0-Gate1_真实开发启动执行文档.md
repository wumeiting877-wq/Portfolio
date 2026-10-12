# 企业项目资源与费用管理系统
# Gate 0 + Gate 1 真实开发启动执行文档

版本：V1.0  
阶段：Gate 0 / Gate 1  
目标：完成项目可运行骨架、数据库、登录、人员、系统账号、角色与数据权限底座。

---

# 一、当前阶段目标

本阶段不开发完整业务系统。

本阶段只完成后续所有模块依赖的基础能力：

1. 前后端项目骨架
2. PostgreSQL 数据库
3. Docker Compose 本地运行
4. 系统登录
5. 人员管理
6. 系统账号管理
7. 角色管理
8. 权限校验
9. 数据范围 Scope
10. 审计基础
11. 基础测试
12. 一键启动

完成后必须达到：

- 管理员可以登录
- 管理员可以创建人员
- 管理员可以给人员创建系统登录账号
- 管理员可以设置角色和初始密码
- 老板可以登录
- 负责人可以登录
- 普通成员可以登录
- 不同角色进入系统后权限不同
- 后端接口真正执行权限校验
- 前端隐藏按钮只是辅助，不能作为权限边界
- 项目能够稳定启动、停止、重新启动

---

# 二、最高级开发约束

必须严格遵守。

## 2.1 技术栈

前端：

- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios

后端：

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic
- Alembic
- JWT

数据库：

- PostgreSQL

密码：

- Argon2 优先
- bcrypt 可作为备选
- 禁止明文密码

部署：

- Docker
- Docker Compose
- Nginx 暂不作为 Gate 0 强制项

测试：

- pytest
- FastAPI TestClient / httpx

---

## 2.2 不允许做的事情

当前阶段禁止：

- 提前开发资源账号业务
- 提前开发费用业务
- 提前开发 Dashboard 大屏
- 提前开发 Excel 导入导出
- 接入 AI
- 接入聊天功能
- 引入复杂微服务
- 引入消息队列
- 引入 Redis，除非有明确必要
- 使用 SQLite 替代正式 PostgreSQL
- 把权限只做在前端
- 把人员和登录账号合并成一张表
- 把角色写死在前端
- 直接硬编码老板账号

---

# 三、项目目录建议

项目根目录：

```text
project-cost-hub/
├── backend/
├── frontend/
├── deploy/
├── docs/
├── scripts/
├── .env.example
├── docker-compose.yml
├── README.md
└── START-HERE.md
```

---

# 四、后端目录

```text
backend/
├── app/
│   ├── api/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── employees/
│   │   ├── roles/
│   │   └── health/
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   └── logging.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── employee.py
│   │   ├── role.py
│   │   └── audit_log.py
│   │
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── permissions/
│   │   ├── roles.py
│   │   ├── scopes.py
│   │   └── dependencies.py
│   │
│   ├── main.py
│   └── __init__.py
│
├── alembic/
├── tests/
├── requirements.txt
└── Dockerfile
```

---

# 五、前端目录

```text
frontend/
├── src/
│   ├── api/
│   │   ├── auth.ts
│   │   ├── users.ts
│   │   └── employees.ts
│   │
│   ├── components/
│   ├── layouts/
│   ├── router/
│   ├── stores/
│   │   ├── auth.ts
│   │   └── user.ts
│   │
│   ├── views/
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── employees/
│   │   └── users/
│   │
│   ├── utils/
│   ├── App.vue
│   └── main.ts
│
├── package.json
├── vite.config.ts
└── Dockerfile
```

---

# 六、核心数据模型

## 6.1 employees

人员表。

字段建议：

```text
id
employee_no
name
department
position
email
phone
employment_status
remark
created_at
updated_at
```

employment_status：

```text
ACTIVE
INACTIVE
LEFT
```

注意：

Employee 与 User 必须分离。

---

## 6.2 users

系统登录账号。

字段：

```text
id
username
password_hash
employee_id
role_id
status
must_change_password
last_login_at
password_updated_at
created_at
updated_at
```

status：

```text
ACTIVE
DISABLED
LOCKED
```

要求：

- username 唯一
- employee_id 可唯一绑定
- password_hash 不得返回前端
- 创建账号时管理员设置初始密码
- 首次登录建议强制修改密码

---

## 6.3 roles

系统角色。

第一版固定角色：

```text
ADMIN
BOSS
PROJECT_MANAGER
MEMBER
```

字段：

```text
id
code
name
description
created_at
updated_at
```

角色含义：

ADMIN：
全局读写。

BOSS：
全局只读。

PROJECT_MANAGER：
负责项目只读。

MEMBER：
参与项目只读。

---

# 七、数据范围 Scope

不要把数据范围逻辑散落到每一个接口里。

统一定义：

```text
GLOBAL
MANAGED_PROJECTS
MEMBER_PROJECTS
```

对应：

```text
ADMIN -> GLOBAL
BOSS -> GLOBAL
PROJECT_MANAGER -> MANAGED_PROJECTS
MEMBER -> MEMBER_PROJECTS
```

当前 Gate 1 尚未实现 projects 表时：

先建立 Scope 基础结构、枚举和权限依赖。

Gate 2 再接入真实项目关系。

---

# 八、权限模型

系统必须同时有：

## 8.1 Role

控制“能做什么”。

例如：

```text
ADMIN:
read
create
update
delete

BOSS:
read

PROJECT_MANAGER:
read

MEMBER:
read
```

## 8.2 Scope

控制“能看哪些数据”。

例如：

```text
BOSS:
GLOBAL

PROJECT_MANAGER:
MANAGED_PROJECTS

MEMBER:
MEMBER_PROJECTS
```

后续所有 API 都采用：

```text
Role Permission + Data Scope
```

双重校验。

---

# 九、登录流程

流程：

```text
用户名 + 密码
        ↓
后端验证
        ↓
检查账号状态
        ↓
验证密码 Hash
        ↓
生成 JWT
        ↓
返回用户信息
        ↓
前端保存认证状态
        ↓
请求 /api/auth/me
```

JWT 至少包含：

```text
user_id
username
role
scope
exp
```

不要把敏感数据放入 JWT。

---

# 十、登录接口

必须实现：

```http
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/change-password
POST /api/auth/logout
```

logout 第一版可由前端清理 token 完成。

如未来需要服务端 token 撤销，再增加 token blacklist。

---

# 十一、初始化管理员

项目第一次启动必须提供初始化方式。

推荐：

```bash
python -m app.scripts.create_admin
```

或者：

```bash
docker compose exec backend python -m app.scripts.create_admin
```

读取环境变量：

```text
INITIAL_ADMIN_USERNAME
INITIAL_ADMIN_PASSWORD
```

要求：

- 如果管理员已存在，不重复创建
- 初始化完成后日志不得打印明文密码

---

# 十二、人员管理 API

管理员：

```http
GET    /api/employees
POST   /api/employees
GET    /api/employees/{id}
PUT    /api/employees/{id}
DELETE /api/employees/{id}
```

注意：

DELETE 第一版建议逻辑停用，不物理删除。

老板：

```text
只读
```

负责人/成员：

当前 Gate 1 可暂不开放完整人员列表。

Gate 2 按项目范围控制。

---

# 十三、系统账号管理 API

管理员：

```http
GET    /api/users
POST   /api/users
GET    /api/users/{id}
PUT    /api/users/{id}
POST   /api/users/{id}/reset-password
POST   /api/users/{id}/disable
POST   /api/users/{id}/enable
```

禁止：

```http
DELETE /api/users/{id}
```

直接物理删除账号。

建议使用 DISABLED。

---

# 十四、前端第一阶段页面

当前只做：

## 14.1 登录页

字段：

```text
用户名
密码
登录
```

不要：

- 注册
- 第三方登录
- 复杂动画
- AI 风格背景

---

## 14.2 基础后台布局

左侧菜单：

```text
首页
人员管理
系统账号
```

当前 Gate 1 不展示：

```text
项目
资源
费用
统计
```

或可以以 disabled 状态展示，但不要实现空功能。

---

## 14.3 首页

只需要简单展示：

```text
当前登录用户
当前角色
账号状态
系统状态
```

Gate 5 再开发真正 Dashboard。

---

## 14.4 人员管理

管理员：

- 搜索
- 新建
- 编辑
- 停用
- 查看

老板：

- 查看

负责人/成员：

当前阶段不开放。

---

## 14.5 系统账号

仅管理员可访问。

功能：

- 查看账号
- 创建账号
- 绑定人员
- 设置角色
- 设置初始密码
- 重置密码
- 启用
- 停用

---

# 十五、前端路由权限

必须存在 route meta：

```ts
meta: {
  roles: ['ADMIN']
}
```

同时需要全局路由守卫。

但是：

前端路由守卫不能代替后端权限校验。

---

# 十六、审计日志基础

Gate 1 先建立 audit_logs 表。

字段：

```text
id
operator_user_id
action
module
target_type
target_id
before_data
after_data
ip_address
created_at
```

当前至少记录：

- 创建人员
- 修改人员
- 停用人员
- 创建账号
- 修改角色
- 重置密码
- 启用账号
- 停用账号

密码禁止写入 before_data / after_data。

---

# 十七、数据库迁移

必须使用 Alembic。

禁止：

- 项目启动时自动 create_all 作为正式迁移方式
- 手工进入数据库建表

需要：

```bash
alembic upgrade head
```

即可完成数据库初始化。

---

# 十八、Docker Compose

至少包含：

```text
postgres
backend
frontend
```

建议本地端口：

```text
frontend: 5173
backend: 8010
postgres: 55432
```

如果已有端口冲突，可通过 .env 修改。

数据库名建议：

```text
project_cost_hub
```

---

# 十九、健康检查

必须实现：

```http
GET /health
```

返回：

```json
{
  "status": "ok"
}
```

建议增加：

```http
GET /health/db
```

验证 PostgreSQL。

---

# 二十、环境变量

必须提供 `.env.example`。

至少包含：

```text
APP_ENV=development

BACKEND_PORT=8010
FRONTEND_PORT=5173

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=project_cost_hub
POSTGRES_USER=project_cost
POSTGRES_PASSWORD=change_me

JWT_SECRET_KEY=change_me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=change_me
```

真实 `.env` 不提交 Git。

---

# 二十一、安全要求

必须完成：

1. 密码 Hash
2. JWT 过期时间
3. 禁止返回 password_hash
4. 登录失败统一提示
5. 防止通过接口越权
6. 管理员接口必须 ADMIN
7. 修改密码需要旧密码
8. 重置密码必须管理员操作
9. 停用账号后不能登录
10. 审计日志不记录密码
11. 数据库密码放环境变量
12. JWT_SECRET 不写死源码

---

# 二十二、测试要求

必须新增自动测试。

至少覆盖：

## Auth

- 正确账号密码登录成功
- 错误密码失败
- 停用账号无法登录
- token 可访问 /me
- 无 token 返回 401

## Role

- ADMIN 可创建人员
- BOSS 不可创建人员
- PROJECT_MANAGER 不可创建人员
- MEMBER 不可创建人员

## Users

- ADMIN 可创建系统账号
- 非 ADMIN 返回 403
- username 重复失败
- 重置密码成功
- 停用后无法登录

## Employees

- 创建
- 查询
- 更新
- 停用

---

# 二十三、验收标准

Gate 0 + Gate 1 只有满足以下条件才允许 CLOSED。

## 运行

- `docker compose up -d` 成功
- frontend 正常打开
- backend 正常
- PostgreSQL 正常
- `/health` 200
- `/health/db` 200

## 数据库

- Alembic 正常
- 数据库可以从空库完整迁移

## 登录

- 管理员正常登录
- BOSS 正常登录
- PROJECT_MANAGER 正常登录
- MEMBER 正常登录

## 权限

- ADMIN 可修改
- BOSS 只能查看
- PROJECT_MANAGER 只能查看
- MEMBER 只能查看
- 非管理员调用写接口返回 403

## 安全

- 数据库无明文密码
- API 不返回 password_hash
- JWT secret 不在源码
- 禁用账号立即失效

## 测试

- pytest 全部通过

---

# 二十四、Gate 0 实施顺序

按顺序执行：

```text
G0-01 创建仓库结构
G0-02 创建 FastAPI
G0-03 创建 Vue3
G0-04 配置 PostgreSQL
G0-05 配置 Docker Compose
G0-06 增加 .env.example
G0-07 增加 Health API
G0-08 配置 Alembic
G0-09 完成 README / START-HERE
G0-10 验证一键启动
```

---

# 二十五、Gate 1 实施顺序

```text
G1-01 Employee 数据模型
G1-02 Role 数据模型
G1-03 User 数据模型
G1-04 初始化四类角色
G1-05 密码 Hash
G1-06 JWT Auth
G1-07 登录 API
G1-08 /auth/me
G1-09 权限依赖
G1-10 Scope 基础
G1-11 Employee CRUD
G1-12 User 管理
G1-13 重置密码
G1-14 启用/停用
G1-15 Audit Log
G1-16 前端登录页
G1-17 前端后台壳层
G1-18 人员管理页
G1-19 系统账号页
G1-20 路由权限
G1-21 自动测试
G1-22 真实运行验收
```

---

# 二十六、要求 Codex/Cursor 的工作方式

不要一次性修改整个项目。

每完成一个子任务：

1. 说明修改文件
2. 说明为什么修改
3. 执行测试
4. 给出测试结果
5. 再进入下一项

如果发现架构问题：

先输出：

```text
BLOCKER
原因
影响
建议方案
```

禁止为了继续执行而偷偷绕过问题。

---

# 二十七、阶段输出文档

完成 Gate 0 后生成：

```text
docs/GATE0-IMPLEMENTATION-REPORT.md
```

内容：

- 实际目录
- 实际端口
- 启动方式
- 数据库状态
- 健康检查
- 已完成项
- 未完成项
- 测试结果

完成 Gate 1 后生成：

```text
docs/GATE1-IMPLEMENTATION-REPORT.md
docs/GATE1-TEST-REPORT.md
docs/GATE1-CLOSURE-REPORT.md
```

---

# 二十八、给 Codex / Cursor 的直接执行提示词

你现在位于“企业项目资源与费用管理系统”项目仓库。

请严格按照本文件执行 Gate 0 + Gate 1。

目标不是生成 Demo，也不是只搭 UI，而是创建可以真实长期开发和运行的项目基础。

必须优先保证：

1. 项目结构正确
2. PostgreSQL 正常
3. Alembic 正常
4. 登录链路真实
5. 密码安全
6. 后端权限真实
7. Employee 与 User 分离
8. Role + Scope 双层权限模型
9. 自动测试可重复
10. Docker 一键启动

执行前：

- 检查当前目录
- 检查是否已有代码
- 如已有代码，不得覆盖有效内容
- 输出 CURRENT STATE
- 再开始实施

执行顺序严格按照：

Gate 0 → Gate 1

不得提前进入：

Gate 2 项目管理
Gate 3 资源账号
Gate 4 费用管理
Gate 5 Dashboard

每完成一个 Gate 必须先测试和生成实施报告。

如果测试未通过，不得宣称 Gate CLOSED。

最终交付必须包含：

- 可运行前端
- 可运行后端
- PostgreSQL
- Alembic
- 登录
- 四类角色
- 人员管理
- 系统账号管理
- 权限保护
- 审计基础
- 自动测试
- README
- START-HERE
- Gate 0 / Gate 1 报告

最终请明确输出：

```text
Gate 0: PASS / FAIL
Gate 1: PASS / FAIL

Frontend:
Backend:
PostgreSQL:
Auth:
RBAC:
Scope:
Tests:

Known Issues:
Next Gate:
```

只有所有验收项通过，才允许进入 Gate 2。

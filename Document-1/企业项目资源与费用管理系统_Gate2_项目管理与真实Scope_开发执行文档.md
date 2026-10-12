# 企业项目资源与费用管理系统
# Gate 2 项目管理与真实 Scope 开发执行文档

版本：V1.0
阶段：Gate 2
前置状态：Gate 0 PASS / Gate 1 PASS
Gate 1 自动测试：32 passed
目标：完成项目管理、项目负责人、项目成员关系，并将 `MANAGED_PROJECTS` / `MEMBER_PROJECTS` 接入真实数据库关系。

---

# 一、Gate 2 进入条件

当前已确认：

```text
Gate 0: PASS
Gate 1: PASS

Frontend: PASS
Backend: PASS
PostgreSQL: PASS
Auth: PASS
RBAC: PASS
Scope 基础: PASS
Tests: 32 passed
```

当前真实基础：

```text
Frontend:
http://localhost:5173

Backend:
http://localhost:8010

PostgreSQL:
localhost:55432
database = project_cost_hub
```

已存在角色：

```text
ADMIN
BOSS
PROJECT_MANAGER
MEMBER
```

已存在 Scope：

```text
GLOBAL
MANAGED_PROJECTS
MEMBER_PROJECTS
```

Gate 1 中 Scope 仅存在于：

```text
Enum
JWT
/api/auth/me
```

Gate 2 的核心任务是：

> 把 Scope 从“声明”变成“真实数据访问边界”。

---

# 二、最高级业务原则

Gate 2 只解决：

```text
项目
负责人
项目成员
项目访问范围
```

本阶段不得提前开发：

```text
资源账号
费用
费用统计
Dashboard KPI
项目预算
Excel 导入导出
到期提醒
```

---

# 三、前端最高级设计约束

从 Gate 2 开始，所有新增和修改前端页面必须遵守：

```text
./IBM-DESIGN.md
```

视觉实现顺序必须为：

```text
真实业务
>
PROJECT-UI-CONSTRAINTS.md
>
IBM-DESIGN.md
>
Element Plus 默认样式
>
开发工具自行判断
```

编码前必须读取：

```text
./IBM-DESIGN.md
./PROJECT-UI-CONSTRAINTS.md
```

禁止：

- 重新设计第二套后台 Design System
- 新建另一套颜色 Token
- 使用 Element Plus 默认视觉覆盖 IBM 规范
- 大圆角
- 大阴影
- 渐变背景
- 大面积营销式 Hero
- AI/SaaS 风格 Dashboard
- 卡片套卡片
- 为每个字段创建独立 Card
- 使用无业务含义的装饰图标
- 私自增加不存在的业务入口

Element Plus 可以继续使用，但只作为实现工具。

---

# 四、IBM UI 基线

Gate 2 前端必须复用当前 IBM 基线：

## 色彩

```text
Primary:       #0f62fe
Ink:           #161616
Ink Muted:     #525252
Ink Subtle:    #8c8c8c
Canvas:        #ffffff
Surface 1:     #f4f4f4
Surface 2:     #e0e0e0
Hairline:      #e0e0e0
Success:       #24a148
Warning:       #f1c21b
Error:         #da1e28
```

## 字体

```text
IBM Plex Sans
```

默认正文：

```text
16px / 400 / line-height 1.5
```

表格、导航、按钮：

```text
14px
```

## 形状

默认：

```text
border-radius: 0
```

使用：

```text
1px hairline
surface change
```

表达层级。

禁止使用 drop shadow 制造层级。

## 间距

必须服从 4px Grid：

```text
4
8
12
16
24
32
48
```

---

# 五、Gate 2 数据模型

新增：

```text
projects
project_members
```

不要破坏 Gate 1 的：

```text
employees
users
roles
audit_logs
```

---

# 六、projects 表

建议字段：

```text
id
project_code
name
description
manager_employee_id
status
start_date
end_date
created_by
created_at
updated_at
```

约束：

```text
project_code UNIQUE
name NOT NULL
manager_employee_id FK -> employees.id
```

项目状态：

```text
PLANNING
ACTIVE
PAUSED
COMPLETED
ARCHIVED
```

中文映射：

```text
PLANNING   -> 筹备中
ACTIVE     -> 进行中
PAUSED     -> 已暂停
COMPLETED  -> 已完成
ARCHIVED   -> 已归档
```

---

# 七、负责人规则

第一版：

> 一个项目只有一个主负责人。

`manager_employee_id` 指向 Employee。

要求：

1. 负责人必须是有效 Employee。
2. 设置负责人时，不强制要求对方已经拥有系统账号。
3. 但如果负责人需要登录查看项目，则必须拥有：
   `PROJECT_MANAGER` 系统账号。
4. 如果管理员把负责人调整为其他人员，项目访问范围必须实时变化。
5. 不使用 username 作为项目负责人外键。
6. 不使用 nickname/name 字符串匹配权限。

真正权限关系必须通过：

```text
users.employee_id
        ↓
employees.id
        ↓
projects.manager_employee_id
```

---

# 八、project_members 表

字段建议：

```text
id
project_id
employee_id
member_role
joined_at
left_at
is_active
created_at
updated_at
```

唯一约束：

```text
(project_id, employee_id)
```

一个成员可以：

```text
加入多个项目
```

一个项目可以：

```text
拥有多个成员
```

这是多对多关系。

---

# 九、负责人是否同时属于项目成员

推荐规则：

项目负责人创建或变更时：

```text
自动保证负责人存在于 project_members
```

如果没有，则新增一条：

```text
member_role = PROJECT_MANAGER
is_active = true
```

这样所有“项目人员”逻辑保持一致。

但访问 `MANAGED_PROJECTS` 时仍然必须以：

```text
projects.manager_employee_id
```

为真实负责人边界。

禁止只根据 `project_members.member_role` 判断负责人 Scope。

---

# 十、成员关系历史

移除成员时：

禁止物理删除历史关系。

推荐：

```text
is_active = false
left_at = 当前时间
```

重新加入时：

第一版可以恢复原关系：

```text
is_active = true
joined_at = 当前时间
left_at = null
```

如后续需要完整加入/退出历史，再拆 history 表。

---

# 十一、项目删除规则

V1.0 禁止直接物理删除项目。

API 的“删除”语义应调整为：

```text
ARCHIVED
```

建议使用显式接口：

```http
POST /api/projects/{id}/archive
```

---

# 十二、Gate 2 Scope 真正实现

## ADMIN

```text
Role: ADMIN
Scope: GLOBAL
```

权限：

```text
查看全部项目
创建项目
修改项目
归档项目
设置负责人
添加成员
移除成员
```

## BOSS

```text
Role: BOSS
Scope: GLOBAL
```

权限：

```text
查看全部项目
查看全部项目成员
```

禁止所有写操作。

## PROJECT_MANAGER

```text
Role: PROJECT_MANAGER
Scope: MANAGED_PROJECTS
```

只能读取：

```text
projects.manager_employee_id == current_user.employee_id
```

不得根据前端传入 employee_id 决定范围。

## MEMBER

```text
Role: MEMBER
Scope: MEMBER_PROJECTS
```

只能读取：

```text
project_members.employee_id == current_user.employee_id
AND project_members.is_active == true
```

---

# 十三、Scope 查询服务

不要把 Scope SQL 重复写在每个接口。

新增统一服务，例如：

```text
permissions/project_scope.py
```

推荐能力：

```text
readable_projects(...)
can_read_project(...)
```

必须集中管理：

```text
GLOBAL
MANAGED_PROJECTS
MEMBER_PROJECTS
```

Gate 3 / Gate 4 后续资源与费用查询将复用项目 Scope。

---

# 十四、项目 API

## 项目列表

```http
GET /api/projects
```

支持：

```text
keyword
status
page
page_size
```

## 项目详情

```http
GET /api/projects/{id}
```

按 Scope 校验。

## 新建项目

```http
POST /api/projects
```

仅 ADMIN。

## 修改项目

```http
PUT /api/projects/{id}
```

仅 ADMIN。

## 归档

```http
POST /api/projects/{id}/archive
```

仅 ADMIN。

---

# 十五、项目成员 API

建议：

```http
GET    /api/projects/{id}/members
POST   /api/projects/{id}/members
PUT    /api/projects/{id}/members/{employee_id}
DELETE /api/projects/{id}/members/{employee_id}
```

GET 按项目可读 Scope。

POST / PUT / DELETE 仅 ADMIN。

DELETE 为逻辑移除。

---

# 十六、负责人修改

管理员修改负责人时：

- 校验 employee 存在
- 校验 employee ACTIVE
- 确保负责人 project_members active
- 写 Audit Log
- 原负责人如仍是普通成员，不自动移除
- 新负责人 Scope 立即生效
- 原负责人 MANAGED_PROJECTS Scope 立即失效

---

# 十七、Audit Log

Gate 2 必须记录：

```text
PROJECT_CREATE
PROJECT_UPDATE
PROJECT_ARCHIVE
PROJECT_MANAGER_CHANGE
PROJECT_MEMBER_ADD
PROJECT_MEMBER_REMOVE
PROJECT_MEMBER_RESTORE
```

---

# 十八、Alembic

新增正式迁移，例如：

```text
0003_gate2_projects
```

必须验证：

```text
空数据库
Gate 0
→ Gate 1
→ Gate 2
```

完整迁移通过。

---

# 十九、G2-00：先修复测试库污染

当前已知问题：

```text
pytest 与开发数据库共用
```

Gate 2 开始前先处理。

推荐新增：

```text
project_cost_hub_test
```

要求：

1. pytest 自动连接测试库。
2. 测试前后不污染开发库。
3. 测试数据可重复执行。
4. 连续运行两次 pytest 都 PASS。
5. 测试启动时如果 DB 名不是 test DB，则直接 FAIL。

---

# 二十、前端新增页面

Gate 2 后允许新增：

```text
/projects
/projects/:id
```

只有 Backend API / Router / Permission 都真实存在后，才能加菜单。

---

# 二十一、菜单权限

项目管理菜单：

```text
ADMIN            -> 显示
BOSS             -> 显示
PROJECT_MANAGER  -> 显示
MEMBER           -> 显示
```

但数据必须由后端 Scope 直接过滤。

禁止：

```text
前端拿全部项目后自己 filter
```

---

# 二十二、项目列表页

建议文件：

```text
frontend/src/views/projects/ProjectListView.vue
```

页面结构：

- `PageHeader`
- 紧凑筛选区
- 项目表格

筛选：

```text
项目名称/编码
状态
查询
重置
```

表格列：

```text
项目编码
项目名称
负责人
成员数
状态
开始日期
结束日期
更新时间
操作
```

ADMIN：

```text
查看
编辑
成员
归档
```

其他角色：

```text
查看
```

---

# 二十三、项目详情页

建议：

```text
frontend/src/views/projects/ProjectDetailView.vue
```

当前只允许：

```text
概览
成员
```

禁止提前创建：

```text
资源
费用
费用统计
```

---

# 二十四、项目概览

展示：

```text
项目名称
项目编码
负责人
状态
开始日期
结束日期
项目说明
创建时间
更新时间
```

采用：

```text
hairline
surface
structured descriptions
```

不要每个字段一张卡。

---

# 二十五、项目成员

表格：

```text
姓名
工号
部门
职位
成员角色
加入日期
状态
操作
```

ADMIN 有添加/移除。

其他角色只读。

---

# 二十六、新建 / 编辑项目

建议使用现有稳定的 Dialog 或 Drawer 模式。

字段：

```text
项目编码 *
项目名称 *
负责人 *
项目状态 *
开始日期
结束日期
项目说明
```

必须使用 IBM Input / Select 视觉，不增加装饰元素。

---

# 二十七、成员选择

添加成员时优先使用：

```text
可搜索 Employee Select
```

如人员规模扩大，使用搜索/分页 API。

---

# 二十八、StatusTag

复用现有：

```text
StatusTag.vue
```

建议：

```text
ACTIVE      -> Success
PAUSED      -> Warning
ARCHIVED    -> Neutral
COMPLETED   -> Neutral/Success
PLANNING    -> Info/Neutral
```

IBM Blue 不作为所有状态的默认色。

---

# 二十九、页面响应式

至少保证：

```text
1280px
1024px
768px
```

可正常使用。

窄屏表格允许横向滚动。

不要为了移动端把企业表格强行改成大量 Card。

---

# 三十、前端禁止项

Gate 2 禁止：

```text
Dashboard KPI 卡
顶部彩色统计块
渐变蓝背景
大 Banner
12/16/20px 大圆角 Card
大阴影
悬浮动画
玻璃拟态
AI 星光装饰
不必要图标
```

---

# 三十一、前端复用组件

优先复用：

```text
PageHeader.vue
StatusTag.vue
AdminLayout.vue
tokens.css
style.css
```

只有出现至少两个真实复用点时，再抽象公共组件。

---

# 三十二、API 数据响应

列表建议：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

项目详情只返回业务需要的数据。

不要把系统登录账号敏感信息嵌入项目详情。

---

# 三十三、项目与 User 的关系原则

Project 负责人是：

```text
Employee
```

不是 User。

权限解析：

```text
current User
→ user.employee_id
→ Employee
→ Project / ProjectMember
```

必须保持身份层与业务人员层分离。

---

# 三十四、测试要求

必须覆盖：

## Project CRUD

```text
ADMIN 创建项目成功
ADMIN 修改项目成功
ADMIN 归档项目成功
project_code 重复失败
无效负责人失败
```

## Project Members

```text
ADMIN 添加成员成功
同一成员不可重复 active 添加
ADMIN 移除成员成功
移除后 MEMBER 失去访问权限
重新加入后恢复权限
负责人自动存在于 project_members
```

## BOSS

```text
GET /projects 返回全部
GET 项目详情成功
所有写接口 403
```

## PROJECT_MANAGER

准备 Project A / Project B：

```text
pm 只负责 Project A
```

验证：

```text
pm 只返回 Project A
Project A 可读
Project B 不可读
所有写接口 403
```

## MEMBER

准备：

```text
member 加入 Project A
未加入 Project B
```

验证：

```text
只返回 Project A
Project A 可读
Project B 不可读
退出后立即失去权限
加入多个项目后可看到多个项目
```

## Security

必须验证：

```text
伪造 employee_id 无法越权
猜测 project id 无法越权
直接调 API 也不能突破 Scope
```

---

# 三十五、前端四角色回归

ADMIN：

```text
项目管理菜单出现
可新建/编辑/归档
可添加/移除成员
```

BOSS：

```text
项目菜单出现
看到全部
无写操作
```

PROJECT_MANAGER：

```text
只看到自己负责项目
无写操作
```

MEMBER：

```text
只看到参与项目
无写操作
```

---

# 三十六、Gate 2 开发顺序

```text
G2-00 独立 pytest 数据库
G2-01 Project 数据模型
G2-02 ProjectMember 数据模型
G2-03 Alembic 0003
G2-04 Project Schema
G2-05 Project Repository
G2-06 Project Service
G2-07 Project Scope Service
G2-08 Project API
G2-09 Project Member API
G2-10 负责人变更规则
G2-11 Audit Log
G2-12 Scope 自动测试
G2-13 CRUD 自动测试
G2-14 读取 IBM-DESIGN.md / PROJECT-UI-CONSTRAINTS.md
G2-15 Project 前端 API
G2-16 Project Router
G2-17 项目管理菜单
G2-18 ProjectListView
G2-19 新建/编辑项目
G2-20 ProjectDetailView
G2-21 Project Members
G2-22 IBM UI 审计
G2-23 npm run build
G2-24 pytest 全量回归
G2-25 四角色真实运行验收
G2-26 Gate 2 报告
```

---

# 三十七、IBM UI 审计清单

```text
[ ] 已读取 IBM-DESIGN.md
[ ] 已读取 PROJECT-UI-CONSTRAINTS.md
[ ] IBM Blue 仅作主要强调
[ ] IBM Plex Sans
[ ] 默认 0px radius
[ ] 无大圆角
[ ] 无大阴影
[ ] 无渐变
[ ] Surface / Canvas 使用正确
[ ] 1px Hairline 表达层级
[ ] 4px spacing grid
[ ] 表格紧凑
[ ] 没有 KPI 假数据
[ ] 没有资源/费用假 Tab
[ ] PageHeader 已复用
[ ] StatusTag 已复用
[ ] ADMIN 写按钮可见
[ ] 只读角色无写按钮
[ ] 后端才是权限边界
```

---

# 三十八、Gate 2 验收标准

只有以下全部通过才允许：

```text
Gate 2: PASS
```

Database：

```text
projects 存在
project_members 存在
Alembic head 正常
空库迁移 PASS
测试库独立
```

Backend：

```text
Project CRUD PASS
Project Member PASS
负责人关系 PASS
Scope 真实过滤 PASS
Audit Log PASS
```

Roles：

```text
ADMIN = GLOBAL + WRITE
BOSS = GLOBAL + READ
PROJECT_MANAGER = MANAGED_PROJECTS + READ
MEMBER = MEMBER_PROJECTS + READ
```

Frontend：

```text
项目菜单真实存在
项目列表真实 API
项目详情真实 API
成员真实 API
无假数据
IBM UI PASS
```

Tests：

```text
Gate 1 原 32 tests 不退化
Gate 2 新测试全部 PASS
连续运行 pytest 两次 PASS
npm run build PASS
```

---

# 三十九、阶段报告

完成后必须生成：

```text
docs/GATE2-IMPLEMENTATION-REPORT.md
docs/GATE2-TEST-REPORT.md
docs/GATE2-SCOPE-VERIFICATION.md
docs/GATE2-IBM-UI-REVIEW.md
docs/GATE2-CLOSURE-REPORT.md
```

---

# 四十、GATE2-SCOPE-VERIFICATION 要求

必须用真实运行数据验证：

```text
Project A
manager = pm_employee
members = member_employee

Project B
manager = other_pm
members = other_member
```

分别使用：

```text
admin
boss
pm
member
```

调用：

```text
GET /api/projects
GET /api/projects/{id}
```

记录真实返回。

不能只写“代码检查正确”。

---

# 四十一、GATE2-IBM-UI-REVIEW 要求

必须记录：

```text
修改文件
每个页面使用的 IBM Token
IBM-DESIGN 未覆盖场景
未覆盖场景如何处理
是否新增自定义视觉规则
是否出现大圆角/阴影/渐变
ADMIN 与只读角色按钮差异
npm build 结果
浏览器实测结果
```

原则：

```text
IBM 没明确规定
→ 保持稳定结构
→ 使用现有 IBM Token
→ 不创造第三套视觉体系
```

---

# 四十二、Gate 2 完成后的能力

Gate 2 CLOSED 后：

```text
管理员：
创建项目
指定负责人
添加成员
移除成员
修改项目
归档项目

老板：
查看全部项目
查看项目成员

负责人：
只看自己负责的项目

普通成员：
只看自己参与的项目
```

此时：

```text
GLOBAL
MANAGED_PROJECTS
MEMBER_PROJECTS
```

才算真正落地。

---

# 四十三、下一 Gate

Gate 2 CLOSED 后：

```text
Gate 3：企业资源账号管理
```

Gate 3 才允许：

```text
资源类型
资源账号
资源分配
共享资源账号
资源与项目
资源与成员
```

费用仍留 Gate 4。

---

# 四十四、给 Codex / Cursor 的直接执行提示词

你现在位于“企业项目资源与费用管理系统”真实项目仓库。

当前状态：

```text
Gate 0 PASS
Gate 1 PASS
32 tests passed
Next Gate = Gate 2
```

请先读取并核对：

```text
docs/GATE0-IMPLEMENTATION-REPORT.md
docs/GATE1-IMPLEMENTATION-REPORT.md
docs/GATE1-TEST-REPORT.md
docs/GATE1-CLOSURE-REPORT.md

IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

然后执行：

```text
Gate 2：项目管理与真实 Scope
```

最高级要求：

1. 先检查真实仓库，不根据方案臆测现有代码。
2. 不修改 Gate 1 已冻结的认证与角色语义。
3. Employee 与 User 继续分离。
4. Project 负责人绑定 Employee，不绑定 User。
5. Project Member 使用多对多关系。
6. `MANAGED_PROJECTS` 必须通过 `projects.manager_employee_id` 做后端真实过滤。
7. `MEMBER_PROJECTS` 必须通过 `project_members` 做后端真实过滤。
8. 禁止后端返回全部、前端再过滤。
9. ADMIN 全局读写。
10. BOSS 全局只读。
11. PROJECT_MANAGER 负责项目只读。
12. MEMBER 参与项目只读。
13. 先建立独立 test database，解决 pytest 污染开发库。
14. 所有数据库变化使用 Alembic。
15. 所有写操作记录 Audit Log。
16. 不允许提前开发资源账号、费用、Dashboard。
17. Gate 2 新增前端必须严格读取并遵守 `IBM-DESIGN.md`。
18. Element Plus 只是实现工具，不得覆盖 IBM 视觉。
19. 禁止大圆角、大阴影、渐变、营销 Hero、KPI 假卡片。
20. 只有真实 API/Router 完成后才能增加项目菜单与页面。
21. 项目详情当前只允许“概览 / 成员”。
22. 每个逻辑块完成后运行测试。
23. Scope 必须做四角色运行态取证。
24. 前端完成后必须执行 IBM UI Review。
25. Gate 1 原 32 项测试不得回归失败。

严格按：

```text
G2-00 → G2-26
```

执行。

最终必须生成：

```text
docs/GATE2-IMPLEMENTATION-REPORT.md
docs/GATE2-TEST-REPORT.md
docs/GATE2-SCOPE-VERIFICATION.md
docs/GATE2-IBM-UI-REVIEW.md
docs/GATE2-CLOSURE-REPORT.md
```

最终输出：

```text
Gate 2: PASS / FAIL

Test DB Isolation:
Projects:
Project Members:
Manager Relation:
GLOBAL Scope:
MANAGED_PROJECTS Scope:
MEMBER_PROJECTS Scope:
Audit:
Frontend:
IBM UI:
Build:
Tests:

Known Issues:
Next Gate:
```

只有全部真实验收通过后，才能宣告 Gate 2 CLOSED。

不得只输出方案，现在开始从真实代码实施。

# 企业项目资源与费用管理系统
# Gate 3 企业资源账号管理开发执行文档

版本：V1.0  
阶段：Gate 3  
前置状态：Gate 0 PASS / Gate 1 PASS / Gate 2 PASS  
Gate 2 回归：55 passed  
目标：完成企业资源类型、资源账号、资源分配、多人共享、项目/成员关联、资源访问 Scope 与资源生命周期管理。

---

# 1. Gate 3 进入条件

当前已确认：

```text
Gate 0: PASS
Gate 1: PASS
Gate 2: PASS

Auth: PASS
RBAC: PASS
Project Scope: PASS
Test DB Isolation: PASS
IBM UI Review: PASS
Tests: 55 passed
```

Gate 2 已实现：

- Project / ProjectMember
- ADMIN = GLOBAL + WRITE
- BOSS = GLOBAL + READ
- PROJECT_MANAGER = MANAGED_PROJECTS + READ
- MEMBER = MEMBER_PROJECTS + READ
- 项目 Scope 后端真实过滤
- 独立 `project_cost_hub_test`
- Alembic head = `0003_gate2_projects`

Gate 3 不得破坏上述冻结语义。

---

# 2. Gate 3 核心业务目标

本阶段只完成：

```text
资源类型
    ↓
企业资源账号
    ↓
资源分配
    ↓
项目
    ↓
成员
```

系统必须回答：

- 公司购买了哪些资源？
- 这些资源是什么类型？
- 当前资源状态是什么？
- 一个资源分配给了哪个项目？
- 一个资源由哪些成员使用？
- 一个成员正在使用哪些资源？
- 一个资源是否多人共享？
- 资源何时开始使用？
- 资源什么时候到期？
- 谁曾经使用过这个资源？
- 哪些资源当前没有分配？

---

# 3. Gate 3 明确不做

本阶段禁止提前开发：

```text
金额
订阅费用
API 用量金额
服务器账单
一次性费用
周期费用
费用分摊
费用统计
预算
财务 Dashboard
Excel 费用导入
```

上述内容统一进入：

```text
Gate 4：费用管理
```

Gate 3 可以保存与资源生命周期有关的日期和套餐名称，但不能把价格模型提前塞入资源表。

---

# 4. 前端最高级约束

所有 Gate 3 前端新增和修改必须先读取：

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

优先级：

```text
真实业务
>
PROJECT-UI-CONSTRAINTS.md
>
IBM-DESIGN.md
>
Element Plus 默认视觉
>
工具自行发挥
```

禁止：

- 新建第二套 Design System
- 大圆角
- 大阴影
- 渐变
- 玻璃拟态
- SaaS 营销卡片
- AI 星光/科技装饰
- 无业务意义图标
- KPI 假数据卡
- 每个字段一个 Card
- 为“视觉完整”提前展示费用 Tab

---

# 5. Gate 3 数据模型

新增三张核心表：

```text
resource_types
resource_accounts
resource_allocations
```

不破坏：

```text
employees
users
projects
project_members
roles
audit_logs
```

---

# 6. resource_types

资源类型由管理员维护。

建议字段：

```text
id
code
name
category
description
is_active
created_at
updated_at
```

`code` 唯一。

建议 category：

```text
AI
DEVELOPMENT
DESIGN
GIT
CLOUD_SERVER
DATABASE
STORAGE
API
DOMAIN
EMAIL
OFFICE
SAAS
OTHER
```

示例：

```text
CHATGPT
CURSOR
CLAUDE
GITHUB
FIGMA
ALIYUN_ECS
OPENAI_API
MICROSOFT_365
```

注意：

`resource_type` 表示“资源是什么”，不表示费用。

---

# 7. resource_accounts

资源账号代表企业真实采购/持有的一项资源。

建议字段：

```text
id
resource_type_id
resource_name
provider
account_identifier
plan_name
status
purchased_at
activated_at
expires_at
remark
created_by
created_at
updated_at
```

字段含义：

- `resource_name`：内部可识别名称，例如 `Cursor-开发01`
- `provider`：Cursor / OpenAI / GitHub / 阿里云等
- `account_identifier`：登录邮箱、账号别名、实例 ID 等非秘密标识
- `plan_name`：Pro / Team / Enterprise / ECS 2C4G 等
- `expires_at`：资源到期日
- `remark`：普通备注

---

# 8. 禁止保存明文凭据

Gate 3 严禁保存：

```text
外部账号明文密码
API Key Secret
AccessKey Secret
Token Secret
数据库密码
SSH 私钥
```

如果需要记录账号，只保存：

```text
登录邮箱
账号名称
实例 ID
资源别名
```

不得新增：

```text
password
api_key
secret
token
credential
```

等明文业务字段。

未来如果确需凭据管理，必须单独立项：

```text
Credential Vault
```

并使用加密、独立权限和访问审计。

---

# 9. Resource Status

建议数据库保存稳定生命周期状态：

```text
ACTIVE
IDLE
EXPIRED
DISABLED
```

中文：

```text
ACTIVE    -> 使用中
IDLE      -> 闲置
EXPIRED   -> 已到期
DISABLED  -> 已停用
```

“即将到期”不要作为永久数据库状态。

应根据：

```text
expires_at
```

动态计算，例如：

```text
0 < expires_at - today <= 30 days
```

返回：

```text
is_expiring_soon = true
```

避免数据库状态和真实日期不一致。

---

# 10. resource_allocations

资源分配关系是 Gate 3 的核心。

建议字段：

```text
id
resource_account_id
project_id
employee_id
allocated_at
released_at
is_active
remark
created_by
created_at
updated_at
```

其中：

```text
project_id 可为空
employee_id 可为空
```

但必须满足：

```text
project_id 与 employee_id 不能同时为空
```

支持三种分配：

## A. 项目级资源

例如服务器：

```text
resource = 阿里云 ECS
project = 新华制药
employee = null
```

## B. 个人资源

例如公司级账号：

```text
resource = GitHub Enterprise Seat
employee = 李四
project = null
```

## C. 项目 + 成员

例如：

```text
resource = Cursor-开发01
project = 新华制药
employee = 李四
```

---

# 11. 成员与项目一致性

如果 allocation 同时填写：

```text
project_id
employee_id
```

则必须验证：

```text
employee 是该项目 active project_member
```

否则拒绝。

禁止把：

```text
不属于新华项目的员工
```

分配成：

```text
新华项目的资源使用人
```

---

# 12. 多人共享资源

一个 `resource_account` 必须允许存在多条 active allocation。

例如：

```text
ChatGPT-Team-01
├── 新华 / 张三
├── 新华 / 李四
└── 佳悦 / 王五
```

不要在 `resource_accounts` 中存：

```text
user_id
employee_id
project_id
```

作为单一归属。

归属全部通过：

```text
resource_allocations
```

表达。

---

# 13. 是否需要 is_shared

不建议把 `is_shared` 作为手工维护的真值。

共享状态应由：

```text
active allocation count
```

计算。

例如：

```text
active_allocation_count > 1
→ is_shared = true
```

API 可以返回计算字段：

```text
is_shared
active_user_count
active_project_count
```

避免人工勾选与真实分配关系不一致。

---

# 14. 分配历史

移除资源使用关系时：

禁止物理删除。

执行：

```text
is_active = false
released_at = now
```

重新分配同一资源给同一目标时：

第一版允许恢复旧 allocation：

```text
is_active = true
allocated_at = now
released_at = null
```

这样可保留基础历史语义。

---

# 15. Resource Scope

Gate 3 必须复用 Gate 2 的项目 Scope，不重新发明第二套项目权限。

---

# 16. ADMIN

```text
Role = ADMIN
Scope = GLOBAL
```

可：

```text
查看全部资源
创建资源类型
修改资源类型
创建资源账号
修改资源账号
停用资源账号
分配资源
释放资源
查看全部分配关系
```

---

# 17. BOSS

```text
Role = BOSS
Scope = GLOBAL
```

可查看：

```text
全部资源
全部资源分配
全部项目资源
全部成员资源
```

禁止任何写操作。

---

# 18. PROJECT_MANAGER

```text
Role = PROJECT_MANAGER
Scope = MANAGED_PROJECTS
```

只能查看：

```text
分配到自己负责项目的资源
```

包括：

- 项目级资源
- 项目成员资源
- 共享到该项目的资源

不得查看：

- 其他项目资源
- 仅公司级且未关联自己项目的资源
- 其他项目成员的资源

仍然只读。

---

# 19. MEMBER

```text
Role = MEMBER
Scope = MEMBER_PROJECTS
```

Gate 3 推荐最小披露原则：

普通成员只查看：

```text
直接分配给自己的 active 资源
```

以及这些资源对应的：

```text
自己参与的项目
```

MEMBER 不应看到：

```text
同项目其他成员具体使用了哪些账号
```

除非未来产品明确增加权限。

---

# 20. Resource Scope Service

新增统一资源 Scope 服务，例如：

```text
permissions/resource_scope.py
```

必须复用：

```text
ProjectScopeService
```

而不是复制 Gate 2 逻辑。

推荐能力：

```text
readable_resources(current_user)
can_read_resource(resource_id, current_user)
readable_allocations(current_user)
```

---

# 21. 资源列表 Scope 逻辑

## ADMIN / BOSS

```text
全部
```

## PROJECT_MANAGER

资源必须存在 active allocation：

```text
allocation.project_id IN current_user.managed_project_ids
```

## MEMBER

资源必须存在 active allocation：

```text
allocation.employee_id == current_user.employee_id
```

如果 allocation 带 project：

还必须保证：

```text
project 在 MEMBER 的 active member projects 中
```

---

# 22. Resource Type API

建议：

```http
GET    /api/resource-types
POST   /api/resource-types
GET    /api/resource-types/{id}
PUT    /api/resource-types/{id}
POST   /api/resource-types/{id}/disable
POST   /api/resource-types/{id}/enable
```

读取：

```text
所有登录用户可读取 active 类型
```

写：

```text
仅 ADMIN
```

---

# 23. Resource Account API

建议：

```http
GET    /api/resources
POST   /api/resources
GET    /api/resources/{id}
PUT    /api/resources/{id}
POST   /api/resources/{id}/disable
POST   /api/resources/{id}/enable
```

支持列表筛选：

```text
keyword
resource_type_id
category
status
project_id
employee_id
expiring_soon
page
page_size
```

注意：

筛选不能扩大 Scope。

例如 MEMBER 传：

```text
employee_id=其他人
```

不得看到其他人的资源。

---

# 24. Resource Allocation API

建议：

```http
GET    /api/resources/{id}/allocations
POST   /api/resources/{id}/allocations
DELETE /api/resources/{id}/allocations/{allocation_id}
```

也可增加：

```http
GET /api/resource-allocations
```

供 ADMIN/BOSS 全局检索。

写操作仅 ADMIN。

---

# 25. API 响应字段

资源列表建议返回：

```json
{
  "id": 1,
  "resource_name": "Cursor-开发01",
  "resource_type": {
    "id": 1,
    "code": "CURSOR",
    "name": "Cursor",
    "category": "DEVELOPMENT"
  },
  "provider": "Cursor",
  "account_identifier": "dev01@example.com",
  "plan_name": "Pro",
  "status": "ACTIVE",
  "expires_at": "2027-01-01",
  "is_expiring_soon": false,
  "is_shared": true,
  "active_user_count": 2,
  "active_project_count": 1
}
```

不得返回任何密码/Secret。

---

# 26. Audit Log

Gate 3 必须新增 action：

```text
RESOURCE_TYPE_CREATE
RESOURCE_TYPE_UPDATE
RESOURCE_TYPE_DISABLE
RESOURCE_TYPE_ENABLE

RESOURCE_CREATE
RESOURCE_UPDATE
RESOURCE_DISABLE
RESOURCE_ENABLE

RESOURCE_ALLOCATION_ADD
RESOURCE_ALLOCATION_RELEASE
RESOURCE_ALLOCATION_RESTORE
```

必须记录：

- 操作人
- 资源 ID
- 项目 ID
- Employee ID
- before / after 必要字段

不得记录外部凭据。

---

# 27. Alembic

新增正式迁移：

```text
0004_gate3_resources
```

必须验证：

```text
空 schema
0001
→ 0002
→ 0003
→ 0004
```

完整升级。

pytest 继续强制使用：

```text
project_cost_hub_test
```

---

# 28. 开发库历史测试数据

Gate 2 已知：

```text
开发库仍存在 Gate 1 时期 pytest 测试人员
```

这不是 Gate 3 Blocker。

但在未来导入真实公司人员前必须清理。

Gate 3 不允许“顺手删除”未知历史数据。

如需要清理：

必须单独生成：

```text
DEV-DATA-CLEANUP-PLAN.md
```

先识别测试数据来源，再人工确认。

---

# 29. 前端页面规划

Gate 3 允许新增：

```text
/resources
/resources/:id
```

ADMIN 可额外访问资源类型管理。

可选：

```text
/resource-types
```

如果资源类型管理规模很小，也可以在资源页通过 Dialog/Drawer 管理，不强制独立页面。

---

# 30. 左侧菜单

新增：

```text
资源账号
```

角色：

```text
ADMIN           显示
BOSS            显示
PROJECT_MANAGER 显示
MEMBER          显示
```

但是：

```text
不同角色看到的数据由后端 Scope 决定
```

不得前端拿全量再过滤。

---

# 31. 资源列表页

建议：

```text
frontend/src/views/resources/ResourceListView.vue
```

PageHeader：

```text
资源账号
```

描述：

```text
查看企业采购资源及其项目和成员分配情况
```

ADMIN 右侧：

```text
新建资源
资源类型
```

其他角色：

```text
无写按钮
```

---

# 32. 列表筛选

紧凑横向筛选：

```text
关键字
资源类型
状态
项目
使用人
到期状态
查询
重置
```

对 MEMBER：

无需显示“使用人”筛选，默认即本人。

---

# 33. 资源表格

建议列：

```text
资源名称
类型
平台
账号/标识
套餐
使用项目
使用人数
状态
到期时间
操作
```

ADMIN：

```text
查看
编辑
分配
停用
```

BOSS / PM / MEMBER：

```text
查看
```

不要显示费用列。

Gate 4 再加入费用信息。

---

# 34. 资源详情页

建议：

```text
frontend/src/views/resources/ResourceDetailView.vue
```

Gate 3 只允许两个 Tab：

```text
概览
分配记录
```

禁止提前创建：

```text
费用
账单
成本趋势
```

---

# 35. 资源概览

展示：

```text
资源名称
资源类型
平台
账号标识
套餐
状态
购买日期
启用日期
到期日期
是否即将到期
备注
创建时间
更新时间
```

使用 IBM descriptions / hairline / surface。

禁止一字段一卡片。

---

# 36. 分配记录

表格：

```text
项目
使用人
分配时间
释放时间
状态
操作
```

ADMIN：

```text
新增分配
释放
恢复
```

只读角色：

```text
无写操作
```

---

# 37. 新建资源 Dialog / Drawer

字段：

```text
资源名称 *
资源类型 *
平台
账号/标识
套餐
状态 *
购买日期
启用日期
到期日期
备注
```

不得出现：

```text
费用
单价
月费
价格
```

---

# 38. 新增分配 Dialog

字段：

```text
项目
成员
分配时间
备注
```

业务规则：

- 项目与成员至少选一个
- 如果同时选项目 + 成员，成员必须属于项目
- 可创建项目级资源
- 可创建成员级资源
- 可多人共享同一资源

---

# 39. IBM UI 要求

继续复用：

```text
PageHeader.vue
StatusTag.vue
AdminLayout.vue
tokens.css
style.css
```

必须：

```text
IBM Blue #0f62fe
IBM Plex Sans 字体栈
0px radius
1px hairline
Surface / Canvas
4px spacing grid
紧凑表格
```

禁止：

```text
资源统计彩色卡片
大面积图标
图标宫格
账号平台 Logo 墙
渐变
阴影
大圆角
```

---

# 40. 状态视觉

Resource Status：

```text
ACTIVE   -> Success
IDLE     -> Neutral/Warning
EXPIRED  -> Error
DISABLED -> Neutral
```

`is_expiring_soon`：

可使用 Warning Tag。

不要把所有状态都用 IBM Blue。

---

# 41. Gate 3 自动测试

必须在 Gate 2 的 55 tests 基础上增加。

原 55 项不得回归。

---

# 42. Resource Type Tests

至少：

```text
ADMIN 创建资源类型成功
code 重复失败
ADMIN 修改类型成功
ADMIN 停用/启用成功
BOSS/PM/MEMBER 写接口 403
```

---

# 43. Resource Account Tests

至少：

```text
ADMIN 创建资源成功
无效 resource_type 失败
ADMIN 修改成功
ADMIN 停用/启用成功
接口不返回 secret 字段
数据库模型不存在明文 password/api_key/secret
```

---

# 44. Allocation Tests

至少：

```text
项目级分配成功
成员级分配成功
项目+成员分配成功
同一资源可多人共享
跨项目共享成功
项目+成员不匹配时失败
释放分配成功
释放后不再 active
恢复分配成功
```

---

# 45. Scope Tests

准备：

```text
Resource A -> Project A -> pm/member
Resource B -> Project B -> other_pm
Resource C -> unassigned
Resource D -> Project A -> another member
```

验证：

## ADMIN

```text
A/B/C/D 全部可见
可写
```

## BOSS

```text
A/B/C/D 全部可见
所有写接口 403
```

## PROJECT_MANAGER(pm)

```text
只看到 Project A 相关 A/D
看不到 B
看不到未分配 C
写接口 403
```

## MEMBER

```text
只看到直接分配给自己的资源 A
看不到同项目他人的 D
看不到 B/C
写接口 403
```

---

# 46. 越权测试

必须验证：

```text
member 传 employee_id=其他人不能扩大结果
pm 传 project_id=其他项目不能扩大结果
猜 resource id 无法读取越权资源
直接调用 allocation API 不能突破 Scope
非 ADMIN 不能通过 API 新建/修改/释放
```

---

# 47. 共享资源运行态取证

不能只自动测试。

必须使用真实账号：

```text
admin
boss
pm
member
```

并准备至少：

```text
一个项目级资源
一个个人资源
一个多人共享资源
一个其他项目资源
一个未分配资源
```

真实调用：

```text
GET /api/resources
GET /api/resources/{id}
GET /api/resources/{id}/allocations
```

记录返回。

---

# 48. 前端真实验收

## ADMIN

验证：

```text
资源菜单出现
新建资源
编辑资源
管理资源类型
新增分配
多人共享
释放资源
查看详情
```

## BOSS

```text
看到全部
只读
无写按钮
```

## PROJECT_MANAGER

```text
只看到负责项目相关资源
只读
```

## MEMBER

```text
只看到直接分配给自己的资源
看不到同项目其他成员资源
只读
```

---

# 49. Gate 3 开发顺序

严格按照：

```text
G3-00 扫描真实 Gate 2 代码与报告
G3-01 ResourceType Model
G3-02 ResourceAccount Model
G3-03 ResourceAllocation Model
G3-04 Alembic 0004
G3-05 Resource Schemas
G3-06 Resource Repository
G3-07 Resource Service
G3-08 Resource Scope Service
G3-09 Resource Type API
G3-10 Resource Account API
G3-11 Allocation API
G3-12 Allocation 一致性规则
G3-13 Shared Resource 规则
G3-14 Audit
G3-15 Backend CRUD Tests
G3-16 Scope Tests
G3-17 Security Tests
G3-18 读取 IBM-DESIGN / PROJECT-UI-CONSTRAINTS
G3-19 Frontend API
G3-20 Router / Menu
G3-21 ResourceListView
G3-22 新建/编辑 Resource
G3-23 ResourceDetailView
G3-24 Allocation UI
G3-25 Resource Type UI
G3-26 IBM UI Review
G3-27 npm run build
G3-28 pytest 全量回归
G3-29 四角色运行态取证
G3-30 Gate 3 报告
```

---

# 50. Gate 3 验收标准

只有全部通过才可：

```text
Gate 3: PASS
```

数据库：

```text
resource_types 存在
resource_accounts 存在
resource_allocations 存在
Alembic 0004 head
空库完整迁移 PASS
test DB 继续隔离
```

业务：

```text
资源类型 PASS
资源账号 PASS
项目级分配 PASS
成员级分配 PASS
多人共享 PASS
跨项目共享 PASS
释放/恢复 PASS
```

权限：

```text
ADMIN = 全部 + WRITE
BOSS = 全部 + READ
PM = 管理项目相关资源 + READ
MEMBER = 本人直接资源 + READ
```

安全：

```text
不保存明文资源密码
不保存 API Secret
越权资源 404/403
筛选参数不能扩大 Scope
```

前端：

```text
真实 API
IBM UI
无费用假数据
无费用 Tab
无第二套视觉体系
```

测试：

```text
原 55 tests 不退化
Gate 3 新测试全部 PASS
pytest 连续两次 PASS
npm run build PASS
```

---

# 51. Gate 3 输出报告

必须生成：

```text
docs/GATE3-IMPLEMENTATION-REPORT.md
docs/GATE3-TEST-REPORT.md
docs/GATE3-RESOURCE-SCOPE-VERIFICATION.md
docs/GATE3-SHARED-RESOURCE-VERIFICATION.md
docs/GATE3-IBM-UI-REVIEW.md
docs/GATE3-CLOSURE-REPORT.md
```

---

# 52. Gate 3 完成后的能力

Gate 3 CLOSED 后系统应具备：

```text
项目
↓
成员
↓
资源类型
↓
企业资源账号
↓
资源分配
↓
共享使用
↓
资源访问权限
```

能够回答：

> 谁在什么项目使用了什么企业资源？

但此时还不能完整回答：

> 花了多少钱？

因为金额和费用统一留给 Gate 4。

---

# 53. Next Gate

Gate 3 CLOSED 后：

```text
Gate 4：费用与计费管理
```

Gate 4 才实现：

- 周期订阅费用
- 一次性费用
- API 按量费用
- 服务器费用
- 费用归属
- 共享资源费用
- 月度费用
- 自动周期费用

---

# 54. 给 Cursor / Codex 的直接执行提示词

你现在位于“企业项目资源与费用管理系统”真实仓库。

当前已确认：

```text
Gate 0 PASS
Gate 1 PASS
Gate 2 PASS
55 tests passed
Alembic head = 0003_gate2_projects
test DB = project_cost_hub_test
```

请先读取：

```text
企业项目资源与费用管理系统_Gate3_企业资源账号管理_开发执行文档.md

docs/GATE2-IMPLEMENTATION-REPORT.md
docs/GATE2-TEST-REPORT.md
docs/GATE2-SCOPE-VERIFICATION.md
docs/GATE2-IBM-UI-REVIEW.md
docs/GATE2-CLOSURE-REPORT.md

IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

先扫描真实代码并输出：

```text
GATE3 CURRENT STATE
```

至少包括：

- 当前 Models
- 当前 Alembic head
- 当前 Project Scope 实现
- 当前 API
- 当前前端 Router/Menu
- 当前测试数量
- IBM UI 基础
- Gate 3 需要修改的真实文件
- 与 Gate 3 文档存在的差异

然后严格执行：

```text
G3-00 → G3-30
```

最高级要求：

1. 不回改 Gate 0/1/2 已冻结业务语义。
2. Resource 代表企业资源资产，不能直接绑定单一 Employee/Project。
3. Resource 与项目/人员的关系必须通过 `resource_allocations`。
4. 同一 Resource 必须允许多人共享。
5. 一个 Resource 可以跨项目存在多条 active allocation。
6. 如果 allocation 同时指定项目和成员，必须验证成员属于该项目。
7. PM 只读自己负责项目相关资源。
8. MEMBER 只读直接分配给自己的资源，不能看到同项目其他成员资源。
9. BOSS 全局只读。
10. ADMIN 全局读写。
11. 后端 Scope 才是真实权限边界。
12. 禁止前端获取全量后自己过滤。
13. 禁止保存资源明文密码、API Secret、Token Secret、SSH 私钥。
14. Gate 3 不允许增加金额、价格、费用、账单模型。
15. Gate 4 才处理所有费用。
16. 所有数据库变化使用 Alembic `0004`。
17. 所有资源写操作进入 Audit Log。
18. 测试继续强制使用 `project_cost_hub_test`。
19. Gate 2 原 55 tests 不得回归。
20. 前端编码前必须读取 `IBM-DESIGN.md`。
21. 新前端必须保持 0px radius / hairline / Surface / IBM Blue / IBM Plex Sans 栈。
22. 禁止大圆角、大阴影、渐变、AI/SaaS 卡片。
23. 资源详情当前只能有“概览 / 分配记录”。
24. 禁止提前增加“费用 / 账单 / 成本”Tab。
25. Scope 必须做 admin / boss / pm / member 真实运行态取证。
26. 必须验证共享资源真实链路。
27. 不要只输出方案，直接修改真实项目并测试。

最终必须生成：

```text
docs/GATE3-IMPLEMENTATION-REPORT.md
docs/GATE3-TEST-REPORT.md
docs/GATE3-RESOURCE-SCOPE-VERIFICATION.md
docs/GATE3-SHARED-RESOURCE-VERIFICATION.md
docs/GATE3-IBM-UI-REVIEW.md
docs/GATE3-CLOSURE-REPORT.md
```

最终输出：

```text
Gate 3: PASS / FAIL

Alembic:
Resource Types:
Resource Accounts:
Allocations:
Shared Resources:
Project Relation:
Member Relation:
GLOBAL Scope:
MANAGED_PROJECTS Resource Scope:
MEMBER Resource Scope:
Credential Safety:
Audit:
Frontend:
IBM UI:
Build:
Tests:

Known Issues:
Next Gate:
```

只有全部真实验收通过，才能宣告 Gate 3 CLOSED。

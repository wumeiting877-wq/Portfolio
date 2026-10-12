# 企业项目资源与费用管理系统
# Gate 6 企业化能力收口开发执行文档

版本：V1.0
阶段：Gate 6
前置状态：Gate 0 PASS / Gate 1 PASS / Gate 2 PASS / Gate 3 PASS / Gate 4 PASS / Gate 5 PASS
Gate 5 回归：163 passed × 2
目标：完成 Excel 导入导出、到期提醒、审计日志查询、系统设置、开发数据清理、备份恢复、真实数据导入准备与发布验收，使系统达到可长期内部使用状态。

---

# 一、Gate 6 进入条件

当前已确认：

```text
Gate 0: PASS
Gate 1: PASS
Gate 2: PASS
Gate 3: PASS
Gate 4: PASS
Gate 5: PASS

Tests: 163 passed × 2
Frontend Build: PASS
Alembic head: 0005_gate4_expenses
Test DB: project_cost_hub_test
```

当前系统核心业务已经闭环：

```text
身份 / 权限
↓
项目 / 成员
↓
资源账号 / 分配
↓
费用 / 分摊
↓
周期计费
↓
统计 / Dashboard
```

Gate 6 不再新增新的核心业务实体。

Gate 6 目标：

> 把当前系统从“业务功能完整”收口为“可维护、可导入、可导出、可审计、可备份、可发布”的内部企业系统。

---

# 二、Gate 6 最高级约束

不得：

- 回改 Gate 0–5 已冻结业务语义
- 改变 ADMIN / BOSS / PROJECT_MANAGER / MEMBER 权限定义
- 新增 AI 功能
- 新增审批流
- 新增报销系统
- 新增采购系统
- 新增复杂通知平台
- 新增消息队列，除非真实需求证明必要
- 为了“企业化”引入大型 ERP 能力
- 在未确认的情况下自动删除开发库数据
- 通过导入绕过业务校验 / Scope / Audit

Gate 6 优先：

```text
稳定
可维护
可恢复
可迁移
可审计
可交付
```

---

# 三、Gate 6 核心能力

本阶段完成：

```text
1. Excel 模板
2. Excel 导入
3. Excel 导出
4. 导入预检 / Preview
5. 到期提醒中心
6. 审计日志查询
7. 系统设置
8. 开发数据识别与清理方案
9. PostgreSQL 备份
10. PostgreSQL 恢复验证
11. 真实数据导入准备
12. 发布前安全检查
13. 发布前运行验收
14. V1.0 Release Closure
```

---

# 四、Excel 导入范围

第一版只允许 ADMIN 导入：

```text
人员
项目
项目成员
资源类型
资源账号
资源分配
费用记录
```

不建议第一版直接通过 Excel 导入：

```text
系统登录账号密码
角色权限
Audit Log
Recurring Expense Rules
```

系统登录账号继续由管理员在系统中创建。

---

# 五、Excel 导出范围

## ADMIN

允许导出：

```text
人员
项目
项目成员
资源账号
资源分配
费用明细
费用分摊
项目费用汇总
成员费用汇总
资源类型费用
即将到期资源
闲置资源
审计日志
```

## BOSS

只读导出：

```text
全局项目
全局资源
全局费用
费用汇总
即将到期
闲置资源
```

## PROJECT_MANAGER

只允许导出：

```text
自己负责项目
自己项目成员
自己项目资源
自己项目费用份额
```

## MEMBER

第一版只允许导出：

```text
我的资源
我的费用
```

禁止导出其他成员明细。

---

# 六、导出必须复用真实 Scope

禁止：

```text
导出接口单独查全表
```

导出必须复用：

```text
ProjectScope
ResourceScope
ExpenseScope
Statistics Scope
```

导出只是不同输出格式，不是绕过权限的新数据通道。

---

# 七、Excel 技术方案

使用：

```text
openpyxl
```

建议新增：

```text
backend/app/services/import_service.py
backend/app/services/export_service.py
backend/app/schemas/import_export.py
backend/app/api/imports/router.py
backend/app/api/exports/router.py
```

---

# 八、Excel 模板

必须提供标准模板下载。

建议 API：

```http
GET /api/imports/templates/{type}
```

type：

```text
employees
projects
project_members
resource_types
resources
resource_allocations
expenses
```

模板必须包含：

```text
字段名
是否必填
示例
说明
```

建议增加“说明”Sheet。

---

# 九、导入流程

必须采用：

```text
上传
↓
预检
↓
Preview
↓
错误列表
↓
用户确认
↓
正式导入
↓
结果报告
```

禁止：

```text
上传即直接写数据库
```

---

# 十、导入 Preview

建议：

```http
POST /api/imports/{type}/preview
```

返回：

```json
{
  "total_rows": 100,
  "valid_rows": 92,
  "invalid_rows": 8,
  "errors": [
    {
      "row": 12,
      "field": "employee_no",
      "message": "工号已存在"
    }
  ]
}
```

Preview 不得写入业务数据库。

---

# 十一、正式导入

建议：

```http
POST /api/imports/{type}/commit
```

必须：

- 仅 ADMIN
- 使用预检结果
- 再次校验
- 使用数据库事务
- 失败时整体回滚
- 写 Audit Log

禁止部分成功后静默忽略错误。

第一版推荐：

> 一个导入批次要么全部成功，要么整体失败。

---

# 十二、导入业务校验

## 人员

```text
employee_no 唯一
email 格式
employment_status 合法
```

## 项目

```text
project_code 唯一
负责人 Employee 存在且 ACTIVE
状态合法
```

## 项目成员

```text
Project 存在
Employee 存在
不得违反 active membership 规则
```

## 资源账号

```text
ResourceType 存在
status 合法
不允许 password / api_key / secret 字段
```

## 资源分配

```text
Resource 存在
Project / Employee 至少一个
项目+成员时必须是 active project_member
```

## 费用

```text
ExpenseType 存在
金额 Decimal
币种合法
分摊合计 == amount
项目/成员关系合法
```

---

# 十三、导入安全

必须防止：

```text
公式注入
超大文件
异常 Sheet
非法文件扩展名
恶意文件名
路径穿越
```

建议限制：

```text
.xlsx only
最大 10 MB
最大 10,000 行 / 批次
```

---

# 十四、Excel 导出格式

金额：

```text
数字单元格
2~4 位小数
币种独立列
```

日期：

```text
YYYY-MM-DD
```

不要把：

```text
CNY 100.00
```

写成无法计算的文本金额。

推荐：

```text
amount = 100.00
currency = CNY
```

---

# 十五、到期提醒中心

Gate 3 已有：

```text
expires_at
is_expiring_soon
```

Gate 5 已有：

```text
expiring-resources statistics
```

Gate 6 不重复建新事实。

只增加：

```text
提醒中心 / 提醒状态
```

第一版不强制邮件 / 微信 / Slack。

---

# 十六、Reminder 类型

建议第一版支持：

```text
RESOURCE_EXPIRING
RESOURCE_EXPIRED
RESOURCE_UNASSIGNED
RECURRING_RULE_DUE
```

其中优先级最高：

```text
RESOURCE_EXPIRING
```

---

# 十七、Notifications 表

为支持“已读 / 已处理”，推荐新增：

```text
notifications
```

字段：

```text
id
type
target_type
target_id
title
message
status
created_at
read_at
resolved_at
```

状态：

```text
UNREAD
READ
RESOLVED
```

如果落地该表，可与 system_settings 一起使用：

```text
0006_gate6_enterprise
```

---

# 十八、提醒生成

不引入 Celery。

建议：

```text
CLI 定时生成 + 页面主动刷新
```

脚本：

```bash
python -m app.scripts.generate_notifications
```

要求幂等：

```text
同一 target + type + 业务周期
不得重复生成多条未解决提醒
```

---

# 十九、提醒权限

## ADMIN / BOSS

可看全局提醒。

## PM

只看自己负责项目相关资源提醒。

## MEMBER

只看直接分配给自己的资源提醒。

必须复用 Resource Scope。

---

# 二十、Audit Log 查询

新增：

```text
GET /api/audit-logs
GET /api/audit-logs/{id}
```

前端：

```text
/audit-logs
```

---

# 二十一、Audit Log 权限

推荐：

```text
ADMIN -> 全部
BOSS -> 全部只读
PM -> 403
MEMBER -> 403
```

Audit Log 可能包含管理员操作、项目变化、费用调整，不向普通成员开放。

---

# 二十二、Audit Log 筛选

支持：

```text
operator
module
action
target_type
target_id
date_from
date_to
page
page_size
```

敏感字段继续保证：

```text
不显示 password
不显示 password_hash
不显示 secret
不显示 token
```

---

# 二十三、系统设置

Gate 6 只允许轻量系统设置：

```text
company_name
default_currency
business_timezone
expiring_days
page_size_default
```

`default_currency` 只作为新建费用默认值。

不代表实时汇率，不允许因此混合币种。

---

# 二十四、System Settings 权限

```text
ADMIN -> READ + WRITE
BOSS -> READ
PM -> 403
MEMBER -> 403
```

---

# 二十五、Settings 存储

建议固定字段模型：

```text
system_settings
```

例如单行配置：

```text
id
company_name
default_currency
business_timezone
expiring_days
page_size_default
updated_by
updated_at
```

避免开放任意 key/value 造成配置失控。

---

# 二十六、业务时区收口

Gate 5 已指出统计日期边界需要统一。

Gate 6 必须收口：

```text
business_timezone
```

后端：

```text
统计
提醒
日期默认值
```

统一使用该配置。

不要让前端与后端分别按不同本地时区切日。

---

# 二十七、开发数据清理

当前 Known Issue：

```text
开发库仍存在 Gate 1 时期 pytest 测试人员和既有 Gate 验证费用
```

Gate 6 不允许直接删除。

先生成：

```text
docs/DEV-DATA-CLEANUP-PLAN.md
```

必须识别：

- bootstrap 数据
- Gate 验证数据
- 可能的人工真实数据
- 外键依赖
- 删除顺序
- 回滚方案

---

# 二十八、开发数据识别

可依据：

```text
employee_no
project_code
resource_name
description
created_at
audit_log
```

例如：

```text
GATE2-
GATE3-
GATE4-
GATE5-
```

仅作为候选识别条件。

不得单凭前缀直接 DELETE。

---

# 二十九、数据清理脚本

建议：

```bash
python -m app.scripts.cleanup_dev_data --dry-run
```

默认只 dry-run。

输出：

```text
预计删除数量
预计保留数量
依赖影响
候选记录
```

真正执行必须显式：

```bash
python -m app.scripts.cleanup_dev_data --execute
```

并在执行前确认数据库名。

---

# 三十、PostgreSQL 备份

提供：

```text
scripts/backup.ps1
scripts/backup.sh
```

使用：

```text
pg_dump
```

备份文件：

```text
project_cost_hub_YYYYMMDD_HHMMSS.backup
```

备份目录加入 `.gitignore`。

---

# 三十一、恢复脚本

提供：

```text
scripts/restore.ps1
scripts/restore.sh
```

要求：

- 不默认覆盖当前开发库
- 必须显式指定目标 DB
- 恢复前清晰警告
- 默认建议恢复到临时数据库验证

---

# 三十二、备份恢复验收

必须真实执行：

```text
开发库备份
↓
恢复到 project_cost_hub_restore_test
↓
检查 Alembic
↓
检查关键表 COUNT
↓
关键数据抽样
↓
Smoke Test
```

禁止只写脚本不测试。

---

# 三十三、真实数据导入准备

Gate 6 不要求立刻导入公司真实数据。

但必须生成：

```text
docs/REAL-DATA-IMPORT-CHECKLIST.md
```

导入顺序：

```text
Employees
→ Projects
→ ProjectMembers
→ ResourceTypes
→ Resources
→ ResourceAllocations
→ ExpenseTypes
→ Expenses
```

---

# 三十四、生产配置检查

必须审计：

```text
JWT_SECRET_KEY
POSTGRES_PASSWORD
INITIAL_ADMIN_PASSWORD
APP_ENV
CORS
debug
日志级别
```

要求：

- 生产禁止 `change_me`
- JWT secret 不使用示例值
- DB 密码不使用示例值
- production 关闭 debug
- CORS 不无条件 `*`
- 日志不打印密码/token/secret

---

# 三十五、开发示例账号处理

开发现有：

```text
admin
boss
pm
member
```

生产发布清单必须明确：

- 默认密码全部更换
- 初始化管理员强制改密
- 示例 PM / MEMBER 是否创建由环境决定
- 生产默认不创建无必要的示例业务账号

---

# 三十六、启动与运维脚本

新增：

```text
scripts/start.ps1
scripts/stop.ps1
scripts/status.ps1
```

Windows 优先。

`start.ps1`：

- 检查 Docker
- 启动 Compose
- 等待 backend healthy
- 输出前后端地址

`stop.ps1`：

```text
docker compose down
```

`status.ps1`：

- docker compose ps
- /health
- /health/db

---

# 三十七、Version API

可增加：

```http
GET /version
```

返回：

```json
{
  "name": "project-cost-hub",
  "version": "1.0.0",
  "environment": "production"
}
```

不得返回 Secret、DB URL 等敏感信息。

---

# 三十八、README 收口

README 必须包含：

```text
项目定位
技术栈
项目目录
启动
停止
初始化管理员
数据库迁移
测试
Excel 导入导出
备份
恢复
权限模型
生产发布注意事项
```

---

# 三十九、START-HERE 收口

面向内部使用者，不写成架构论文。

建议：

```text
1. 启动系统
2. 登录
3. 创建人员
4. 创建项目
5. 创建资源
6. 分配资源
7. 录入费用
8. 查看 Dashboard
9. 导出数据
```

---

# 四十、Gate 6 前端页面

允许新增：

```text
/import-export
/notifications
/audit-logs
/settings
```

权限：

```text
Import/Export:
ADMIN -> Import + Export
BOSS -> Export
PM -> Scoped Export
MEMBER -> Self Export

Notifications:
所有角色，按 Scope

Audit Logs:
ADMIN / BOSS

Settings:
ADMIN WRITE
BOSS READ
```

---

# 四十一、IBM UI

所有新增页面继续遵守：

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

禁止：

- 设置页卡片墙
- 大圆角拖拽上传区
- 营销式插画
- 彩色通知 Feed
- Audit Log 大段 JSON 直接堆列表
- 渐变
- 大阴影

推荐：

```text
PageHeader
Hairline Section
DataTable
StatusTag
Dialog / Drawer
Progress / Result
```

---

# 四十二、导入页面

结构建议：

```text
PageHeader

数据类型
下载模板

选择 .xlsx

Preview Summary:
- 总行数
- 有效
- 错误

错误表格

确认导入
```

---

# 四十三、导出页面

字段：

```text
导出类型
时间范围
项目
币种
生成导出
```

项目下拉必须按当前 Scope。

---

# 四十四、通知中心

表格：

```text
类型
内容
关联资源
项目
到期日期
状态
操作
```

操作：

```text
标记已读
标记已处理
查看资源
```

---

# 四十五、Audit UI

列表：

```text
时间
操作人
模块
动作
对象
摘要
```

详情 Drawer：

```text
before
after
```

格式化展示，不在列表直接渲染完整 JSON。

---

# 四十六、Settings UI

单页分区：

```text
基础信息
时间与币种
提醒设置
分页
```

仅 ADMIN 显示保存按钮。

BOSS 只读。

---

# 四十七、Gate 6 自动测试

Gate 5 原：

```text
163 tests
```

不得回归。

---

# 四十八、Import Tests

至少：

```text
模板下载成功
.xlsx preview 成功
非法扩展名拒绝
超大文件拒绝
错误行返回 row/field
preview 不写数据库
commit 成功
commit 失败整体回滚
非 ADMIN import 403
password/api_key/secret 列拒绝
```

---

# 四十九、Export Tests

至少：

```text
ADMIN 全局导出
BOSS 全局只读导出
PM 仅负责项目
MEMBER 仅本人
CNY / USD 独立列
VOIDED 默认不进入有效费用导出
```

---

# 五十、Notification Tests

至少：

```text
即将到期生成
过期生成
未分配资源生成
重复生成幂等
ADMIN/BOSS 全局
PM 仅负责项目
MEMBER 仅本人
read
resolved
```

---

# 五十一、Audit Query Tests

至少：

```text
ADMIN 可查
BOSS 可查
PM 403
MEMBER 403
密码字段不可见
筛选正确
分页正确
```

---

# 五十二、Settings Tests

至少：

```text
ADMIN read/write
BOSS read
PM/MEMBER 403
business_timezone 生效
expiring_days 生效
default_currency 不触发汇率行为
```

---

# 五十三、Backup / Restore 验证

至少验证：

```text
backup file exists
restore DB created
alembic head correct
critical table counts match
关键数据一致
```

---

# 五十四、Release Smoke Test

新增：

```text
backend/app/scripts/release_smoke_test.py
```

至少验证：

```text
health
db
login
projects
resources
expenses
statistics
export
notifications
```

---

# 五十五、浏览器验收

## ADMIN

```text
Import
Export
Notifications
Audit
Settings
```

## BOSS

```text
Export
Notifications
Audit Read
Settings Read
无 Import
```

## PM

```text
Scoped Export
Scoped Notifications
无 Audit
无 Import
```

## MEMBER

```text
Self Export
Self Notifications
无 Audit
无 Import
```

---

# 五十六、Gate 6 开发顺序

```text
G6-00 扫描 Gate 5 真实状态
G6-01 明确 Import / Export Scope
G6-02 Excel Template Service
G6-03 Import Preview
G6-04 Import Commit
G6-05 Import Validation
G6-06 Export Service
G6-07 Export API
G6-08 Notification Model / Service
G6-09 Notification Generator
G6-10 Notification Scope
G6-11 Audit Log Query API
G6-12 System Settings Model / API
G6-13 business_timezone 收口
G6-14 DEV-DATA-CLEANUP-PLAN
G6-15 Cleanup Dry-run Script
G6-16 Backup Script
G6-17 Restore Script
G6-18 Backup / Restore 实测
G6-19 REAL-DATA-IMPORT-CHECKLIST
G6-20 Production Config Audit
G6-21 Version / Release Metadata
G6-22 Start / Stop / Status Scripts
G6-23 README / START-HERE 收口
G6-24 Import/Export 前端
G6-25 Notification 前端
G6-26 Audit Log 前端
G6-27 Settings 前端
G6-28 IBM UI Review
G6-29 Import / Export Tests
G6-30 Notification / Audit / Settings Tests
G6-31 pytest 全量回归
G6-32 npm run build
G6-33 Release Smoke Test
G6-34 四角色浏览器验收
G6-35 V1.0 发布清单
G6-36 Gate 6 报告
```

---

# 五十七、Gate 6 验收标准

只有全部通过才允许：

```text
Gate 6: PASS
```

Import：

```text
Template PASS
Preview PASS
Validation PASS
Transaction PASS
Audit PASS
```

Export：

```text
ADMIN GLOBAL
BOSS GLOBAL READ
PM scoped
MEMBER self
```

Notifications：

```text
Expiring PASS
Expired PASS
Unassigned PASS
Idempotent PASS
Scope PASS
```

Audit：

```text
ADMIN/BOSS PASS
PM/MEMBER denied
Sensitive fields hidden
```

Settings：

```text
ADMIN WRITE
BOSS READ
Timezone PASS
```

Operations：

```text
Backup PASS
Restore PASS
Start/Stop/Status PASS
Release Smoke PASS
```

Frontend：

```text
IBM UI PASS
Build PASS
```

Tests：

```text
原 163 tests 不退化
Gate 6 新 tests PASS
pytest 连续两次 PASS
```

---

# 五十八、Gate 6 输出报告

必须生成：

```text
docs/GATE6-IMPLEMENTATION-REPORT.md
docs/GATE6-TEST-REPORT.md
docs/GATE6-IMPORT-EXPORT-VERIFICATION.md
docs/GATE6-NOTIFICATION-SCOPE-VERIFICATION.md
docs/GATE6-BACKUP-RESTORE-VERIFICATION.md
docs/GATE6-RELEASE-SMOKE-REPORT.md
docs/GATE6-IBM-UI-REVIEW.md
docs/GATE6-CLOSURE-REPORT.md

docs/DEV-DATA-CLEANUP-PLAN.md
docs/REAL-DATA-IMPORT-CHECKLIST.md
docs/V1.0-RELEASE-CHECKLIST.md
```

---

# 五十九、V1.0 Release Checklist

至少检查：

```text
[ ] 默认密码已移除
[ ] JWT Secret 已替换
[ ] DB Password 已替换
[ ] APP_ENV=production
[ ] debug 关闭
[ ] CORS 已限制
[ ] Alembic head 正确
[ ] PostgreSQL 备份成功
[ ] 恢复测试成功
[ ] 测试全绿
[ ] 前端 build 成功
[ ] 四角色权限实测
[ ] 多币种正常
[ ] Import / Export Scope 正确
[ ] Audit 敏感字段安全
[ ] Reminder Scope 正确
[ ] README / START-HERE 完成
[ ] 真实数据导入清单完成
```

---

# 六十、Gate 6 完成后的状态

Gate 6 CLOSED 后，系统从：

```text
开发完成
```

升级为：

```text
V1.0 Release Candidate READY
```

具备：

```text
业务闭环
权限
资源
费用
统计
导入
导出
提醒
审计
设置
备份
恢复
发布验收
```

---

# 六十一、Next Phase

Gate 6 之后不建议立即继续加业务。

建议进入：

```text
V1.0 Pilot / 真实数据试运行
```

流程：

```text
清理开发数据
↓
备份空白基线
↓
导入真实人员
↓
导入真实项目
↓
导入真实资源
↓
导入真实费用
↓
真实用户试用
↓
收集问题
↓
V1.0.1 修复
```

---

# 六十二、给 Cursor / Codex 的直接执行提示词

你现在位于“企业项目资源与费用管理系统”真实仓库。

当前已确认：

```text
Gate 0 PASS
Gate 1 PASS
Gate 2 PASS
Gate 3 PASS
Gate 4 PASS
Gate 5 PASS

163 tests passed × 2
Alembic head = 0005_gate4_expenses
test DB = project_cost_hub_test
```

请先读取：

```text
企业项目资源与费用管理系统_Gate6_企业化能力收口_开发执行文档.md

docs/GATE5-IMPLEMENTATION-REPORT.md
docs/GATE5-TEST-REPORT.md
docs/GATE5-STATISTICS-SCOPE-VERIFICATION.md
docs/GATE5-MULTI-CURRENCY-VERIFICATION.md
docs/GATE5-DASHBOARD-RUNTIME-VERIFICATION.md
docs/GATE5-IBM-UI-REVIEW.md
docs/GATE5-CLOSURE-REPORT.md

IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

先扫描真实仓库并输出：

```text
GATE6 CURRENT STATE
```

至少包括：

- 当前 Models
- 当前 Alembic head
- 当前 Import / Export 能力
- 当前 Notification 能力
- 当前 Audit Log 查询能力
- 当前 Settings
- 当前脚本
- 当前 README / START-HERE
- 当前生产配置风险
- 当前开发数据污染情况
- 当前测试数量
- 当前 IBM UI 基础
- Gate 6 实际需要修改的文件
- 与 Gate 6 文档差异

然后严格执行：

```text
G6-00 → G6-36
```

最高级要求：

1. 不回改 Gate 0–5 已冻结业务语义。
2. Import 仅 ADMIN。
3. Import 必须 Preview 后 Commit。
4. Import Commit 必须事务化。
5. Import 不得绕过业务校验。
6. Import 不得允许 password / api_key / secret。
7. Export 必须复用已有 Scope。
8. ADMIN / BOSS 可全局导出。
9. PM 只能导出自己负责项目。
10. MEMBER 只能导出本人资源和费用。
11. 不同币种必须分列，不做混合总额。
12. 到期提醒必须复用 Resource Scope。
13. 提醒生成必须幂等。
14. Audit Log 仅 ADMIN / BOSS 可查。
15. Audit API 必须隐藏敏感字段。
16. Settings 仅 ADMIN 可写，BOSS 只读。
17. 收口 business_timezone。
18. 不得自动删除开发库历史数据。
19. 先生成 DEV-DATA-CLEANUP-PLAN。
20. Cleanup 默认只 dry-run。
21. 真正清理必须显式 `--execute`。
22. 提供 PostgreSQL backup / restore 脚本。
23. 必须真实恢复到独立 restore test DB 验证。
24. 生产环境禁止 change_me。
25. 生产关闭 debug。
26. CORS 不得无条件 `*`。
27. 发布前执行 release smoke test。
28. Gate 5 原 163 项测试不得回归。
29. 所有新增前端继续遵守 IBM-DESIGN.md。
30. 禁止大圆角、大阴影、渐变、营销式导入页。
31. 不要只生成脚本，要真实验证 backup/restore。
32. 不要只输出方案，直接修改真实代码并测试。

最终必须生成：

```text
docs/GATE6-IMPLEMENTATION-REPORT.md
docs/GATE6-TEST-REPORT.md
docs/GATE6-IMPORT-EXPORT-VERIFICATION.md
docs/GATE6-NOTIFICATION-SCOPE-VERIFICATION.md
docs/GATE6-BACKUP-RESTORE-VERIFICATION.md
docs/GATE6-RELEASE-SMOKE-REPORT.md
docs/GATE6-IBM-UI-REVIEW.md
docs/GATE6-CLOSURE-REPORT.md

docs/DEV-DATA-CLEANUP-PLAN.md
docs/REAL-DATA-IMPORT-CHECKLIST.md
docs/V1.0-RELEASE-CHECKLIST.md
```

最终输出：

```text
Gate 6: PASS / FAIL

Import Templates:
Import Preview:
Import Commit:
Export:
Notification:
Audit Log:
Settings:
Business Timezone:
Dev Data Cleanup Plan:
Backup:
Restore:
Release Smoke:
Production Config:
Frontend:
IBM UI:
Build:
Tests:

Known Issues:
Release Readiness:
Next Phase:
```

只有所有验收项通过，才能宣告：

```text
Gate 6 CLOSED
V1.0 Release Candidate READY
```

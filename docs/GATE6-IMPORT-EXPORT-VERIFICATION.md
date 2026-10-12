# Gate 6 Import / Export Verification

日期：2026-09-22  
结论：PASS

## Import 仅 ADMIN

- API：`require_admin`
- 前端：仅 `auth.canImport` 显示「导入」页签
- 测试：BOSS Preview 403
- 浏览器：ADMIN 有「导入 / 导出」双页签；BOSS / PM / MEMBER 仅「导出」

## Preview 不写库

`preview_import` 只跑 validator，不调用 persist。`test_preview_does_not_write` 对比 Preview 前后人员列表。

## Commit 事务与整批回滚

`deferred_commit` 把业务服务里的 `session.commit` 替换为 `flush`，批次结束后一次 `commit`；异常则 `rollback`。任一行校验失败直接 400，created_count=0。

导入 persist 复用：

```text
create_employee
create_project
add_or_restore_member
create_resource_type
create_resource
add_or_restore_allocation
create_expense / validate_and_build_distributions
```

不另开绕过 Scope / 分摊合计 / 成员关系的通道。费用来源允许 `IMPORT`。

## 凭据列拒绝

`excel_io.FORBIDDEN_HEADERS` 含 password / password_hash / api_key / secret / token / credential / access_key / private_key。表头命中即 400。测试覆盖 password 与 api_key。

## 文件安全

- 仅 `.xlsx`
- 最大 10 MB / 10,000 行
- 拒绝公式单元格
- 导出单元格以 `=` `+` `-` `@` 开头时加前导 `'`

## 模板

`GET /api/imports/templates/{type}` 含字段、是否必填、示例、说明 Sheet。类型：employees / projects / project_members / resource_types / resources / resource_allocations / expenses。不导入登录密码、角色、Audit、周期规则。

## Export 复用 Scope

| 类型 | Scope |
| --- | --- |
| projects / project_members | `readable_projects` |
| resources / allocations / expiring | `readable_resources` / `readable_allocations` |
| expenses / distributions | `readable_expenses` / `readable_distributions` |
| project_costs / employee_costs / resource_type_costs | Statistics Service |
| employees / audit_logs | ADMIN（audit 查询另有 BOSS 页面） |

## 角色导出范围（浏览器实测）

### ADMIN

人员、项目、项目成员、资源账号、资源分配、费用明细、费用分摊、项目费用汇总、成员费用汇总、资源类型费用、即将到期、闲置资源、审计日志。

### BOSS

仅导出页签。项目、资源账号、费用明细、项目费用汇总、成员费用汇总、资源类型费用、即将到期、闲置资源。无人员、无审计导出。

### PROJECT_MANAGER

项目、项目成员、资源账号、资源分配、费用明细、费用分摊、项目费用汇总、成员费用汇总、即将到期。项目下拉仅 Project A。

### MEMBER

资源账号、费用明细、即将到期资源。无导入。

## 多币种

费用导出列为 `amount` + `currency`。`money=True` 使用数字单元格 `0.00##`。VOIDED 排除。禁止混合总额列。

## 审计

Import Commit 写 `IMPORT_COMMIT` audit。

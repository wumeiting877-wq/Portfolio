# 开发数据清理计划

日期：2026-09-22  
状态：PLAN ONLY。未执行 DELETE。默认 `--dry-run`。

## 原则

- 不允许自动删除开发库测试数据
- 先识别，再人工确认，最后显式 `--execute`
- 测试库 `project_cost_hub_test` 由 pytest 自己 DROP SCHEMA，不走本脚本
- 恢复验证库 `project_cost_hub_restore_test` 不作为清理目标

## 必须保留

```text
员工号：ADMIN001 / BOSS001 / PM001 / MB001
登录名：admin / boss / pm / member
system_settings 单行
roles
```

## 识别规则

脚本：`python -m app.scripts.cleanup_dev_data --dry-run`

候选前缀：`GATE1-` … `GATE5-`（工号 / 姓名 / 项目编码 / 资源名 / 费用说明）。  
**前缀不是充分删除条件。** Gate 1 pytest 人员多数没有 GATE 前缀。

## 2026-09-22 dry-run 结果（开发库 project_cost_hub）

| 对象 | 总数 | 前缀候选 | 说明 |
| --- | --- | --- | --- |
| employees | 46 | 0 | 另有约 42 名无 GATE 前缀的 Gate 1 残留人员，**禁止按前缀误删，也禁止本轮自动删除** |
| projects | 2 | 2 | GATE2-A / GATE2-B |
| resources | 11 | 11 | GATE3-* / GATE5-* |
| expenses | 17 | 15 | 2 条无 GATE 前缀，需人工核对后再决定 |

未执行 `--execute`。执行后开发库 Dashboard「本月」数字会变化，需先备份。

## 若将来执行，建议顺序

1. `.\scripts\backup.ps1`
2. 把 backup 恢复到独立库抽查
3. `python -m app.scripts.cleanup_dev_data --dry-run` 再次打印候选
4. 人工勾选：无前缀员工、无前缀费用是否删除
5. 仅当明确需要空白试点库时：`python -m app.scripts.cleanup_dev_data --execute --database-name project_cost_hub`
6. 再备份「清理后基线」

删除顺序（脚本内）：费用分摊 → 费用 → 资源分配 → 资源 → 项目成员 → 项目 → 无登录账号的候选员工。有 User 的员工永不删除。

## 不在本计划删除

- 审计日志（保留追溯）
- 系统设置
- 角色
- pytest 测试库数据

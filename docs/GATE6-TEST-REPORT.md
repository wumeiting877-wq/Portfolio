# Gate 6 Test Report

日期：2026-09-22  
命令：`docker compose exec backend pytest`  
结果：196 passed（连续两次）  
测试库：`project_cost_hub_test`

## 隔离

pytest 仍强制独立测试库。session 开始 DROP SCHEMA + Alembic upgrade head + bootstrap。不写入开发库 `project_cost_hub`。

```text
第一次：196 passed
第二次：196 passed
```

Gate 5 原 163 项全部保留。新增 33 项。

## 新增测试文件

| 文件 | 项数 |
| --- | --- |
| `test_imports.py` | 11 |
| `test_exports.py` | 7 |
| `test_notifications.py` | 2 |
| `test_audit_query.py` | 4 |
| `test_settings.py` | 9 |

另：`test_alembic_config.py` 增加 `test_gate6_migration_file_exists`。

## Import

- 模板下载 200 + spreadsheet content-type
- Preview 成功：valid_rows=1，不写库
- 非 `.xlsx` 400
- 超 10 MB 400
- 错误返回 row + field（重复工号）
- Preview 前后人员数量不变
- Commit 成功写入
- 批次中有一行失败则整批回滚
- BOSS Preview 403
- `password` 列拒绝
- `api_key` 列拒绝

## Export

- ADMIN 全局导出项目
- BOSS 可全局导出项目
- PM 只导出自己负责项目，不见 `OTHR*`
- MEMBER 只导出自己的费用，不见他人 USD 行
- 金额列与 currency 列分开，禁止 `CNY 100.00` 文本混合
- VOIDED 费用不进入费用导出
- MEMBER 导出 audit_logs 403

## Notifications

- 生成 RESOURCE_EXPIRING / RESOURCE_EXPIRED / RESOURCE_UNASSIGNED
- 连续 refresh 幂等，同一资源到期提醒仅 1 条
- ADMIN / BOSS 可见全局；PM / MEMBER 仅 Resource Scope 内
- 已读 / 已处理状态可写

## Audit

- ADMIN / BOSS 200
- PM / MEMBER 403
- 列表与详情不含 password / password_hash / 明文密码
- 模块过滤与分页有效

## Settings / 生产配置

- ADMIN 读写；BOSS GET 200 / PUT 403
- PM / MEMBER GET 403
- 非法时区 400
- 默认币种不产生跨币种 `total`
- production 拒绝 `change_me`、DEBUG、CORS `*`
- development 也拒绝 CORS `*`
- `/version` 返回 `1.0.0`，不含 secret

## 回归

Gate 0–5 原 163 项未退化。

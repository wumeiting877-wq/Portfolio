# Gate 6 Backup / Restore Verification

日期：2026-09-22  
结论：PASS

## 脚本

```text
scripts/backup.ps1
scripts/backup.sh
scripts/restore.ps1
scripts/restore.sh
```

Backup：`pg_dump -Fc` 到 `backups/project_cost_hub_YYYYMMDD_HHMMSS.backup`。`backups/` 与 `*.backup` 已 `.gitignore`。

Restore：必须 `--TargetDatabase`；若等于当前 `POSTGRES_DB` 则拒绝。先 DROP/CREATE 独立库再 `pg_restore`。

## 真实执行

Backup：

```text
BACKUP_OK backups/project_cost_hub_20260922_211247.backup
size = 88468 bytes
```

Restore 目标：`project_cost_hub_restore_test`（不是开发库 `project_cost_hub`，也不是 pytest 库 `project_cost_hub_test`）。

## 对照

| 项 | 开发库 | restore_test |
| --- | --- | --- |
| Alembic | `0006_gate6_enterprise` | `0006_gate6_enterprise` |
| employees | 46 | 46 |
| projects | 2 | 2 |
| resources | 11 | 11 |
| expenses | 17 | 17 |
| audit_logs | 154 | 154 |
| system_settings | 1 | 1 |
| notifications | 4 | 4 |

开发库未被覆盖。pytest 库仍为 `project_cost_hub_test`。

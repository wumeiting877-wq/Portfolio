# Gate 6 Notification Scope Verification

日期：2026-09-22  
结论：PASS

## 模型

`notifications` + unique `(type, target_type, target_id, period_key)`。  
Alembic：`0006_gate6_enterprise`。

类型：

```text
RESOURCE_EXPIRING
RESOURCE_EXPIRED
RESOURCE_UNASSIGNED
RECURRING_RULE_DUE
```

状态：UNREAD / READ / RESOLVED。

## 生成

- CLI：`python -m app.scripts.generate_notifications`
- 页面：`POST /api/notifications/refresh`
- 业务日：`business_today()` ← `system_settings.business_timezone`（默认 Asia/Shanghai）
- 到期天数：`get_expiring_days()`，覆盖原硬编码 30 天只读计算

幂等：`_create_if_absent` + unique 约束。连续 refresh 同一资源到期提醒仍为 1 条。

不引入邮件 / 队列 / Celery。Gate 3 `is_expiring_soon` 仍为动态计算，不把 EXPIRING_SOON 写成资源状态。

## Scope

`readable_notifications`：

- ADMIN / BOSS：全局
- 其他角色：`Notification.resource_account_id IN readable_resources(...)`

复用 Gate 3 Resource Scope，不另查全表。

pytest：

- ADMIN / BOSS 同时看见 mine 与 other
- PM 看见已分配到自己项目的 mine，看不见 other
- MEMBER 同 Resource Scope

## 浏览器

- ADMIN 提醒中心 4 条：GATE5-EXPIRING 未分配 + 即将到期（2026-10-02）、GATE5-UNASSIGNED、GATE3-C
- MEMBER 提醒中心 0 条（无权看全局未分配资源）
- PM 菜单有提醒中心，无审计 / 设置

## 操作

标记已读 / 已处理仅对可读提醒生效；越权返回 404「提醒不存在」。

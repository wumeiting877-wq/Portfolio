# Gate 3 Shared Resource Verification

日期：2026-09-22  
方式：对运行中的后端使用真实账号调用 API  
脚本：`backend/app/scripts/verify_gate3_shared.py`

验证同一资源可多人共享、可跨项目存在多条 active allocation，且 Scope 仍按角色裁剪分配可见性。

## 准备资源

| 资源 | 类型 | 分配 |
| --- | --- | --- |
| GATE3-ECS-新华 | 项目级 | Project A，无使用人 |
| GATE3-GitHub-Seat | 个人 | member，无项目 |
| GATE3-ChatGPT-Team-01 | 多人共享 | Project A / pm；Project A / member；Project B / PM002 |

## 共享资源本体

`GET /api/resources/{shared_id}`（admin）HTTP 200：

```json
{
  "id": 7,
  "name": "GATE3-ChatGPT-Team-01",
  "is_shared": true,
  "active_user_count": 3,
  "active_project_count": 2
}
```

`is_shared` 由 active allocation count 计算，不是手工勾选字段。

## ADMIN 分配记录

三条 active allocation 全部可见：

```text
Project B / 另一负责人 (PM002)
Project A / 普通成员 (MB001)
Project A / 项目负责人 (PM001)
```

## PROJECT_MANAGER (pm) 可见资源

```text
GATE3-ChatGPT-Team-01
GATE3-ECS-新华
GATE3-D
GATE3-A
```

- 能看到共享到自己项目的 ChatGPT
- 能看到项目级 ECS
- 不能看到仅分配给 member、且无项目的 GitHub Seat（公司级个人资源）
- 不能看到 Project B 独有资源 GATE3-B

共享资源分配记录（pm）：

```text
employee_ids = [4, 3]
```

只含 Project A 的 pm 与 member，不含 Project B 的 PM002。

## MEMBER 可见资源

```text
GATE3-ChatGPT-Team-01
GATE3-GitHub-Seat
GATE3-A
```

- 能看到直接分配给自己的共享账号和个人 GitHub Seat
- 不能看到同项目他人资源 GATE3-D
- 不能看到项目级 ECS（没有直接分配给自己）
- 不能看到 Project B 资源

共享资源分配记录（member）：

```text
employee_ids = [4]
```

只含自己。同项目负责人、其他项目使用人不可见。

## 浏览器

admin 详情「分配记录」可见三条跨项目分配，并有「新增分配 / 释放」。  
member 列表仅「查看」，使用项目列对共享资源只显示 Project A（来自自己可读的 allocation），不展示 Project B。

## 结论

- 同一个 resource_account 支持多人共享
- 同一个资源允许跨项目多条 active allocation
- 资源表不绑定单一 Employee / Project
- MEMBER 最小披露：只看到自己的账号使用关系
- PM 只看到自己负责项目上的分配

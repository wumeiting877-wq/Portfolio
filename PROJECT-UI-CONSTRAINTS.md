# 项目 UI 业务约束

本文件只定义当前项目的业务边界与实现约束，不定义或改写视觉规范。

后续前端任务必须按以下顺序执行：

1. 读取 `./IBM-DESIGN.md`，确定页面视觉。
2. 读取 `./PROJECT-UI-CONSTRAINTS.md`，确定业务边界。
3. 读取真实代码与 API，确定真实功能。
4. 开始编码。

优先级：

```text
真实业务
>
PROJECT-UI-CONSTRAINTS.md
>
IBM-DESIGN.md 视觉规则
>
Element Plus 默认样式
>
Cursor 自己的设计判断
```

## 当前技术栈

```text
Vue 3
Vite
TypeScript
Element Plus
Pinia
Vue Router
Axios
```

## UI 实现策略

可以继续使用 Element Plus 实现页面，但 Element Plus 只是实现工具。

页面最终视觉必须以 `./IBM-DESIGN.md` 为准，不得因为 Element Plus 默认样式而偏离 IBM 风格，也不得另行建立或重新设计一套企业后台视觉规范。

`frontend/src/styles/tokens.css` 是 `IBM-DESIGN.md` 的代码实现层，不是项目自己的第二套 Design System：

```text
IBM-DESIGN.md
↓
tokens.css
↓
Element Plus
```

当 IBM 规范与当前实现对照时：

```text
符合 IBM-DESIGN.md
→ 保留

与 IBM-DESIGN.md 存在明确冲突
→ 修改

IBM-DESIGN.md 没有规定
→ 保持当前实现，不自行创造新规则
```

## 业务保护

禁止修改：

```text
backend
database
API
Router 业务语义
Store 业务结构
权限
角色 code
登录逻辑
强制改密
人员字段
系统账号字段
```

## 当前真实页面

只有：

```text
/login
/change-password
/
/statistics
/projects
/projects/:id
/resources
/resources/:id
/expenses
/expenses/:id
/recurring-expenses
/employees
/users
/import-export
/notifications
/audit-logs
/settings
```

禁止为 UI 完整性创建当前不存在的：

```text
角色权限配置页
```

项目详情当前允许：

```text
概览
成员
费用
```

资源详情当前允许：

```text
概览
分配记录
费用记录
```

费用与周期规则页面必须走真实 API。首页 `/` 为角色化 Dashboard，`/statistics` 为详细统计分析，均走 Statistics API。

只有真实路由与 API 存在后，才能增加相应页面、菜单或数据展示。

## 角色与权限

必须保留真实角色 code、权限判断与路由访问语义，不得为视觉实现改名或改写：

```text
ADMIN
BOSS
PROJECT_MANAGER
MEMBER
```

菜单必须服从当前权限：

- 首页：所有已登录角色；数据由后端 Statistics Scope 过滤。
- 统计分析：所有已登录角色；MEMBER 仅本人费用与资源，无项目/员工排行。
- 项目管理：所有已登录角色；数据由后端 Scope 过滤。
- 资源账号：所有已登录角色；数据由后端 Resource Scope 过滤。
- 人员管理：`ADMIN`、`BOSS`。
- 系统账号：仅 `ADMIN`。
- 费用管理：所有已登录角色；数据由后端 Expense Scope 过滤。
- 周期规则：`ADMIN`、`BOSS`；写操作仅 `ADMIN`。
- 导入导出：所有已登录角色可见导出；导入仅 `ADMIN`。
- 提醒中心：所有已登录角色；数据由后端 Resource Scope 过滤。
- 审计日志：`ADMIN`、`BOSS`。
- 系统设置：`ADMIN` 可写，`BOSS` 只读。

## 账号概念

必须区分：

```text
系统登录账号
```

和未来：

```text
资源账号
```

系统登录账号用于登录本系统。未来资源账号是被管理的资源或资产。两者不得混淆，文案中不得在语义不明确时笼统称为“账号”。

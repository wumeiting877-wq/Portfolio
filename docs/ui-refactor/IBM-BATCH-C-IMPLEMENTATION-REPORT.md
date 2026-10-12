# IBM UI Batch C 实施报告

日期：2026-09-22  
范围：`EmployeeListView.vue`、`UserListView.vue`，以及本轮真实需要的 `PageHeader.vue` 最小调整与 `style.css` 列表/表格/对话框公共样式。  
视觉来源：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`  
结论：完成；`npm run build` PASS；`/employees`、`/users` 业务回归 PASS；四类角色权限回归 PASS；未修改业务逻辑。

未读取、未引用 `DESIGN-PROJECT-ADAPTATION-ARCHIVE.md` 作为视觉规则。

---

## 1. 修改文件

- `frontend/src/views/employees/EmployeeListView.vue`
- `frontend/src/views/users/UserListView.vue`
- `frontend/src/style.css`
  - 增加列表页 Toolbar / Content Panel / Table / Dialog / MessageBox 的 IBM 映射样式
  - 补齐备注字段使用的 Textarea，使其跟随已校准的 IBM `text-input`
- `frontend/src/components/PageHeader.vue`
  - 仅当没有说明文字时，主操作与标题垂直居中；有说明时仍顶部对齐

新增：

- `docs/ui-refactor/IBM-BATCH-C-IMPLEMENTATION-REPORT.md`

未修改：

- `frontend/src/components/StatusTag.vue`（本轮直接复用已有 employee / account / role 映射）
- `frontend/src/styles/tokens.css`
- `frontend/src/layouts/AdminLayout.vue`
- `frontend/src/router/index.ts`
- `frontend/src/stores/auth.ts`
- `backend/`、API、Axios、权限 getter、角色 code

未新增通用表格组件或 CRUD 框架。

---

## 2. EmployeeListView 改动

保留真实功能：

- 搜索姓名或工号
- 查询
- 新建人员（仅 `canWriteEmployees`）
- 编辑
- 停用（仅 `employment_status === 'ACTIVE'` 可点）
- 列表加载与 `v-loading`

视觉与结构：

```text
PageHeader「人员管理」+ actions「新建人员」
Toolbar：[搜索框] [查询]
Content Panel
  Table
Dialog：新建人员 / 编辑人员
```

- 去掉外层 `el-card`。
- 人员状态不再直接显示 `ACTIVE` / `INACTIVE` / `LEFT`，改为 `StatusTag kind="employee"`：
  - `ACTIVE` → 在职
  - `INACTIVE` → 停用
  - `LEFT` → 离职
- 行内「编辑」保持蓝色文字按钮；「停用」保持 `danger` 文字按钮。
- 未新增假筛选。
- 未改 API 参数、人员字段或停用确认逻辑。
- BOSS 仍可进入列表并搜索，但不显示新建 / 编辑 / 停用。

---

## 3. UserListView 改动

保留真实功能：

- 创建账号
- 行内修改角色（原 `el-select` + `updateUser({ role_id })`）
- 重置密码 Dialog
- 停用确认 / 启用入口
- 绑定人员展示与创建时过滤 `!has_account`

视觉与结构：

```text
PageHeader「系统账号」
  说明：管理登录本系统使用的账号、角色和账号状态。
  actions：「创建账号」
Content Panel
  Table
Dialog：创建系统账号 / 重置密码
```

- 去掉外层 `el-card` 与空 Toolbar。
- 未新增搜索、角色筛选或状态筛选。
- 账号状态改为 `StatusTag kind="account"`：
  - `ACTIVE` → 启用
  - `DISABLED` → 停用
  - `LOCKED` → 锁定
- 角色下拉中文映射：
  - `ADMIN` → 管理员
  - `BOSS` → 老板
  - `PROJECT_MANAGER` → 负责人
  - `MEMBER` → 成员
- 创建 Dialog 选项为「管理员 (ADMIN)」形式，避免只显示 code，同时保留原有 code 提示。
- 「启用」由绿色 `success` 文字改为蓝色文字，避免角色/操作用成功色；「停用」仍为 `danger`。
- 未改创建、改角色、重置密码、启停的 API 与确认逻辑。

---

## 4. PageHeader 使用情况

两个页面都不再自行写页面 `h1` / `h2` 作为页标题。

| 页面 | 标题 | 说明 | Primary Action |
| --- | --- | --- | --- |
| EmployeeListView | 人员管理 | 无。当前无必要补充说明 | 新建人员（仅 ADMIN 写权限） |
| UserListView | 系统账号 | 管理登录本系统使用的账号、角色和账号状态。 | 创建账号 |

每页只有一个蓝色 Primary。查询按钮使用已校准的 IBM Secondary（炭黑实心），不与主操作同级。

PageHeader 本轮只做无说明时的垂直对齐，没有改成营销 Header，也没有加图标或渐变。

---

## 5. StatusTag 使用情况

`StatusTag.vue` 本身未改。Batch B 已包含本轮所需映射。

| 场景 | kind | 结果 |
| --- | --- | --- |
| 人员状态 | `employee` | 在职 / 停用 / 离职 |
| 系统账号状态 | `account` | 启用 / 停用 / 锁定 |
| 系统账号角色 | 不适合直接替换行内 Select | 使用与 StatusTag 相同的中文映射 |

角色没有做成 Success / Warning / Error，也没有使用 IBM Blue 作为角色主色。

---

## 6. Table 如何映射 IBM 规则

IBM-DESIGN.md Known Gaps 已写明：营销提取没有完整 Data Table 产品组件规范。

因此：

```text
保留 Element Plus Table 结构
+
套用 IBM 已存在的 Colors / Typography / Spacing / Hairline / Surface / Flat geometry
```

运行时测量（ADMIN /employees）：

| 部位 | 运行时值 | IBM 来源 |
| --- | --- | --- |
| 内容容器背景 | `rgb(255, 255, 255)` | `colors.canvas` |
| 容器边框 | `1px #e0e0e0`（设备上显示约 0.8px） | `colors.hairline` |
| 圆角 | `0px` | `rounded.none` |
| 阴影 | `none` | Elevation：hairline + surface change |
| 表头背景 | `rgb(244, 244, 244)` | `colors.surface-1` |
| 表头文字 | `rgb(82, 82, 82)` / 14px / 600 | `ink-muted` + `body-emphasis` |
| 单元格 | 14px | `body-sm` |
| Hover | Surface 1 | surface lift |
| 空状态 | `暂无数据` | 保留 Element Plus 空状态，只统一中文 |

未自行规定新的行高，未做圆角表格、彩色/渐变表头、卡片式一行一条、蓝色表头。

---

## 7. Dialog 如何处理

IBM 原始文件没有完整后台 Modal 规范。

因此保留 Element Plus Dialog / MessageBox 结构，只映射已有规则。

运行时测量（新建人员 Dialog）：

| 部位 | 运行时值 | IBM 来源 |
| --- | --- | --- |
| 背景 | `rgb(255, 255, 255)` | Canvas |
| 边框 | `1px #e0e0e0` | Hairline |
| 圆角 | `0px` | `rounded.none` |
| 阴影 | `none` | 不用 drop shadow |
| 标题 | `#161616` / 20px / 400 | Ink + `subhead` |
| Input | Surface 1 / `11px 16px` / `0px` | 已校准 `text-input` |

未改 Dialog 字段、校验、确认逻辑，未替换组件库，未做彩色标题栏、大圆角、玻璃背景。

---

## 8. IBM-DESIGN.md 未覆盖的场景

1. 后台 Data Table 产品组件（行高、选中列、排序、分页、批量操作）
2. 后台 Modal / Dialog 组件
3. MessageBox / 确认框
4. Select / 下拉框独立规范
5. 列表页 Toolbar / Filter 组件
6. 表格行内 Overflow Menu
7. 角色在「展示标签」与「即时改角色 Select」并存时的组件选择

---

## 9. 未覆盖场景如何处理

按最高级规则：**IBM 没有明确规则 → 保持当前稳定结构，不创造第三套设计体系。**

- Table：保留 Element Plus，只套用 Canvas / Surface 1 / Hairline / Ink / 14px。
- Dialog：保留 Element Plus，只套用 Canvas / Ink / Hairline / 0 radius / 已有 Button 与 Input。
- Select：保留当前行为和 40px 高度，不 invent 新下拉规范。
- 系统账号无真实筛选：不补假筛选。
- 行内操作：保留文字按钮，不改成 Overflow Menu。
- 角色列：行内 Select 是真实「修改角色」入口，不能用 StatusTag 替换；使用与 StatusTag 相同的中文映射。

---

## 10. 是否修改业务逻辑

否。

未修改：

- backend / database / API
- Axios
- Router 定义、守卫与业务语义
- Pinia Store
- 权限、`v-if` 菜单、role code
- 登录逻辑、`must_change_password`
- 人员字段含义、人员状态 code
- 系统账号字段、账号状态 code、角色枚举
- 表单校验业务规则

未新增：

- 项目管理、资源账号、资源管理、费用管理、费用统计、系统设置、角色权限配置

---

## 11. npm run build 结果

命令：

```text
npm run build
```

结果：PASS。

- `vue-tsc -b` 通过
- Vite 生产构建通过
- 1708 modules transformed
- 构建耗时约 4.07s
- IDE 对本轮 Vue / CSS 文件未报告 lint error

非阻塞警告（原有问题，本批未扩大处理）：

- 主 JS chunk 约 1,114.25kB（gzip 约 369.19kB），超过 Vite 500kB 阈值
- npm 报告本机未知 `devdir` 配置

---

## 12. /employees 回归结果

在当前 Docker 服务（frontend / backend / PostgreSQL 均运行）中，用真实 `admin` 账号走浏览器：

| 项 | 结果 |
| --- | --- |
| 人员列表可加载 | PASS。真实人员行可显示，状态为「在职 / 停用」而非 `ACTIVE` |
| 搜索可用 | PASS。关键字 `ADMIN001` 查询后只剩 1 行 |
| 创建人员 Dialog 可打开 | PASS。标题「新建人员」，工号/姓名/部门/岗位/邮箱/手机/备注均在；未提交 |
| 编辑 Dialog 可打开 | PASS。标题「编辑人员」，工号只读且预填 `ADMIN001`；未保存 |
| 停用流程仍存在 | PASS。出现「确认停用人员 系统管理员？」；已取消，未停用开发账号 |
| PageHeader | PASS。「人员管理」+ 唯一 Primary「新建人员」 |
| Toolbar | PASS。搜索框 + 查询，无 Card / 阴影包裹 |

---

## 13. /users 回归结果

| 项 | 结果 |
| --- | --- |
| 系统账号可加载 | PASS |
| 创建账号 Dialog 可打开 | PASS。标题「创建系统账号」；用户名 / 初始密码 / 角色 / 绑定人员均在；未创建 |
| 角色修改入口正常 | PASS。行内 Select 仍在；选项为管理员 / 老板 / 负责人 / 成员；未改真实角色 |
| 重置密码入口正常 | PASS。Dialog 标题「重置密码」，含新密码；未提交 |
| 启停入口正常 | PASS。停用出现「确认停用账号 u_83e0dfcb？」；已取消。启用入口仍在，未点击以免直接改数据 |
| 标题语义 | PASS。页面是「系统账号」，不是「账号管理」 |
| 假筛选 | PASS。未增加搜索/角色/状态假筛选 |

---

## 14. 四类角色权限回归结果

未改 `AdminLayout.vue`、`router/index.ts`、`auth` store 的 `v-if` / Guard / getter。浏览器实测：

| 角色 | 菜单 | 直接访问 |
| --- | --- | --- |
| ADMIN | 首页、人员管理、系统账号 | `/employees`、`/users` 均可进入 |
| BOSS | 首页、人员管理；无系统账号 | `/employees` 可进入且无写操作；`/users` 被守卫重定向到 `/` |
| PROJECT_MANAGER | 仅首页 | `/employees`、`/users` 均重定向到 `/` |
| MEMBER | 仅首页 | `/employees`、`/users` 均重定向到 `/` |

---

## 15. 剩余问题

- IBM-DESIGN.md 仍无完整 Data Table / Modal / Select 规范，本轮只做 token 映射，没有补一套后台表格设计系统。
- 列表页背景是 Surface 1，IBM `text-input` 也是 Surface 1，搜索框主要靠底边线识别。这与已校准 Input 一致，未另造白底输入框。
- 系统账号角色仍是行内 Select，而不是 StatusTag；这是为了保留真实改角色入口。
- 开发库中已有大量历史测试人员/账号数据，本轮未清理，也未再写入新数据。
- 主 JS chunk 超 500kB、npm `devdir` 警告仍在，与本轮无关。

---

## 16. 下一步建议

等待下一轮明确指令后再执行。不要提前进入：

```text
项目管理
资源账号
资源管理
费用管理
费用统计
费用类型
系统设置
角色权限页面
```

若后续真实 API / 路由完成，再按 `IBM-DESIGN.md` + `PROJECT-UI-CONSTRAINTS.md` 做下一批页面统一。若列表页模式在更多真实页面重复出现，再判断是否值得抽象，而不是本轮做通用 CRUD。

本轮到此停止。

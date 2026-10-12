# 企业项目资源与费用管理系统 — 设计基线

**设计语言：** IBM Carbon Enterprise Light  
**组件策略：** 继续使用 Element Plus，用 Design Token + 全局 CSS 覆盖实现 Carbon 风格。禁止引入 `@carbon/react`、Ant Design 或其他第二套大型 UI 框架。  
**优先级：** 业务清晰 > 操作效率 > 信息密度 > 统一性 > 视觉效果 > 动画  

本文件是后续所有前端开发的强制规范。新增或修改页面、表格、表单、弹窗、标签前，必须先读本文件。禁止各页面自行定义颜色、圆角、阴影、间距、按钮、表格或状态色。

参考来源（只作设计语言参考，不是业务依赖）：

- `design-reference/awesome-design-md/README.md`（索引：IBM / Carbon / Enterprise technology / Structured blue palette）
- `design-reference/awesome-design-md/design-md/ibm/DESIGN.md`（颜色、字体、间距、按钮、输入、导航等具体定义）

该仓库禁止作为 npm 依赖、禁止改业务去适配它、禁止把其代码打进正式前端产物。

---

## 1. 我们要什么，不要什么

要的是 **Carbon Light 企业后台**，不是 IBM 官网复制版。

| 采用 | 禁止 |
| --- | --- |
| 浅灰页面 + 白色内容区 | 大面积黑色、Gray-100 全站暗色 |
| IBM Blue `#0F62FE` 作为唯一品牌强调色 | 营销 Hero、品牌 Banner、全宽 CTA 条 |
| 紧凑、高密度 Table | 巨大标题、巨大 Card、卡片列表化 |
| 小圆角、弱阴影或无阴影 | 玻璃拟态、大阴影、大圆角、炫酷大屏 |
| 4px 网格、结构化排版 | 卡片套卡片、每个字段一张 Card |
| 企业蓝、专业、克制 | AI 官网 / SaaS 营销 / Crypto Dashboard 风格 |

`awesome-design-md` 中的 IBM 文件主要提取自 ibm.com **营销站**（76px 轻字重标题、CTA Banner、深色 Footer）。本系统是内部管理后台，因此：

- 不使用 Display 42–76px 标题
- 不使用全宽蓝色 CTA Banner
- 不把 Footer 做成深色营销页脚
- 侧栏与 Header 保持 Light，不复制官网深色页脚作为主壳层
- 圆角采用 2–4px（适配 Element Plus 与密集表单），而不是营销站强制 0px 直角

---

## 2. 真实业务边界（UI 必须服从现状）

当前仓库已交付 Gate 0 骨架 + Gate 1 身份体系。UI 只能按**已有业务**画菜单与页面，不得为了设计稿虚构模块。

### 2.1 已实现（必须有对应界面）

| 模块 | 说明 | 当前路由 |
| --- | --- | --- |
| 登录 | 系统账号登录，无公开注册 | `/login` |
| 修改密码 | 含首次强制改密 | `/change-password` |
| 首页 | 当前用户、角色、Scope、系统健康 | `/` |
| 人员管理 | Employee 档案，与登录账号分离 | `/employees` |
| 系统账号 | 创建账号、角色、重置密码、启停 | `/users` |

系统登录角色（后端枚举，不可改名）：

| code | 中文 | 数据范围 | 当前前端能力 |
| --- | --- | --- | --- |
| `ADMIN` | 管理员 | `GLOBAL` | 人员读写、账号管理 |
| `BOSS` | 老板 | `GLOBAL` | 人员只读 |
| `PROJECT_MANAGER` | 负责人 | `MANAGED_PROJECTS` | Gate 1 无项目页，首页可见 |
| `MEMBER` | 成员 | `MEMBER_PROJECTS` | Gate 1 无项目页，首页可见 |

人员状态：`ACTIVE` / `INACTIVE` / `LEFT`  
账号状态：`ACTIVE` / `DISABLED` / `LOCKED`

### 2.2 尚未实现（禁止现在做菜单与页面）

项目、资源账号、资源分配、到期管理、费用记录、费用统计、费用类型、角色权限配置页、系统设置页均未交付。这些只在本文件中预留视觉规则，**等对应 API 与路由存在后再建页面**。

### 2.3 资源账号 ≠ 系统登录账号

将来资源账号（ChatGPT、Cursor、Claude、GitHub、服务器、API、SaaS 等）是被管理的资产，不是登录本系统的 User。UI 文案与导航必须分开，禁止混用「账号」一词而不加限定。

---

## 3. 颜色

页面主背景用 Carbon Gray 10，内容容器用白，文字用 Gray 100 / 70 / 50，边框用 Gray 20，主色只用 IBM Blue。

```css
:root {
  --color-primary: #0F62FE;
  --color-primary-hover: #0050E6;
  --color-primary-active: #0043CE;
  --color-primary-pressed: #002D9C;

  --color-bg-page: #F4F4F4;
  --color-bg-panel: #FFFFFF;
  --color-bg-subtle: #E0E0E0;
  --color-bg-hover: #E8E8E8;
  --color-bg-selected: #D0E2FF;

  --color-text-primary: #161616;
  --color-text-secondary: #525252;
  --color-text-muted: #8D8D8D;
  --color-text-on-primary: #FFFFFF;
  --color-text-placeholder: #A8A8A8;
  --color-text-disabled: #C6C6C6;

  --color-border: #E0E0E0;
  --color-border-strong: #8D8D8D;
  --color-focus: #0F62FE;

  --color-success: #198038;
  --color-success-bg: #DEFBE6;
  --color-warning: #F1C21B;
  --color-warning-bg: #FCF4D6;
  --color-danger: #DA1E28;
  --color-danger-bg: #FFF1F1;
  --color-info: #0F62FE;
  --color-info-bg: #D0E2FF;

  --color-link: #0F62FE;
  --color-link-hover: #0043CE;
}
```

Element Plus 映射（改造阶段写入 token，不另起一套色）：

```css
--el-color-primary: var(--color-primary);
--el-color-success: var(--color-success);
--el-color-warning: var(--color-warning);
--el-color-danger: var(--color-danger);
--el-text-color-primary: var(--color-text-primary);
--el-text-color-regular: var(--color-text-secondary);
--el-border-color: var(--color-border);
--el-bg-color-page: var(--color-bg-page);
--el-fill-color-blank: var(--color-bg-panel);
```

禁止再使用当前散落色值作为新规范：`#1f2a44`、`#409EFF`、`#f5f7fa`、`#eef2f6`、`#ebeef5`、`#606266`。

---

## 4. 字体与字号

优先 IBM Plex Sans（SIL OFL，可本地或字体服务加载）。回退：`"IBM Plex Sans", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif`。

金额、编号、工号可用 IBM Plex Mono 或系统等宽，但不要在标题上用等宽。

后台不使用营销级 Display 字号。

| 角色 | 字号 | 字重 | 行高 | 用途 |
| --- | --- | --- | --- | --- |
| Page title | 20px | 400 | 1.4 | 页头标题 |
| Section title | 16px | 600 | 1.4 | 区块标题 |
| Body | 14px | 400 | 1.29 | 默认正文、表格单元格 |
| Body emphasis | 14px | 600 | 1.29 | 强调、选中 Tab |
| Control | 14px | 400 | 1.29 | Button / Input / Select |
| Caption | 12px | 400 | 1.33 | 辅助说明、表头可降到 12–14px |
| Amount | 14px / 20px | 600 | 1.3 | 表格金额 14px；摘要金额 20px |

正文字距可保留 Carbon 的 `0.16px`。标题与导航使用句首大写 / 中文正常写法，禁止全大写英文追踪标题。

---

## 5. 间距、圆角、边框、阴影

4px 网格。

| Token | 值 | 用途 |
| --- | --- | --- |
| `--space-1` | 4px | 紧贴间距 |
| `--space-2` | 8px | 控件间隙、筛选条 gap |
| `--space-3` | 12px | 表单项内部 |
| `--space-4` | 16px | 模块内边距、模块 gap 下限 |
| `--space-5` | 24px | 页面 padding、模块 gap 上限 |
| `--space-6` | 32px | 大段分隔（少用） |

页面内容区内边距：`24px`。模块之间：`16px–24px`。禁止卡片之间 40–60px 留白。

| Token | 值 | 用途 |
| --- | --- | --- |
| `--radius-sm` | 2px | 默认控件、Tag |
| `--radius-md` | 4px | 面板、对话框 |
| `--radius-lg` | 6px | 极少使用，Dashboard 大图容器上限 |

禁止大圆角与胶囊主按钮。

边框：默认 `1px solid #E0E0E0`。聚焦：底边或 outline 使用 `#0F62FE`（Element Plus 焦点环可映射为此色，不必 1:1 复制 Carbon 底部双线，以免和现有输入框冲突）。

阴影：默认无。Modal / Dropdown / Drawer 使用弱阴影：

```css
--shadow-sm: 0 2px 6px rgba(0, 0, 0, 0.08);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.12);
```

禁止大投影、霓虹光、模糊玻璃。

---

## 6. App Layout

```text
+------------------+--------------------------------------+
| Sidebar 220–240  | Header 48–56                         |
| 白/浅灰          | 白底 + 底边框                         |
| 系统名           +--------------------------------------+
| 当前真实菜单     | Page Header                           |
|                  | Main #F4F4F4                          |
|                  |   白色内容面板                         |
+------------------+--------------------------------------+
```

- 侧栏宽度：`220px`（当前已是 220，保持；上限 240）
- Header 高度：`48px`（当前 Element Plus 默认约 60，需压到 48–56）
- 主区背景：`#F4F4F4`
- 内容面板：`#FFFFFF`，1px `#E0E0E0` 边框，圆角 4px，无大阴影
- 不使用深海军蓝 `#1f2a44` 作为侧栏底（那是通用后台模板，不是 Carbon Light）

---

## 7. Header

高度 48–56px。白底，底部分隔线 `#E0E0E0`。只放：

1. 系统名称（若侧栏已有品牌，Header 可不重复 Logo，可放当前页标题或留空）
2. 当前用户显示名
3. 角色中文名（管理员 / 老板 / 负责人 / 成员）
4. 修改密码
5. 退出

禁止：搜索大框、通知红点堆砌、皮肤切换、无业务的快捷入口。

退出为次要操作，用 Ghost / 文本按钮，不要做成巨大主色按钮。

---

## 8. Sidebar

- 宽度 220–240px
- 背景 `#FFFFFF` 或 `#F4F4F4`
- 文字 `#161616` / 次要 `#525252`
- 选中：浅蓝色背景 `#D0E2FF` 或左侧 3px `#0F62FE` 指示条 + 文字 `#0F62FE` 或 `#161616` 加粗
- Hover：`#E8E8E8`
- 菜单字号 14px，行高约 40–44px
- 品牌区高度与 Header 对齐（48–56px），文案：「项目费用中枢」或全称「企业项目资源与费用管理系统」（短名放侧栏）

### 当前真实菜单（必须按此实现，不得加空菜单）

```text
首页
人员管理      （ADMIN、BOSS 可见）
系统账号      （仅 ADMIN）
```

`PROJECT_MANAGER` / `MEMBER` 在项目模块上线前只看到首页（及改密）。这是现状，不要为「菜单好看」补假入口。

### 未来菜单（模块上线后再加，现在禁止创建）

```text
总览
项目管理
资源管理
    资源账号
    资源分配
    到期管理
费用管理
    费用记录
    费用统计
    费用类型
组织管理
    成员管理          ← 对应现有「人员管理」
    系统账号
系统
    角色权限
    系统设置
```

---

## 9. Page Header

每个业务页顶部统一：

| 元素 | 规格 |
| --- | --- |
| 标题 | 20px / 400 / `#161616` |
| 说明 | 可选，14px / `#525252` |
| 主操作 | 右侧 Primary Button（如「新建人员」） |
| 次操作 | Ghost / Default |

禁止用 `h1`/`h2` 22px+ 再套一层大 Card 当页头。首页不要写巨大「首页」装饰字。

---

## 10. Button

沿用 `el-button`，通过 token 改观感。高度：Primary / Default `40px`；表格内操作 `32px` 文本按钮。

| 类型 | 用法 | 视觉 |
| --- | --- | --- |
| Primary | 每页最多一个主操作：登录、保存、创建 | 底 `#0F62FE`，字白，hover `#0050E6` |
| Default | 查询、取消 | 白底，边框 `#E0E0E0`，字 `#161616` |
| Ghost / text | 表格行内操作 | 无边框，主操作蓝、破坏性红 |
| Danger | 停用、删除确认主按钮 | 底 `#DA1E28` |

圆角 2px。禁止胶囊按钮、渐变按钮、大阴影按钮。不要把「退出」做成 Primary。

---

## 11. Input / Select

高度 40px。白或 `#F4F4F4` 填充，边框 `#E0E0E0`，字 14px，placeholder `#A8A8A8`。

- 聚焦：边框或 focus ring `#0F62FE`
- 错误：边框 `#DA1E28`，下方 12px 错误文案
- 禁用：字 `#C6C6C6`，背景 `#F4F4F4`
- Select 与 Input 同高同宽策略；筛选条内宽度按字段（如搜索 240px）

---

## 12. Form

- 标签在上或左侧 80–100px，同一页面保持一种对齐
- 弹窗表单 label-width 统一 90px（当前人员/账号弹窗已接近此值，保留）
- 必填用红色 `*`，不要每个 label 另配颜色
- 提交按钮在弹窗 footer 右对齐：取消（Default）+ 主操作（Primary）
- 一列布局优先；宽表单最多两列，列间距 16px

---

## 13. Table（核心组件）

项目管理、资源、费用、人员、系统账号等列表**必须用 Table**，禁止一条记录一张大 Card。

| 部分 | 规格 |
| --- | --- |
| Header | 背景 `#F4F4F4`，字 12–14px / `#525252`，字重 600 |
| Row height | 44–48px |
| 边框 | 横向 1px `#E0E0E0`，避免重框网格 |
| Hover | `#E8E8E8` 或 `#F4F4F4` |
| 选中 | `#D0E2FF` |
| 操作列 | 右对齐或固定右侧，text 按钮，间距 8px |
| Loading | `v-loading`，禁止另做骨架屏动画秀 |
| Empty | 统一空状态文案，见第 18 节 |
| Pagination | 需要分页时放表格下方右对齐；当前列表若仍是全量数组，先不虚构分页 |

当前人员页、系统账号页已经是 Table，方向正确。需要改的是：去掉「整页一个装饰 Card」的包法（可改为白面板）、统一表头/行高/状态 Tag、补 Page Header 与筛选条。

---

## 14. Filter Bar

列表页表格上方一行工具条：

- 左：搜索、状态下拉等筛选，gap 8px
- 右：主操作按钮
- 背景与表格同面板，不要单独再套一张 Card
- Input 高 40px，Button 高 40px 对齐

---

## 15. Tag / StatusTag

全站状态必须走统一映射，禁止页面内联一套颜色。

建议实现：`src/components/StatusTag.vue`（改造阶段再落地，本轮只定规则）。

### 人员 `employment_status`

| 值 | 展示 | 色 |
| --- | --- | --- |
| `ACTIVE` | 在职 | success `#198038` |
| `INACTIVE` | 停用 | muted `#8D8D8D` |
| `LEFT` | 离职 | danger `#DA1E28` |

### 系统账号 `status`

| 值 | 展示 | 色 |
| --- | --- | --- |
| `ACTIVE` | 启用 | success |
| `DISABLED` | 停用 | muted |
| `LOCKED` | 锁定 | warning（字色用 `#161616` 以保证黄底可读） |

### 角色

角色用中性/信息 Tag 或纯文本，不用成功绿。展示中文：管理员、老板、负责人、成员。

### 未来资源状态（模块上线后沿用同一组件）

| 展示 | 色 |
| --- | --- |
| 使用中 | success |
| 未分配 | info / muted |
| 即将到期 | warning |
| 已到期 | danger |
| 已停用 | muted |

Tag：高 20–24px，圆角 2px，浅底 + 深字，不要高饱和实心大色块。

表格里禁止直接打印 `ACTIVE` 英文枚举。

---

## 16. Tabs

下划线式。默认字 `#525252`，选中 `#161616` + 底部 2px `#0F62FE`。高度约 40px。不要胶囊 Tabs 作为主导航。

---

## 17. Modal / Drawer

当前系统只用 `el-dialog`，没有 Drawer。规则：

| | Modal | Drawer |
| --- | --- | --- |
| 何时 | 创建/编辑短表单（人员、账号、重置密码） | 未来详情、多段信息、较长表单 |
| 宽度 | 420–520px（与现状一致） | 480–640px |
| 标题 | 16px / 600 | 同左 |
| 圆角 | 4px | 右侧 0 |
| 遮罩 | 半透明黑 40% 左右 | 同左 |
| Footer | 取消 + 主按钮右对齐 | 同左 |

不要全屏炫酷弹层。确认停用继续用 `ElMessageBox`，样式跟随后续 token。

---

## 18. Pagination / Empty / Loading

- Pagination：14px，当前页用 Primary；每页条数可选 20/50
- Empty：表格内「暂无数据」+ 一句操作提示（如「点击右上角新建人员」）。不要插画风空状态
- Loading：Element Plus 的 `v-loading` / 按钮 loading。全页 Loading 仅用于登录跳转等短过程

---

## 19. 登录页

不是官网 Hero。

- 背景 `#F4F4F4`
- 居中白色面板，宽约 400–420px，1px 边框，弱阴影可选
- 标题 20px：「企业项目资源与费用管理系统」
- 说明 14px 次要色：「请使用系统账号登录。本系统不提供公开注册。」
- 用户名、密码、主按钮全宽 Primary
- 无装饰插画、无渐变、无大 Logo 动画

修改密码页：同一面板语言，可放在壳层外（现状如此），视觉与登录对齐。

---

## 20. Dashboard / 首页

当前首页只应展示**真实已有信息**：用户、角色、Scope、账号状态、后端/数据库健康。不要编造项目数、费用总额等假指标。

允许的 Card 场景（少而准）：

- 少量统计（等项目/费用 API 存在后）
- 费用摘要
- 重要提醒（即将到期资源）
- 图表

禁止 Card 套 Card、把 Descriptions 再包进多层阴影卡片。首页用 Page Header + 白色面板 + `el-descriptions` 或定义列表即可。

---

## 21. 费用与金额

统一格式：

```text
¥ 1,280.00
```

规则：

- 货币符号 `¥` + 空格 + 千分位 + 两位小数
- 禁止混用：`1280 元`、`￥1280`、`1280 RMB`、`$1280`
- 负数：`-¥ 1,280.00`，颜色 `--color-danger`
- 零：`¥ 0.00`
- 表格内右对齐、等宽数字
- 费用类型文案（上线后统一，不预先做页面）：订阅费用、一次性费用、API 按量费用、服务器费用、软件采购、其他费用

建议改造阶段增加 `src/utils/formatMoney.ts`，所有金额只走这一处。

---

## 22. 数据可视化（预留）

等费用统计存在后再用。原则：白底、细线、IBM Blue 作为主序列，第二序列用 `#525252` 或 `#8D8D8D`，告警用红/黄。不要彩虹柱、3D、渐变面积图。

---

## 23. 工程落点（改造阶段，本轮不改代码）

当前没有 Design Token 文件，也没有第二套 token。应新建一处并作为唯一来源：

```text
frontend/src/styles/tokens.css
```

在 `frontend/src/main.ts` 中于 Element Plus 样式之后导入，覆盖 `--el-*`。

公共组件目录 `frontend/src/components/` 目前为空，后续按需增加：

```text
StatusTag.vue
PageHeader.vue
（可选）MoneyText.vue
```

不要新建另一套组件库。

---

## 24. 开发强制规则

从本文件生效起：

1. 先读 `./DESIGN.md` 再写 UI
2. 颜色、圆角、阴影、间距、Button、Table、Tag 不得页面私自发明
3. 不存在的业务不创建菜单和假数据看板
4. 不替换 Element Plus，不安装 Carbon 官方组件包
5. 不把 `design-reference/awesome-design-md` 当运行时依赖

相关计划与现状审计：

- `docs/ui-refactor/UI-CURRENT-STATE-AUDIT.md`
- `docs/ui-refactor/UI-REFACTOR-PLAN.md`

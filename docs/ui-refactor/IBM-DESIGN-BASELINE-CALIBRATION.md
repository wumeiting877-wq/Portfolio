# IBM Design Baseline Calibration

日期：2026-09-22  
范围：设计来源校准、P0 / Batch A 对照与必要的最小样式调整。  
结论：已完成；未进入 Batch B，未修改业务逻辑。

## 1. IBM 原始文件来源

唯一视觉设计来源：

```text
design-reference/awesome-design-md/design-md/ibm/DESIGN.md
```

该文件已完整读取，并原样复制到：

```text
./IBM-DESIGN.md
```

复制后对源文件与目标文件执行 SHA-256 校验，两者均为：

```text
435881F55AC62CD0ADBF9B1F27E78DA42D7E6D5B8A4E742626C19A50FF558E3B
```

因此 `IBM-DESIGN.md` 未被重新解释、总结、改写或混入项目业务规则。

## 2. 已创建文件

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
docs/ui-refactor/IBM-DESIGN-BASELINE-CALIBRATION.md
```

- `IBM-DESIGN.md`：IBM 原始视觉规范的逐字节副本，是本项目唯一视觉 Source of Truth。
- `PROJECT-UI-CONSTRAINTS.md`：只保存技术栈、业务保护、真实路由、角色权限、账号概念和实施顺序。

## 3. 旧 DESIGN.md 的处理

根目录原 `DESIGN.md` 已改名为：

```text
DESIGN-PROJECT-ADAPTATION-ARCHIVE.md
```

该文件仅作历史参考，不再作为 UI 视觉设计基线。没有删除其内容。

## 4. Batch A 与 IBM 对照表

“Batch A 当前值”指本次校准开始时 `P0-BATCH-A-IMPLEMENTATION-REPORT.md` 与真实代码中的值。IBM 列只引用 `IBM-DESIGN.md` 的真实 token、组件或正文定义。

| 项目 | Batch A 当前值 | IBM-DESIGN.md 真实定义 | 处理 |
| --- | --- | --- | --- |
| Primary | `#0f62fe` | `colors.primary: "#0f62fe"`；Brand & Accent 定义为唯一品牌强调色 | 保留 |
| Primary hover | `#0050e6` | `colors.blue-hover: "#0050e6"`；用于 primary button hover | 保留并明确映射到 Primary Button hover |
| Primary pressed | token 为 `#002d9c`，但 Element Plus active 映射到 `#0043ce` | `colors.blue-80: "#002d9c"`；`button-primary-pressed` 使用 Blue 80 | Element Plus active 改为 `#002d9c` |
| Text | Primary `#161616`、Secondary `#525252`、Muted `#8d8d8d` | `colors.ink: "#161616"`、`ink-muted: "#525252"`、`ink-subtle: "#8c8c8c"` | 前两项保留；Muted 调整为 `#8c8c8c` |
| Success | `#198038` | `colors.semantic-success: "#24a148"` | 调整为 `#24a148` |
| Warning / Error / Info | `#f1c21b` / `#da1e28` / `#0f62fe` | `semantic-warning` / `semantic-error` / `semantic-info` 为相同值 | 保留 |
| Surfaces | Page `#f4f4f4`、Panel `#ffffff`、Subtle `#e0e0e0` | `surface-1: "#f4f4f4"`、`canvas: "#ffffff"`、`surface-2: "#e0e0e0"` | 保留 |
| Typography | Body 14px；IBM Plex Sans 字体栈 | `typography.body` 为 16px / 400 / 1.50 / 0.16px；`body-sm` 与 `button` 为 14px；fallback 为 `Helvetica Neue, Arial, sans-serif` | Body 调整为 16px；按钮、Header、Navigation 保持 IBM 的 14px；字体 fallback 对齐 |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32px；Main padding 24px | 4px base grid；`xxs` 至 `xl` 为相同值；feature card padding 24px | 保留 |
| Border | 默认 `#e0e0e0`；Strong `#8d8d8d` | `hairline: "#e0e0e0"`；`hairline-strong: "#161616"`；层级使用 1px hairline | 默认保留；Strong 调整为 `#161616` |
| Radius | Element Plus 默认 2px；token 有 2 / 4 / 6px | `rounded.none: 0px` 是 button、card、input、container 默认；2 / 4 / 6px 作为存在但少用的 scale | 增加 0 token，Element Plus 默认与 small radius 调整为 0；2 / 4 / 6 token 保留为 IBM 已定义 scale |
| Shadow | token 自定义两级弱阴影；Batch A Layout 实际无阴影 | Elevation & Depth 明确 marketing 使用无阴影、hairline 与 surface change | 删除未使用的自定义 shadow token；现有无阴影 Layout 保留 |
| Header | 白色、52px、底部 1px 边线、无阴影 | `components.top-nav`：白色、48px、1px bottom hairline、`body-sm` | 高度调整为 48px；其余保留；Header 字体明确为 14px |
| Sidebar | 220px、白色、右侧 1px 边线 | IBM 文件未定义应用 Sidebar 宽度或专用 Sidebar 组件；只定义白色 Canvas 与 hairline | 保留，不创造新宽度 |
| Navigation | 菜单项 44px、14px；浅色 Sidebar | IBM `top-nav` 使用 `body-sm` 14px；未定义 Sidebar 行高 | 字号保留；44px 保留 |
| Active state | `#d0e2ff` 背景 + 3px Blue 左边线 | IBM 定义 selected product tab 为 2px Blue 底线，但未定义 Sidebar active state | 保留当前稳定 Sidebar active state，不套用不同组件规则 |
| Hover state | Sidebar `#e8e8e8` | IBM 定义 primary button hover `#0050e6`、surface lift `#f4f4f4`，未定义 Sidebar hover | Sidebar hover 保留；Primary Button hover 对齐 IBM |
| Button | 40px、2px radius；Primary 使用 IBM Blue；Default 白底描边 | `button` 为 14px / 400；所有按钮 padding 12px 16px、0px radius；secondary 为 Charcoal 实心；primary pressed 为 Blue 80 | 默认按钮样式、padding、圆角、Primary hover/pressed 与 focus 按 IBM 调整 |
| Input | 40px、2px radius、默认 Element Plus 白底边框 | `text-input` 为 Surface 1、16px body、11px 16px padding、0px radius；focus 为 2px IBM Blue 底线；error 为 2px Error 底线 | 按 IBM 调整默认、focus 与 error 外观 |
| Select | 40px | IBM 原始文件没有独立 Select 组件或明确高度定义 | 保留 40px，不自行创建规则；全局默认圆角随 IBM 变为 0 |
| Layout | Sidebar 220px；Main `#f4f4f4`、padding 24px | IBM 定义 Canvas / Surface、4px spacing grid，但没有后台两栏宽度定义 | 保留 |
| Focus state | 主要依赖 Element Plus 默认 focus | Elevation Level 3 定义 2px Primary outline；Input 明确 2px Primary underline | Button 增加 2px focus-visible outline；Input 使用 2px Primary 底线 |

## 5. 修改了哪些文件

新增：

- `IBM-DESIGN.md`
- `PROJECT-UI-CONSTRAINTS.md`
- `docs/ui-refactor/IBM-DESIGN-BASELINE-CALIBRATION.md`

改名：

- `DESIGN.md` → `DESIGN-PROJECT-ADAPTATION-ARCHIVE.md`

样式校准：

- `frontend/src/styles/tokens.css`
- `frontend/src/style.css`
- `frontend/src/layouts/AdminLayout.vue`

已审计但无需修改：

- `frontend/src/main.ts`：当前加载顺序已经是 Element Plus CSS → `tokens.css` → `style.css`，符合实现层覆盖要求。

## 6. 保留的 Batch A 内容

- IBM Blue 主色及已有 Hover / Pressed token。
- Canvas、Surface 1、Surface 2、Ink、Ink Muted、Hairline 和 Error / Warning / Info 色。
- 4px spacing grid 与 Main 24px padding。
- 220px Sidebar。
- 白色 Sidebar、白色 Header、1px 分隔线与无阴影 Layout。
- 44px Sidebar 菜单项。
- Sidebar 的 `#e8e8e8` Hover 和 `#d0e2ff` Active 背景；IBM 原始文件没有定义 Sidebar 对应值，因此不改。
- 真实菜单、路由跳转、角色显示、权限判断和退出流程。
- `tokens.css`、`style.css` 的加载顺序。

## 7. 因不符合 IBM 而调整的内容

- 默认圆角从 2px 改为 0px；2 / 4 / 6px 仅保留为 IBM 已记录的非默认 scale。
- Header 与品牌区从 52px 改为 IBM `top-nav` 的 48px。
- Body 从 14px 改为 IBM `body` 的 16px；Button、Header、Navigation 使用 IBM 14px 类型。
- Input 改为 Surface 1、0px 圆角、11px 16px padding、16px 字体，以及 Blue / Error 底线状态。
- Button 改为 12px 16px padding、0px 圆角；Default 对齐 IBM Secondary；Primary hover / pressed 对齐 IBM 值。
- Ink Subtle 从 `#8d8d8d` 改为 `#8c8c8c`。
- Success 从 `#198038` 改为 `#24a148`。
- Hairline Strong 从 `#8d8d8d` 改为 `#161616`。
- 删除没有 IBM 对应定义且未使用的自定义两级 shadow token。

## 8. Build 结果

执行：

```text
npm run build
```

结果：PASS。

- `vue-tsc -b` 通过。
- Vite 生产构建通过。
- 1705 modules transformed。
- 最终构建耗时约 6.44s。
- IDE 对本次修改的 CSS / Vue 文件未报告 lint error。

非阻塞警告：

- 主 JS chunk 仍超过 Vite 默认 500kB 阈值（约 1,114.34kB，gzip 约 369.22kB）。
- npm 仍报告本机未知 `devdir` 配置。
- 两项均为已有工程问题，本轮未扩大范围处理。

## 9. 是否修改业务逻辑

否。

未修改：

- `backend/`
- database
- API
- Axios
- Router 定义、守卫与业务语义
- Pinia Store 与业务结构
- 登录、强制改密与退出逻辑
- 权限、角色 code
- 人员字段、系统账号字段
- 任何业务 View

没有创建 Batch B 的 `PageHeader.vue`、`StatusTag.vue`，也没有修改 `LoginView.vue`、`ChangePasswordView.vue`、`HomeView.vue`。

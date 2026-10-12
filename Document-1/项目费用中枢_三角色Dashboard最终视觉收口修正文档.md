# 三角色 Dashboard 最终视觉收口修正文档
## BOSS / PROJECT_MANAGER / MEMBER

你现在正在操作【项目费用中枢】真实项目。

当前三角色 Dashboard 已完成两轮重构：

- BOSS：经营总览
- PROJECT_MANAGER：项目看板
- MEMBER：我的工作台

当前功能、权限、数据范围、币种显示和主要信息架构已经确认正确。

上一轮已完成：

- BOSS：趋势 / 状态双列
- BOSS：项目成本 / 费用结构双列
- BOSS：“需要关注”三区布局
- PM：三层双列
- PM：项目、成员链接统一
- MEMBER：项目优先
- MEMBER：资源状态 / 资源类型费用并列
- MEMBER：0 值弱化
- MEMBER：趋势压缩
- MEMBER：空态压缩
- Carbon Tab
- IBM Blue 文本链接
- 表格密度收口
- 图表高度收口

验证已通过：

- `npm run build`
- `vue-tsc -b`
- BOSS / PM / MEMBER 真实账号回归
- PM Project A 筛选联动
- 979px 单列降级
- 无横向溢出
- Console error = 0

---

# 一、本轮目标

本轮不是第三次重新设计 Dashboard。

本轮只做：

> 最终宽度、横向空间利用率、Alignment 和视觉一致性收口。

当前在 1440px 桌面视口下：

- 左侧 Sidebar 正常
- Dashboard 主内容已经收紧
- 但是主内容区域整体偏窄
- 页面右侧存在较大空白
- BOSS / PM / MEMBER 都没有充分利用桌面横向空间

本轮目标：

> 让 Dashboard 在 1440px 等主流桌面分辨率下充分利用主内容区域，同时保持 IBM 企业管理系统的紧凑感。

---

# 二、最高级规则

任何修改前必须首先读取：

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
docs/ROLE-DASHBOARD-DESIGN-INPUT.md
docs/ROLE-DASHBOARD-IBM-REDESIGN-IMPLEMENTATION-REPORT.md
docs/ROLE-DASHBOARD-VISUAL-FIX-REPORT.md
```

真实文件名如带后缀，以实际文件为准。

然后先输出：

```text
IBM-DESIGN.md READ CONFIRMED
FINAL DASHBOARD POLISH SCOPE CONFIRMED
```

## UI Source of Truth

任何新增或修改前端页面：

> 必须以 `IBM-DESIGN.md` 作为 UI Source of Truth。

禁止因为当前截图效果不满意而绕过 IBM 规范。

---

# 三、本轮严禁修改

禁止：

- 修改后端
- 修改数据库
- 修改 API
- 修改 Scope
- 修改 Permission
- 修改 RoleCode
- 修改 JWT
- 修改路由业务语义
- 修改统计口径
- 修改费用计算
- 修改资源状态规则
- 修改项目成员关系
- 修改币种 Raw Value
- 新增 Dashboard 指标
- 删除现有 Dashboard 核心区块
- 重新调整三角色信息架构
- 新增预算
- 新增审批
- 新增风险评分
- 新增 AI 洞察
- 新增同比 / 环比
- 新增项目健康度
- 重构 ADMIN Dashboard

特别注意：

> BOSS / PM / MEMBER 当前模块顺序原则上冻结。

本轮不要再次自由发挥。

---

# 四、当前三角色结构冻结

## BOSS

```text
经营总览
日期筛选
5 KPI
费用趋势              | 资源状态
项目成本              | 费用结构
需要关注
```

## PROJECT_MANAGER

```text
项目看板
日期筛选 + 我的负责项目
5 KPI
我的项目费用趋势      | 资源状态
项目费用              | 资源类型费用
项目成员费用          | 项目公共费用
资源关注
```

## MEMBER

```text
我的工作台
日期筛选
4 KPI
我的项目
我的资源状态          | 我的资源类型费用
我的费用趋势
即将到期资源
```

以上顺序冻结，不得重新排序。


---

# 五、P1：解决主内容区域过窄问题

当前 1440px 实际截图中，Dashboard 主内容只使用了页面中间偏左区域，右侧存在明显大面积空白。

本轮首先检查：

```text
AdminLayout.vue
HomeView.vue
Dashboard shell
main content wrapper
page container
content max-width
width
margin
padding
grid container
```

重点排查是否存在类似：

```css
max-width: 960px;
max-width: 1000px;
max-width: 1100px;
```

或固定 width 导致 Dashboard 无法充分使用可用空间。

## 主内容宽度目标

不要简单写死 `width: 100vw`。

必须基于现有 Layout 正确计算 Sidebar 后的主内容宽度。

目标：

```text
左侧 Sidebar
+
主内容区域充分展开
+
右侧保留正常页面 padding
```

推荐方向：

```css
width: 100%;
max-width: none;
```

或者：

```css
width: 100%;
max-width: 1280px;
```

但最终不能盲目照抄，必须结合 Sidebar width、Main padding、IBM-DESIGN.md 与当前 Layout 计算实际合理值。

## 禁止走向另一个极端

解决右侧空白时，不要把页面撑得过满。

禁止：

- 模块贴住浏览器最右边
- 表格无限拉长
- 标题与内容跨度过大
- KPI 宽到信息分散

最终目标：

> 横向充分利用，但仍保持 IBM 企业应用的阅读宽度与节奏。

---

# 六、BOSS 最终调整

BOSS 当前结构已经通过，本轮仅处理宽度与对齐。

## 6.1 页面宽度

让：

```text
费用趋势 + 资源状态
```

充分使用主内容宽度。

建议继续保持约 `2 : 1`，但不要写死像素。使用 Grid 或现有 Layout Grid。

## 6.2 项目成本 + 费用结构

继续双列，建议接近 `1 : 1`。

扩大后：

- 项目名称有更多空间
- 金额列保持紧凑
- 费用结构 Tab 不被拉散

## 6.3 需要关注

保持当前三区结构：

```text
即将到期
尚未分配
闲置
```

三块均匀使用宽度，不要重新做卡片。

## 6.4 单月趋势

当前只有一个月数据时图表只有单点，这是数据事实，不是 UI Bug。

禁止：

- 伪造月份
- 填充假数据
- 创建虚拟趋势

只保证图表在扩大宽度后不异常拉伸，Legend、单点、X Axis 正常。


---

# 七、PROJECT_MANAGER 最终调整

## 7.1 工具区 Alignment

日期筛选与“我的负责项目”必须处于同一个工具区：

```text
[本月][近3个月][近6个月][今年][自定义]        [我的负责项目 ▼]
```

要求：

- 垂直居中
- 同一基线
- 左右自然分布
- 不要项目下拉单独漂在右上方
- 不要额外增加一整行高度

优先检查现有布局组件，不要直接新造一套。

## 7.2 第一层

继续：

```text
我的项目费用趋势     | 资源状态
```

扩大主内容后继续维持约 `2 : 1`。

## 7.3 第二层

继续：

```text
项目费用             | 资源类型费用
```

建议 `1 : 1`，两个模块顶部、底部、表头和行高尽量对齐。

## 7.4 第三层

继续：

```text
项目成员费用         | 项目公共费用
```

建议 `1 : 1`，不要改变现有数据含义。

## 7.5 资源关注必须确认存在

如果当前无异常：

```text
资源关注
当前暂无即将到期、闲置或未分配资源。
```

要求：

- 一行或紧凑两行
- 约 40～56px 高度
- 不使用大型 Empty Illustration
- 不占大块空白

不要因为无数据直接删除整个模块。

---

# 八、MEMBER 最终调整

MEMBER 当前信息架构已经正确，本轮只做宽度利用率。

## 8.1 KPI

4 个 KPI 保持均分。

不要：

- 单卡过宽导致文字漂散
- 放大数字
- 增加说明文字

## 8.2 我的项目

扩大宽度以后，不要让“项目名称 / 状态”跨度过大到影响扫读。

允许为状态列设置合理宽度。

## 8.3 我的资源状态 + 我的资源类型费用

保持 `1 : 1` 或根据真实内容略微微调，禁止再改为上下排列。

## 8.4 我的费用趋势

保持 `200px` 高度。

不要因为页面变宽重新增加图表高度。

## 8.5 即将到期资源

无数据时保持紧凑 Empty State，不要因为主区域变宽重新出现大面积空白。

---

# 九、统一最大内容宽度策略

BOSS / PROJECT_MANAGER / MEMBER 必须使用同一套页面宽度规则。

禁止：

```text
BOSS max-width 1200
PM max-width 1050
MEMBER max-width 980
```

应统一 Dashboard Page Container 或统一 Dashboard CSS token。

三角色必须做到：

```text
PageHeader 左边界
日期筛选左边界
KPI 左边界
主体 Grid 左边界
底部模块左边界
```

全部一致，右边界同样一致。

---

# 十、统一 Section Gap 与 Panel

间距必须来自 `IBM-DESIGN.md`，坚持 4px spacing grid。

不要单独写随机间距：

```text
17px
22px
26px
```

Panel 保持：

- 白色 / 浅灰 Surface
- 1px Border
- 0 Border Radius
- 无 Shadow
- 无 Gradient

---

# 十一、链接、Tab、金额对齐保持上一轮结果

## 链接

继续保持：

```text
Normal → IBM Blue
Hover → underline
Focus → IBM focus
```

不要改回 Button / Badge / 小方框。

## Tab

BOSS 的：

```text
按资源类型
按计费方式
```

上一轮 Carbon Tab 已完成，本轮不要再改，仅检查扩大宽度后不被拉伸。

## 金额

金额保持右对齐，必要时给金额列合理宽度，避免因容器变宽导致金额与主体内容距离过远。

---

# 十二、响应式要求

桌面重点：

```text
1440 × 1000
```

同时验证：

```text
>= 1280px：双列
980～1279px：适度调整 Grid 比例
< 980px：允许双列 → 单列
```

上一轮 `979px` 已通过，本轮修改宽度后必须重新验证。

---

# 十三、绝对禁止横向滚动

至少检查：

```text
1440
1280
1024
979
```

要求：

```js
document.documentElement.scrollWidth <= window.innerWidth
```

---

# 十四、Sidebar 与 TopBar

本轮不要调整 Sidebar：

- 宽度
- 菜单
- 选中状态
- 权限范围

不要为了扩大 Dashboard 缩小 Sidebar。

TopBar 保持：

```text
角色名
修改密码
退出
Breadcrumb
```

除非公共 Main Container 宽度规则影响 Header 对齐，只允许做必要 alignment 修正。

---

# 十五、实施 Gate

## Gate 0 — 规范确认

读取：

```text
IBM-DESIGN.md
PROJECT-UI-CONSTRAINTS.md
```

输出：

```text
GATE 0 PASS
```

## Gate 1 — 宽度根因审计

检查：

```text
AdminLayout
HomeView
Dashboard Shell
Page Container
CSS
max-width
width
margin
padding
grid
```

必须先明确：

```text
ROOT CAUSE:
xxx

CURRENT:
xxx

TARGET:
xxx
```

不要直接试错修改。

## Gate 2 — 公共 Page Container 修正

优先统一 Dashboard 主内容宽度。

不要分别给三个 Shell 打补丁。

如果问题来自公共容器，只修改公共容器。

## Gate 3 — BOSS 对齐

检查：

- KPI
- 2:1
- 1:1
- 三区关注
- 左右边界

## Gate 4 — PM 对齐

检查：

- Filter Bar
- 2:1
- 1:1
- 1:1
- Resource Attention

## Gate 5 — MEMBER 对齐

检查：

- KPI
- 我的项目
- 1:1 中间区
- 200px 趋势
- Empty State

## Gate 6 — Responsive Regression

检查：

```text
1440
1280
1024
979
```

---

# 十六、验收重点

## BOSS

- [ ] Dashboard 横向空间明显改善
- [ ] 右侧不再存在异常大空白
- [ ] 趋势 + 状态比例协调
- [ ] 项目成本 + 费用结构宽度协调
- [ ] 关注三区利用完整宽度
- [ ] 结构没有变化

## PM

- [ ] 页面宽度与 BOSS 一致
- [ ] 日期筛选与项目筛选同一工具行
- [ ] 三层双列边界完全一致
- [ ] 资源关注 Empty State 存在
- [ ] 页面没有新增纵向空间
- [ ] Project A 筛选正常

## MEMBER

- [ ] 页面宽度与另外两个角色一致
- [ ] 4 KPI 平衡
- [ ] 我的项目没有异常拉伸
- [ ] 资源状态 / 类型费用双列自然
- [ ] 趋势仍为 200px
- [ ] 页面仍然明显比管理角色简单

---

# 十七、业务回归

重新真实登录：

```text
boss
pm
member
```

确认：

```text
BOSS = GLOBAL
PROJECT_MANAGER = MANAGED_PROJECTS
MEMBER = MEMBER_PROJECTS
```

不得因为 Layout 修改产生：

- 条件渲染错误
- 模块丢失
- Vue key 问题
- Route 错误
- API 重复调用
- Scope 变化

---

# 十八、技术验证

必须执行：

```text
npm run build
vue-tsc -b
```

并检查：

```text
Console error = 0
```

同时确认：

- 无新增 403
- 无新增 404
- 无新增 Vue warning
- 无 layout overflow

既有 warning 可以记录，不在本轮扩展处理。

---

# 十九、最终截图

生成：

```text
artifacts/dashboard-final-polish-2026-09-24/
```

保存：

```text
boss-dashboard-final.png
pm-dashboard-final.png
member-dashboard-final.png
```

全部使用：

```text
1440 × 1000
```

---

# 二十、最终报告

创建：

```text
docs/ROLE-DASHBOARD-FINAL-POLISH-REPORT.md
```

内容：

```text
1. 本轮范围
2. IBM-DESIGN 读取确认
3. 右侧空白根因
4. 修改文件
5. 公共宽度策略
6. BOSS 最终结果
7. PM 最终结果
8. MEMBER 最终结果
9. 1440 / 1280 / 1024 / 979 响应式验证
10. 权限与业务回归
11. Build / vue-tsc / Console
12. 最终截图索引
13. 剩余技术债
```

---

# 二十一、停止条件

完成：

```text
主内容宽度修正
横向空间利用率修正
PM 筛选器 Alignment
资源关注 Empty State 确认
三角色统一左右边界
响应式回归
```

以后立即停止。

不要进行：

- Dashboard 第三次信息架构调整
- 新增模块
- 删除模块
- ADMIN 重构
- 后端优化
- Chunk 拆分
- Element Plus warning 修复
- 新功能开发

等待最终人工验收。

---

# 最终原则

本轮的目标不是“再设计一次”。

而是：

> 保持已经正确的 BOSS / PM / MEMBER 信息架构完全稳定，仅解决 1440px 桌面环境下主内容区域偏窄、右侧空白过大和少量 Alignment 问题。

完成本轮后：

> BOSS / PROJECT_MANAGER / MEMBER Dashboard 应进入 UI FROZEN BASELINE 候选状态。

# Gate 6 IBM UI Review

日期：2026-09-22  
视觉 Source of Truth：`./IBM-DESIGN.md`  
业务边界：`./PROJECT-UI-CONSTRAINTS.md`

编码前已读取二者。未新建第二套 Design System。新页面使用既有 PageHeader、list-panel、product-tab、StatusTag、tokens.css。

## 新增页面

```text
/import-export   ImportExportView.vue
/notifications   NotificationsView.vue
/audit-logs      AuditLogsView.vue
/settings        SettingsView.vue
```

## 对照

| 规则 | 实现 |
| --- | --- |
| 画布 | `--color-bg-page` `#f4f4f4` |
| 面板 | 白底 + 1px hairline + `radius-none` |
| 主色 | IBM Blue `#0f62fe`（预检、生成导出、保存） |
| 次按钮 | 炭黑描边，非渐变 |
| 圆角 | 0（禁止 12/16/20） |
| 阴影 | 无大阴影；仅 Carbon 式 inset 底线 |
| 导入页 | 字段 + 文件 + 预检 + 错误表，无营销 Hero / 插画 |
| 状态 | StatusTag 方框 1px，notification tone 克制 |
| 表格 | 标准 list-panel + 分页 |

浏览器实测：导入页无大圆角、无玻璃拟态、无渐变卡片。设置页分区为方块面板。提醒标签「即将到期 / 未分配 / 未读」为方框色边。

## 菜单

新增「导入导出」「提醒中心」；「审计日志」「系统设置」仅 ADMIN / BOSS。

## 禁止项未出现

彩色营销导入、拖放云盘 Hero、大阴影上传区、圆角 16px 卡片、跨币种合计 KPI。

## 已知视觉债（非 Gate 6 回退）

IBM Plex Sans 仍为 CSS 字体栈声明（Gate 1 既有）。Element Plus `el-input-number` 的 +/- 在 BOSS 只读设置页仍出现在可访问树，但 spinbutton 为 disabled，且无保存按钮。

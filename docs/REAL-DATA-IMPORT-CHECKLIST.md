# 真实数据导入清单

版本：V1.0  
前置：Gate 6 Import Preview / Commit PASS。仅 ADMIN。

## 顺序

```text
1. 备份当前库
2. 按 DEV-DATA-CLEANUP-PLAN 决定是否清理开发验证数据
3. 导入人员
4. 导入项目
5. 导入项目成员
6. 导入资源类型（如需新类型）
7. 导入资源账号
8. 导入资源分配
9. 导入费用
10. 生成提醒
11. 抽查 Scope / 统计 / 多币种
```

系统登录账号仍在「系统账号」中创建，不通过 Excel 导入密码。

## 每类检查

### 人员

- [ ] employee_no 唯一
- [ ] email 格式
- [ ] employment_status ∈ ACTIVE / INACTIVE / LEFT
- [ ] 无 password 列

### 项目

- [ ] project_code 唯一
- [ ] 负责人工号存在且在职
- [ ] 日期 YYYY-MM-DD

### 项目成员

- [ ] 项目编码存在
- [ ] 工号存在
- [ ] 不违反 active membership

### 资源

- [ ] 资源类型 code 存在且启用
- [ ] 无 api_key / secret / token / password
- [ ] 到期日合法

### 资源分配

- [ ] 资源名存在
- [ ] 项目或成员至少一个
- [ ] 项目+成员时成员已在项目中

### 费用

- [ ] 费用类型存在
- [ ] amount 为数字，currency 独立列（CNY / USD）
- [ ] 分摊合计 == amount
- [ ] 禁止把「CNY 100」写进金额单元格
- [ ] VOIDED 不要导入；作废在系统内操作

## 操作

1. 下载模板：`GET /api/imports/templates/{type}`
2. 填写「数据」Sheet，不要用公式
3. 单文件 < 10 MB，< 10,000 行
4. Preview，处理错误列表（行号 + 字段）
5. 错误为 0 后再 Commit
6. Commit 失败则整批未写入，修正后重传同一文件

## 导入后抽查

- [ ] ADMIN 人员列表数量
- [ ] PM 只能看见自己的项目
- [ ] MEMBER 只能看见自己的资源 / 费用
- [ ] Dashboard 按币种分行，无混合总额
- [ ] 审计日志有 IMPORT_COMMIT
- [ ] 提醒中心生成到期 / 未分配

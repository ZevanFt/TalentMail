# 自动化功能文档

## 概览

TalentMail 提供三大自动化能力：

1. **规则引擎** — 基于条件自动执行邮件操作
2. **工作流系统** — 可视化拖拽流程编辑器
3. **Automation API** — 外部系统集成 (API Key 认证)
4. **临时邮箱** — 一次性邮箱地址

## 规则引擎

### 触发器

| 触发器 | 说明 |
|--------|------|
| `email_received` | 收到新邮件时 |
| `email_sent` | 发送邮件后 |

### 条件

支持组合条件 (AND/OR)：

| 条件类型 | 说明 | 示例 |
|---------|------|------|
| `from_contains` | 发件人包含 | `@github.com` |
| `to_contains` | 收件人包含 | `support@` |
| `subject_contains` | 主题包含 | `[Alert]` |
| `body_contains` | 正文包含 | `verification code` |
| `has_attachment` | 有附件 | `true` |

### 动作类型 (13种)

| 动作 | 说明 |
|------|------|
| `move_to_folder` | 移动到指定文件夹 |
| `add_tag` | 添加标签 |
| `remove_tag` | 移除标签 |
| `mark_read` | 标记已读 |
| `mark_starred` | 标星 |
| `archive` | 归档 |
| `delete` | 删除 |
| `forward` | 转发到指定地址 |
| `auto_reply` | 自动回复 |
| `send_notification` | 发送通知 |
| `webhook` | 调用外部 Webhook |
| `add_to_blocklist` | 加入黑名单 |
| `mark_spam` | 标记为垃圾邮件 |

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/automation/rules` | 列出用户规则 |
| `POST` | `/api/automation/rules` | 创建规则 |
| `PUT` | `/api/automation/rules/{id}` | 更新规则 |
| `DELETE` | `/api/automation/rules/{id}` | 删除规则 |
| `POST` | `/api/automation/rules/{id}/toggle` | 启用/禁用 |

## 工作流系统

### 架构

```
Vue Flow 编辑器 → JSON 图定义 → BFS 遍历执行引擎
```

### 41 种节点类型

分类包括：
- **触发节点**: 邮件接收、定时触发、Webhook 触发
- **邮件操作**: 发送、转发、回复、移动、标记
- **条件判断**: If/Else、Switch、包含检测
- **循环**: 遍历收件人、批量处理
- **通知**: 站内通知、Webhook、HTTP 请求
- **数据操作**: 变量设置、JSON 解析、模板渲染

### 版本控制

每次保存工作流会创建新版本：

```json
{
  "workflow_id": 1,
  "version": 3,
  "nodes": [...],
  "edges": [...],
  "created_at": "2026-04-20T10:00:00Z"
}
```

### 系统工作流

预置的系统级工作流（管理员可编辑）：

| 工作流 | 触发条件 | 动作 |
|--------|---------|------|
| 欢迎邮件 | 用户注册 | 发送欢迎邮件 |
| 密码变更通知 | 密码修改 | 发送安全通知 |
| 登录异常提醒 | 异常登录 | 发送警告邮件 |

### 模板市场

预构建的工作流模板，用户可一键导入：

```
GET /api/workflow-templates        # 浏览模板
POST /api/workflow-templates/{id}/import  # 导入模板
```

## Automation API

### 认证方式

使用 API Key 认证（Bearer Token）：

```bash
curl -H "Authorization: Bearer ak_xxxxxxxxxxxx" \
     https://mail.example.com/api/automation/temp-mailboxes
```

### API Key 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/api-keys` | 列出 API Key |
| `POST` | `/api/api-keys` | 创建 (含 scope 和 rate limit) |
| `DELETE` | `/api/api-keys/{id}` | 删除 |

### Scope 权限

| Scope | 说明 |
|-------|------|
| `temp_mailbox:create` | 创建临时邮箱 |
| `temp_mailbox:read` | 读取临时邮箱列表 |
| `temp_email:read` | 读取邮箱中的邮件 |
| `temp_code:read` | 读取验证码 |
| `temp_mailbox:extend` | 延长邮箱有效期 |
| `temp_mailbox:restore` | 恢复过期邮箱 |

### 幂等性

通过 `Idempotency-Key` 头实现幂等创建：

```bash
curl -X POST \
  -H "Authorization: Bearer ak_xxx" \
  -H "Idempotency-Key: unique-key-123" \
  https://mail.example.com/api/automation/temp-mailboxes \
  -d '{"prefix": "test"}'
```

## 临时邮箱

### 生命周期

```
创建 (active) → 过期 (expired, 24h后) → 可恢复 (10天内) → 永久删除
```

### 特性

- 自动提取验证码 (4-8 位，支持中英文模式)
- 24 小时默认有效期，可延期
- 过期后 10 天内可恢复
- 按用户配额限制

### 验证码提取

正则匹配模式：
- 英文: `verification code: XXXX`, `code is: XXXX`
- 中文: `验证码：XXXX`, `验证码为XXXX`
- 通用: 连续 4-8 位字母数字

详细 API 文档请参见 [API Reference](./api-reference.md)

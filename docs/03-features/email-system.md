# 邮件系统文档

## 概览

TalentMail 的邮件系统基于 Postfix + Dovecot + 自建 LMTP 实现，支持完整的邮件收发、文件夹管理、全文搜索、追踪、导入导出和 PGP 加密。

## 邮件收发流程

### 发送邮件

```
用户 → ComposePanel → POST /api/emails/send
  → 收件人/主题/正文/附件
  → 支持 CC/BCC
  → 支持定时发送 (scheduled_send_at)
  → 支持草稿自动保存
  → PGP 加密 (可选, 客户端加密)
  → Postfix relay → 目标 MTA
```

**发送端点**: `POST /api/emails/send`

| 参数 | 类型 | 说明 |
|------|------|------|
| `to` | string[] | 收件人列表 |
| `cc` | string[] | 抄送列表 |
| `bcc` | string[] | 密送列表 |
| `subject` | string | 主题 |
| `body_html` | string | HTML 正文 |
| `attachment_ids` | int[] | 已上传附件 ID |
| `in_reply_to` | string | 回复邮件的 Message-ID |
| `scheduled_send_at` | datetime | 定时发送时间 |
| `is_encrypted` | boolean | 是否 PGP 加密 |

### 接收邮件

```
外部 MTA → Postfix (:25)
  → LMTP handler (aiosmtpd)
  → email_parser 解析:
    - decode_mime_header (MIME 头解码)
    - parse_email_date (日期解析)
    - extract_email_address (地址提取)
    - get_email_body_and_attachments (正文+附件分离)
  → PostgreSQL 入库
  → WebSocket 推送 "new_email" 事件
  → 规则引擎执行 (如有匹配规则)
```

### IMAP 增量同步

后台任务每 30 秒同步一次 Dovecot：

```python
# 基于 UID 的增量同步
last_uid = db.query(max(Email.uid)).filter(user_id=...).scalar()
new_messages = imap.uid('FETCH', f'{last_uid+1}:*', '(RFC822)')
```

## 文件夹管理

### 系统文件夹

| 文件夹 | 类型 | 说明 |
|--------|------|------|
| INBOX | system | 收件箱 |
| Sent | system | 已发送 |
| Drafts | system | 草稿箱 |
| Trash | system | 回收站 |
| Archive | system | 归档 |
| Spam | system | 垃圾邮件 |

### 自定义文件夹

用户可创建自定义文件夹，支持：
- 创建 / 重命名 / 删除
- 邮件拖拽移动
- 文件夹排序

## 全文搜索

基于 PostgreSQL `tsvector` 实现：

```sql
-- 搜索索引 (邮件主题 + 发件人 + 收件人 + 正文)
CREATE INDEX idx_email_search ON emails USING gin(search_vector);
```

### 搜索过滤器

| 过滤器 | 说明 |
|--------|------|
| `q` | 关键词 (主题/发件人/正文) |
| `from` | 发件人地址 |
| `to` | 收件人地址 |
| `date_from` / `date_to` | 日期范围 |
| `has_attachment` | 是否有附件 |
| `is_starred` | 是否标星 |
| `is_read` | 是否已读 |
| `folder_id` | 文件夹 ID |

## 邮件追踪

### 追踪像素

发送邮件时可嵌入 1x1 透明 GIF 追踪像素：

```
GET /api/track/open/{pixel_id}  → 返回 1x1 GIF + 记录打开事件
```

记录数据：
- 打开次数
- 设备信息 (User-Agent)
- IP 地址 (脱敏)
- 首次/最后打开时间

## 邮件导入

### 支持格式

| 格式 | 说明 | 限制 |
|------|------|------|
| `.eml` | 单封邮件 | 50MB |
| `.mbox` | 邮箱归档 (多封) | 50MB, 最多 500 封 |

### 导入流程

```
POST /api/emails/import
  → 文件类型检测
  → email.message_from_bytes() / mailbox.mbox() 解析
  → Message-ID 去重 (同用户)
  → 附件保存到 /app/uploads/attachments/
  → 默认标记为已读 (is_read=True)
  → 返回 {total_found, imported, skipped_duplicate, errors}
```

限速: 5 次 / 5 分钟 / 用户

## 邮件导出

| 格式 | 端点 | 说明 |
|------|------|------|
| EML | `GET /api/emails/{id}/export/eml` | 原始 RFC 822 格式 |
| PDF | `GET /api/emails/{id}/export/pdf` | 打印视图 |

## PGP 端到端加密

### 架构原则

**客户端加密，服务端不触碰明文。** 私钥仅存在于浏览器 localStorage。

### 流程

```
发送方:
  1. 查找收件人公钥: GET /api/encryption/lookup?email=...
  2. OpenPGP.js 加密正文 + 主题
  3. 发送加密内容到服务端
  4. 服务端存储密文，标记 is_encrypted=True

接收方:
  1. 看到加密邮件横幅
  2. 输入私钥密码 → OpenPGP.js 解密
  3. 明文仅在浏览器内显示
```

### 密钥管理

| 端点 | 说明 |
|------|------|
| `GET /api/encryption/my-key` | 获取自己的公钥 |
| `POST /api/encryption/my-key` | 上传公钥 |
| `DELETE /api/encryption/my-key` | 删除公钥 |
| `GET /api/encryption/lookup?email=` | 查找用户公钥 |

## 批量操作

支持选中多封邮件后一键操作：

- 移动到文件夹
- 删除 / 永久删除
- 归档
- 标星 / 取消标星
- 标记已读 / 未读
- Gmail 风格撤销 (5 秒倒计时)

## 邮件线程

基于 `In-Reply-To` / `References` 头自动聚合邮件线程：

```
原始邮件 (Message-ID: abc@example.com)
  └── 回复1 (In-Reply-To: abc@example.com)
       └── 回复2 (In-Reply-To: def@example.com, References: abc def)
```

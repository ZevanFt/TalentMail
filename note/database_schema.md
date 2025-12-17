# 数据库设计方案 (V10 - 梦想版)

## 核心理念
本方案旨在构建一个功能强大、可扩展、同时兼顾自用与商业化潜力的邮件服务。它遵循 IMAP 标准以获得最佳兼容性，并通过域名、会员和兑换码系统，实现“进可商业化，退可自用”的灵活架构。

---

## 数据表目录 (Table of Contents)

- [1. `users` (用户表)](#1-users-用户表)
- [2. `plans` (会员方案表)](#2-plans-会员方案表)
- [3. `subscriptions` (用户订阅表)](#3-subscriptions-用户订阅表)
- [4. `redemption_codes` (兑换码/卡密表)](#4-redemption_codes-兑换码卡密表)
- [5. `transactions` (交易记录表)](#5-transactions-交易记录表)
- [6. `domains` (域名管理表)](#6-domains-域名管理表)
- [7. `folders` (文件夹表)](#7-folders-文件夹表)
- [8. `emails` (邮件表)](#8-emails-邮件表)
- [9. `attachments` (附件表)](#9-attachments-附件表)
- [10. `aliases` (邮件别名表)](#10-aliases-邮件别名表)
- [11. `signatures` (邮件签名表)](#11-signatures-邮件签名表)
- [12. `contacts` (联系人表)](#12-contacts-联系人表)
- [13. `filters` (筛选器/规则表)](#13-filters-筛选器规则表)
- [14. `templates` (邮件模板表)](#14-templates-邮件模板表)
- [15. `temp_mailboxes` (临时邮箱表)](#15-temp_mailboxes-临时邮箱表)
- [16. `tags` (标签表)](#16-tags-标签表)
- [17. `email_tags` (邮件-标签关联表)](#17-email_tags-邮件-标签关联表)
- [18. `tracking_pixels` (追踪像素表)](#18-tracking_pixels-追踪像素表)
- [19. `tracking_events` (追踪事件表)](#19-tracking_events-追踪事件表)
- [20. `user_sessions` (用户会话表)](#20-user_sessions-用户会话表)
- [21. `api_keys` (API密钥表)](#21-api_keys-api密钥表)
- [22. `server_logs` (系统日志表)](#22-server_logs-系统日志表)

---

## V10 表结构详解

### 1. `users` (用户表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `email` | String | 用户的完整邮箱地址 (唯一) |
| `phone` | String | 用户的手机号 (唯一, 可选) |
| `password_hash` | String | 加密后的用户密码 |
| `display_name` | String | 显示名称 |
| `avatar_url` | String | 头像图片链接 (可选) |
| `role` | String | **[V10]** 角色 ('user', 'admin') |
| `theme` | String | 外观主题 ('light', 'dark', 'system') |
| `recovery_email` | String | 安全辅助邮箱 (可选) |
| `two_factor_enabled`| Boolean | 是否启用两步验证 |
| `storage_used_bytes` | BigInt | 已用空间 (字节) |
| `auto_reply_enabled` | Boolean | 是否启用自动回复 |
| `auto_reply_start_date` | Date | 自动回复开始日期 (可选) |
| `auto_reply_end_date` | Date | 自动回复结束日期 (可选) |
| `auto_reply_message` | Text | 自动回复内容 (可选) |
| `enable_desktop_notifications` | Boolean | 启用桌面通知 |
| `enable_sound_notifications` | Boolean | 启用提示音 |
| `enable_pool_notifications` | Boolean | 启用账号池验证码推送 |
| `created_at` | DateTime | 账户创建时间 |

### 2. `plans` (会员方案表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `name` | String | 方案名称 ("Free", "Pro") |
| `price_monthly` | Decimal | 月付价格 |
| `price_yearly` | Decimal | 年付价格 |
| `storage_quota_bytes` | BigInt | 存储空间额度 |
| `max_domains` | Integer | **[V10]** 允许绑定多少个域名 |
| `max_aliases` | Integer | **[V10]** 允许创建多少个别名 |
| `allow_temp_mail` | Boolean | **[V10]** 是否允许使用临时邮箱 |
| `features` | JSON | 其他功能 |

### 3. `subscriptions` (用户订阅表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `plan_id` | Integer | **外键** -> `plans.id` |
| `status` | String | 订阅状态 ('active', 'canceled') |
| `current_period_end` | DateTime | 当前订阅周期的结束时间 |

### 4. `redemption_codes` (兑换码/卡密表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `code` | String | 唯一索引, 兑换码 (如 "VIP-YEAR-2025") |
| `plan_id` | Integer | **外键** -> `plans.id` |
| `duration_days` | Integer | 兑换时长 (如 365 表示一年) |
| `status` | String | 状态 ('unused', 'used', 'expired') |
| `created_by_id` | Integer | **外键** -> `users.id` (管理员ID) |
| `used_by_id` | Integer | **外键** -> `users.id` (使用者ID) |
| `used_at` | DateTime | 使用时间 |
| `created_at` | DateTime | 生成时间 |

### 5. `transactions` (交易记录表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `subscription_id` | Integer | **外键** -> `subscriptions.id` (可选) |
| `amount` | Decimal | 支付金额 |
| `currency` | String | 货币单位 ('CNY', 'USD') |
| `status` | String | 交易状态 ('succeeded', 'failed') |
| `payment_gateway_charge_id` | String | 支付网关的交易ID |
| `created_at` | DateTime | 交易创建时间 |

### 6. `domains` (域名管理表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` (域名所有者) |
| `domain_name` | String | 唯一, 域名 (e.g., "my-studio.com") |
| `is_verified` | Boolean | DNS 验证是否通过 (TXT记录验证) |
| `dkim_selector` | String | DKIM 选择器 (默认 "mail") |
| `dkim_private_key` | Text | 私钥 (服务器存着，发信用) |
| `dkim_public_key` | Text | 公钥 (给用户，让他填到 DNS 里) |
| `created_at` | DateTime | 创建时间 |

### 7. `folders` (文件夹表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `name` | String | 文件夹名 ("Inbox", "Work", "Sent") |
| `role` | String | 类型 ('system', 'user') |
| `parent_id` | Integer | **外键** -> `folders.id` (支持嵌套) |

### 8. `emails` (邮件表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `folder_id` | Integer | **[V10] 外键** -> `folders.id` |
| `mailbox_address` | String | **索引**, 邮件接收地址 |
| `message_id` | String | 邮件头中全局唯一的 `Message-ID` |
| `thread_id` | String | 用于聚合同一会话的ID |
| `subject` | String | 邮件主题 |
| `sender` | String | 发件人地址 |
| `recipients` | Text/JSON | 完整的收件人列表 |
| `body_text` | Text | 纯文本格式的邮件正文 |
| `body_html` | Text | HTML格式的邮件正文 |
| `received_at` | DateTime | 服务器收到邮件的时间 |
| `is_read` | Boolean | **[状态]** 是否已读 |
| `is_starred` | Boolean | **[状态]** 是否星标 |
| `is_draft` | Boolean | **[状态]** 是否为草稿 |
| `sent_at` | DateTime | **[状态]** 邮件发送时间 (可选) |
| `scheduled_send_at` | DateTime | **[功能]** 定时发送的时间 (可选) |
| `snoozed_until` | DateTime | **[功能]** 稍后处理，到期时间 (可选) |
| `is_tracked` | Boolean | **[追踪]** 此邮件发送时是否启用了追踪 |

### 9. `attachments` (附件表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `email_id` | Integer | **外键** -> `emails.id` |
| `filename` | String | 附件的原始文件名 |
| `content_type` | String | 附件的MIME类型 |
| `file_path` | String | 附件在服务器上的存储路径 (可选) |
| `attached_email_id` | Integer | **外键** -> `emails.id` (作为附件的邮件) (可选) |

### 10. `aliases` (邮件别名表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `alias_email` | String | 别名邮箱地址 (唯一) |
| `name` | String | 别名用途描述 (e.g., "工作") |
| `is_active` | Boolean | 是否启用 |

### 11. `signatures` (邮件签名表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `name` | String | 签名名称 (e.g., "工作签名") |
| `content_html` | Text | 签名内容 (HTML格式) |
| `is_default` | Boolean | 是否为默认签名 |

### 12. `contacts` (联系人表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `owner_id` | Integer | **外键** -> `users.id` |
| `name` | String | 联系人姓名 |
| `email` | String | 联系人邮箱 |
| `phone` | String | 联系人电话 (可选) |
| `notes` | Text | 备注 (可选) |

### 13. `filters` (筛选器/规则表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `name` | String | 规则名称 |
| `priority` | Integer | 执行优先级 |
| `conditions` | JSON | **IF**: 规则的条件 |
| `actions` | JSON | **THEN**: 规则要执行的动作 |

### 14. `templates` (邮件模板表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `name` | String | 模板名称 |
| `subject` | String | 模板主题 |
| `body_html` | Text | 模板内容 |

### 15. `temp_mailboxes` (临时邮箱表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `owner_id` | Integer | **外键** -> `users.id` |
| `email` | String | 临时邮箱的完整地址 (唯一) |
| `purpose` | String | 用途标签 |
| `auto_verify_codes` | Boolean | 是否自动识别验证码 |
| `is_active` | Boolean | 是否可用 (默认 True) |
| `created_at` | DateTime | 创建时间 |

### 16. `tags` (标签表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `name` | String | 标签名称 |
| `color` | String | 标签颜色 |

### 17. `email_tags` (邮件-标签关联表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `email_id` | Integer | **主键/外键** -> `emails.id` |
| `tag_id` | Integer | **主键/外键** -> `tags.id` |

### 18. `tracking_pixels` (追踪像素表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | UUID | **主键**, 用于生成追踪URL的唯一ID |
| `email_id` | Integer | **外键** -> `emails.id` |
| `created_at` | DateTime | 创建时间 |

### 19. `tracking_events` (追踪事件表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `pixel_id` | UUID | **外键** -> `tracking_pixels.id` |
| `event_type` | String | 事件类型 ('open', 'click') |
| `timestamp` | DateTime | 事件发生时间 |
| `ip_address` | String | 访问者IP地址 |
| `user_agent` | String | 访问者设备信息 |

### 20. `user_sessions` (用户会话表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `device_info` | String | 设备/浏览器信息 |
| `ip_address` | String | 登录IP地址 |
| `location` | String | 地理位置 (可选) |

### 21. `api_keys` (API密钥表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | Integer | **主键** |
| `user_id` | Integer | **外键** -> `users.id` |
| `key` | String | 唯一的 API 密钥 |
| `permissions` | JSON | 权限 (e.g., `{"send_email": true}`) |
| `last_used_at` | DateTime | 最后使用时间 |
| `created_at` | DateTime | 创建时间 |

### 22. `server_logs` (系统日志表)
| 字段名 | 数据类型 | 描述 |
| :--- | :--- | :--- |
| `id` | BigInt | **主键** |
| `level` | String | 'INFO', 'WARN', 'ERROR' |
| `source` | String | 来源 ('smtp', 'imap', 'web') |
| `message` | Text | 日志内容 |

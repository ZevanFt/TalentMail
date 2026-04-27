# 术语表

## 邮件协议

| 术语 | 全称 | 说明 |
|------|------|------|
| **SMTP** | Simple Mail Transfer Protocol | 邮件发送协议，端口 25 (明文) / 465 (SSL) / 587 (STARTTLS) |
| **IMAP** | Internet Message Access Protocol | 邮件接收协议，端口 143 (明文) / 993 (SSL)，支持服务端文件夹管理 |
| **POP3** | Post Office Protocol v3 | 邮件接收协议（TalentMail 不使用），下载后从服务器删除 |
| **LMTP** | Local Mail Transfer Protocol | 本地邮件传输协议，Postfix 将邮件交给 TalentMail 的方式 |
| **MIME** | Multipurpose Internet Mail Extensions | 邮件内容编码标准，支持附件、HTML、多语言字符集 |
| **RFC 822** | - | 互联网邮件格式标准，定义邮件头和正文结构 |

## 邮件安全

| 术语 | 全称 | 说明 |
|------|------|------|
| **SPF** | Sender Policy Framework | DNS TXT 记录，声明哪些 IP 可以代表域名发送邮件。例: `v=spf1 mx ~all` |
| **DKIM** | DomainKeys Identified Mail | 邮件数字签名，接收方可验证邮件未被篡改 |
| **DMARC** | Domain-based Message Authentication, Reporting & Conformance | 基于 SPF + DKIM 的策略，告诉接收方如何处理验证失败的邮件 |
| **TLS** | Transport Layer Security | 传输层加密，保护邮件在传输过程中的安全 |
| **STARTTLS** | - | 在明文连接上升级为 TLS 加密的机制 |
| **PGP** | Pretty Good Privacy | 端到端加密标准，TalentMail 使用 OpenPGP.js 在客户端实现 |
| **S/MIME** | Secure/Multipurpose Internet Mail Extensions | 基于证书的邮件加密标准（规划中） |

## 邮件服务组件

| 术语 | 说明 |
|------|------|
| **Postfix** | 高性能 MTA (Mail Transfer Agent)，负责邮件的发送和中转路由 |
| **Dovecot** | IMAP/POP3 服务器，负责邮件存储和客户端访问 |
| **Fail2Ban** | 入侵防御工具，自动封禁暴力破解 IP |
| **MTA** | Mail Transfer Agent，邮件传输代理（如 Postfix） |
| **MDA** | Mail Delivery Agent，邮件投递代理（如 Dovecot LDA） |
| **MUA** | Mail User Agent，邮件客户端（如 Thunderbird、TalentMail 前端） |

## 邮件概念

| 术语 | 说明 |
|------|------|
| **Message-ID** | 邮件的全局唯一标识符，格式: `<uuid@domain>` |
| **In-Reply-To** | 回复邮件时指向原始邮件的 Message-ID，用于线程关联 |
| **References** | 邮件线程中所有相关邮件的 Message-ID 列表 |
| **Envelope** | SMTP 协议层的发件人/收件人，可能与邮件头中的 From/To 不同 |
| **BCC** | Blind Carbon Copy，密送，收件人互不可见 |
| **Tracking Pixel** | 1x1 透明 GIF 图片，嵌入邮件中用于追踪是否被打开 |

## TalentMail 专有概念

| 术语 | 说明 |
|------|------|
| **临时邮箱 (Temp Mailbox)** | 一次性邮件地址，默认 24h 有效，过期后 10 天可恢复 |
| **验证码提取** | 自动从收到的邮件中提取 4-8 位验证码 |
| **邮件池 (Pool)** | 临时邮箱的管理界面，显示所有创建的一次性邮箱 |
| **工作流 (Workflow)** | 可视化流程编辑器，通过拖拽节点定义自动化流程 |
| **规则引擎** | 基于条件自动执行邮件操作（移动、标记、转发等） |
| **Automation API** | 使用 API Key 认证的外部集成接口 |
| **Idempotency-Key** | 幂等键，防止重复创建资源 |
| **写信模板** | 用户自定义的邮件模板，用于快速写信 |
| **系统模板** | 管理员管理的邮件模板，用于系统通知和自动化 |

## 技术栈术语

| 术语 | 说明 |
|------|------|
| **Nuxt 4** | Vue 3 全栈框架，支持 SSR/SSG，TalentMail 的前端框架 |
| **FastAPI** | 高性能 Python Web 框架，自动生成 OpenAPI 文档 |
| **SQLAlchemy** | Python ORM 框架，TalentMail 使用 2.0 版本 |
| **Alembic** | SQLAlchemy 的数据库迁移工具 |
| **Pydantic** | Python 数据验证库，用于请求/响应 schema |
| **TipTap** | 基于 ProseMirror 的富文本编辑器 |
| **Vue Flow** | Vue 3 的流程图编辑器组件库 |
| **Caddy** | 自动 HTTPS 的反向代理服务器 |
| **OpenPGP.js** | JavaScript PGP 加密库，用于客户端 E2E 加密 |
| **tsvector** | PostgreSQL 全文搜索索引类型 |
| **JWT** | JSON Web Token，用于无状态认证 |
| **TOTP** | Time-based One-Time Password，基于时间的一次性密码 (2FA) |
| **PWA** | Progressive Web App，渐进式 Web 应用 |
| **DOMPurify** | HTML 清理库，防止 XSS 攻击 |

## DNS 记录类型

| 类型 | 说明 | TalentMail 用途 |
|------|------|----------------|
| **A** | 域名 → IPv4 地址 | `mail.example.com` → 服务器 IP |
| **MX** | 邮件交换记录 | `example.com` → `maillink.example.com` |
| **TXT** | 文本记录 | SPF、DKIM、DMARC 配置 |
| **CNAME** | 别名记录 | 可选的域名别名 |

---

最后更新: 2026-04-27

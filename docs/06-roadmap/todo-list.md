# TalentMail 待办事项清单

本文档记录了项目当前待完善的功能和未来的开发计划。

> 最后更新：2026-09-16

## 功能完成度概览

| 模块 | 完成度 | 状态 | 说明 |
|------|--------|------|------|
| 核心邮件功能 | 100% | 已完成 | SMTP/IMAP、附件、全文搜索等 |
| 用户系统 | 100% | 已完成 | 登录、注册、2FA、会话管理、SSO 建邮箱 |
| 工作流系统 | 100% | 已完成 | 图遍历引擎、条件分支、并行执行、事件驱动 |
| 模板系统 | 100% | 已完成 | 可视化编辑、变量替换、测试发送 |
| 自动化规则 | 100% | 已完成 | 规则引擎、条件匹配、动作执行 |
| 账号池功能 | 100% | 已完成 | 临时邮箱、验证码识别 |
| API 开放平台 | 90% | 基本完成 | Key 管理、鉴权、限流分层、SDK/文档示例已落地；**OAuth 不自建**，作为 Auth Center 客户端接入（见 auth-center-integration.md） |
| 订阅计费 | 100% | 已完成 | 套餐管理、兑换码 |
| PWA 支持 | 100% | 已完成 | 可安装为桌面/移动应用 |
| 安全性功能 | 100% | 已完成 | 密码加密、配置加密、会话识别 |
| 批量操作 | 100% | 已完成 | 批量读/星标/移动/删除/归档 |
| 垃圾邮件 | 100% | 已完成 | 白名单、标记、`sa-learn` 训练链路 |
| 备份恢复 | 90% | 基本完成 | 脚本 + systemd timer + 管理端 API + openssl 加密 + uploads 打包 |
| 操作审计 | 100% | 已完成 | 登录/SSO登录/备份/发信/删用户/云盘/联系人/工作流/模板触发(规则+工作流+手动)/API Key 创建吊销；API 调用审计在 api_key_audit_logs；管理端可查 |
| 性能监控 | 100% | 已完成 | health 含 DB/任务/磁盘/uptime/邮件队列 + API P95/P99、mail_sync 耗时、慢查询；Webhook 告警覆盖死任务/队列积压/API 延迟/同步失败与过慢/慢查询 |
| 国际化 | 100% | 已完成 | 批次3 完成：布局侧栏/Header、账号池、云盘/通讯录/附件/分享、注册/找回密码/SSO回调、日历弹窗、编辑器工具栏、common 组件、error 页、settings 余量全部迁入 zh/en；覆盖检查 t() 零缺失，前端 build 通过 |
| 日历增强 | 100% | 已完成 | 周视图 + 循环 + .ics 进出 + CalDAV 读写 + sync-token/calendar-query/multiget 增量同步 |

## 已完成的高优先级任务

### 1. 安全性增强
- [x] **密码加密存储** - 2025-02-01
  - 创建 `core/crypto.py` 加密模块
  - Fernet 对称加密算法
  - 数据迁移脚本

- [x] **会话识别优化** - 2025-02-03
  - JWT token 中添加 session_id
  - TokenData schema 添加 session_id 字段
  - 会话列表 API 支持 is_current 标识

- [x] **敏感配置加密** - 2025-02-03
  - `scripts/config_encrypt.py` 配置加密工具
  - 支持 encrypt/decrypt 单个值
  - 支持 encrypt-file/decrypt-file 整个 .env 文件

### 2. 工作流引擎升级
- [x] **支持复杂流程图** - 2025-02-03
  - GraphExecutor 图遍历执行器
  - 条件分支（通过 source_handle）
  - 并行执行（asyncio.gather）
  - 完全向后兼容

- [x] **高级节点类型** - 2025-02-03
  - DelayHandler - 延时等待节点
  - LoopHandler - 循环执行节点
  - ParallelHandler - 并行执行节点
  - SwitchHandler - 多路分支节点
  - WebhookHandler - Webhook 调用节点
  - TransformHandler - 数据转换节点

- [x] **工作流底层逻辑完善** - 2025-02-03
  - 41 个节点处理器
  - 34 个节点类型，32 个有 config_schema
  - 4 个系统工作流绑定事件
  - 业务代码触发点：user.registered, user.login, password.changed

### 3. 邮件系统功能
- [x] **全文搜索引擎** - 2025-02-03
  - PostgreSQL 原生全文搜索（tsvector + GIN 索引）
  - 自动更新触发器
  - 按相关性排序（ts_rank）

- [x] **垃圾邮件过滤** - 2025-02-03
  - 白名单管理 API
  - 标记垃圾/非垃圾邮件
  - SpamAssassin 学习接口

- [x] **批量操作功能** - 2025-02-03
  - 批量标记已读/未读
  - 批量标记星标
  - 批量移动/删除/归档

## 中优先级任务（开发中）

### 1. 邮件与平台能力
- [x] **垃圾邮件训练闭环** - 2026-03-08
  - 真实 `sa-learn --spam/--ham` 已接入
  - 训练结果持久化与失败重试
  - 后台任务可观测日志

- [x] **API 开放平台（阶段化推进）** - 2026-03-08
  - 已完成：API Key 管理、Scope 鉴权、自动化临时邮箱与验证码接口
  - 已完成：基础限流、审计日志、幂等、场景分层限流
  - 已完成：开发者指南 + Python/Node/Bash SDK 示例
  - 待完成：OAuth、公共开发者门户

### 2. 系统功能
- [x] **备份恢复机制** - 2026-03-08
  - `backup-db.sh` / `restore-db.sh`
  - systemd timer（每日 03:17）
  - 管理端 `GET/POST /api/admin/backups`
  - 待增强：备份加密、上传目录打包

- [x] **操作日志审计（骨架）** - 2026-03-08 / 2026-09-16 收尾
  - `operation_audit_logs` 表 + 写入辅助
  - 登录 / 备份 / 发信 / 删用户 / 云盘 / 联系人 / 工作流 / **SSO 登录** / **模板触发（规则+工作流+手动）** / **API Key 创建吊销** 已接入
  - API 调用级审计在 `api_key_audit_logs`（deps 鉴权链路 allow/deny）
  - 管理端查询 API
  - 待完成：异常行为检测

- [x] **性能监控系统** - 2026-03-08 / 2026-09-16 补齐
  - health 含 DB / 后台任务 / 磁盘 / uptime / 邮件队列
  - health 新增 performance：API p50/p95/p99、mail_sync 耗时、慢查询
  - Webhook 告警（冷却 + 后台巡检）：死任务 / 队列积压 / API P95 / mail_sync 失败或过慢 / 慢查询累计

- [x] **国际化框架扩展** - 2026-03-08
  - 登录 / 通讯录 / 云盘 / 日历接入
  - 登录页语言快捷切换

- [x] **操作审计 UI** - 2026-03-08
  - 设置 → 管理 → 操作审计
  - 按动作/状态/用户筛选 + 分页

## 低优先级任务

### 1. 用户体验
- [x] **主题系统扩展** - 2026-03-08
  - 6 套品牌色预设（CSS 变量 + 设置页切换）
  - 自定义主题编辑器仍属后续

- [x] **国际化完善** - 2026-09-16 完成
  - [x] 管理后台全量翻译 - 2026-09-13（用户权限/邀请码/保留前缀/操作审计/邮件模板/系统工作流/API 密钥/临时邮箱策略/订阅管理/更新日志）
  - [x] 设置页壳 + 账号信息/主题/存储/多账号/邮件设置/隐私/加密/登录与安全迁入 i18n - 2026-09-13
  - [x] 邮件列表/写信/详情 + 工作流编辑器/教程迁入 i18n - 2026-09-16
  - [x] 布局侧栏/Header、账号池、云盘/通讯录/附件/分享、注册/找回密码/SSO回调、日历弹窗、编辑器工具栏、common、error、settings 余量迁入 i18n - 2026-09-16

### 2. 集成功能
- [ ] **第三方日历集成**
  - Google Calendar
  - Outlook Calendar
- [ ] **CalDAV 增强**
  - [x] 写回（PUT/DELETE）- 2026-03-08
  - [x] sync-token 增量同步（RFC 6578 + calendar-query/multiget）- 2026-09-16
  - [x] 应用专用密码（设置→登录与安全；SSO 用户也可用）- 2026-09-16
- [x] **SSO 单点登出闭环** - 2026-09-16
  - TalentMail `POST /api/auth/sso/backchannel-logout`（共享密钥校验，吊销该 SSO 用户全部会话）
  - Auth-Center 登出后 fire-and-forget 通知 `AUTH_CENTER_BACKCHANNEL_LOGOUT_URLS`
  - 密钥：`SSO_BACKCHANNEL_SECRET` / `AUTH_CENTER_BACKCHANNEL_SECRET`

---

**相关文档**：
- [当前开发任务](./current-tasks.md)
- [开发指南](../04-development/README.md)

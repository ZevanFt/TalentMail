# TalentMail 开发路线图

> 最后更新: 2025-12-19 (第二次更新)

---

## ✅ 已完成功能

### Phase 1: 基础架构
- [x] 项目初始化 (FastAPI + Nuxt3 + PostgreSQL)
- [x] Docker 开发环境配置
- [x] 用户认证系统 (JWT)
- [x] 邮件服务器集成 (Postfix + Dovecot)

### Phase 2: 核心邮件功能
- [x] 邮件发送 (SMTP)
- [x] 邮件接收 (LMTP)
- [x] 邮件列表/详情
- [x] 文件夹管理 (收件箱/已发送/草稿/垃圾箱等)
- [x] 标记已读/未读/星标
- [x] 待办邮件 (Snooze)
- [x] 删除邮件 (软删除)
- [x] 回复/转发
- [x] 邮件搜索
- [x] 草稿功能

### Phase 3: 高级邮件功能
- [x] 邮件追踪 (打开追踪)
- [x] 投递状态 (pending/sending/sent/failed)
- [x] 重新发送失败邮件
- [x] 实时通知 (WebSocket)
- [x] 邮件签名管理

### Phase 4: 附件功能 ✅
- [x] 附件上传 API
- [x] 附件下载 API
- [x] 发送邮件带附件
- [x] 接收邮件解析附件 (LMTP)
- [x] 邮件列表附件标识
- [x] 邮件详情附件展示

### Phase 5: 会员订阅制度 ✅ (2025-12-19 完成)
- [x] 套餐管理 (Free/Pro/Enterprise)
- [x] 兑换码生成与管理
- [x] 用户兑换码激活
- [x] 订阅状态显示
- [x] 兑换码统计
- [x] 管理后台界面

### 用户系统
- [x] 用户登录
- [x] 邀请码注册
- [x] 邀请码管理 (管理员)
- [x] 个人资料设置
- [x] 修改密码
- [x] 用户权限管理
- [x] 登录设备记录 ✅ (2025-12-19 完成)
- [x] 管理员创建用户 ✅ (2025-12-19 完成)
- [x] 保留邮箱前缀管理 ✅ (2025-12-19 完成)
- [x] 邮箱验证码注册 ✅ (2025-12-19 完成)

### 账号池功能
- [x] 临时邮箱创建/删除
- [x] 邮件列表查看
- [x] 验证码自动识别
- [x] 统计分析
- [x] 活动日志

### 设置页面
- [x] 通知偏好
- [x] 邮件设置 (签名/自动回复)
- [x] 存储统计
- [x] 账号管理
- [x] 主题切换 (深色/浅色)
- [x] 系统邮件模板管理 ✅ (2025-12-19 完成)

---

## 📝 本次对话完成的工作 (2025-12-19)

### 1. 邮箱验证码注册功能
| 模块 | 文件 | 说明 |
|------|------|------|
| 数据库模型 | `backend/db/models/system.py` | `VerificationCode` 模型 |
| 验证码 API | `backend/api/auth.py` | 发送验证码、验证、带验证码注册 |
| 邮件发送 | `backend/core/mail.py` | `send_verification_code_email()` |
| 前端注册页 | `frontend/app/pages/register.vue` | 两步注册流程 |
| 前端 API | `frontend/app/composables/useApi.ts` | 验证码相关方法 |

### 2. 系统邮件模板管理
| 模块 | 文件 | 说明 |
|------|------|------|
| 数据库模型 | `backend/db/models/system.py` | `SystemEmailTemplate` 模型 |
| 模板 API | `backend/api/email_templates.py` | CRUD + 预览 |
| 初始化数据 | `backend/initial/initial_data.py` | 6个默认模板 |
| 管理界面 | `frontend/app/components/settings/EmailTemplates.vue` | 模板管理 |
| 设置页面 | `frontend/app/pages/settings.vue` | 添加菜单入口 |

### 3. 默认邮件模板
| 模板代码 | 名称 | 分类 |
|----------|------|------|
| `verification_code_register` | 注册验证码 | system |
| `verification_code_reset_password` | 密码重置验证码 | system |
| `welcome_email` | 欢迎邮件 | system |
| `password_changed` | 密码修改通知 | notification |
| `login_alert` | 登录提醒 | notification |
| `subscription_expiring` | 订阅即将到期 | notification |

### 4. 数据库迁移
- `6919422f0fb7_add_verification_codes_table.py`
- `f71f922998f4_add_system_email_templates_table.py`

---

## 📋 待完成功能

### Phase 6: 设置页面完善 (优先级：中)

| 功能 | 描述 | 复杂度 | 状态 |
|------|------|--------|------|
| 隐私设置持久化 | 阻止外部图片等设置绑定后端 API | ⭐ | 待开发 |
| 邮件过滤规则 | 根据发件人/主题/内容自动分类、标记、移动邮件 | ⭐⭐⭐ | 待开发 |
| 自动转发规则 | 将符合条件的邮件自动转发到其他地址 | ⭐⭐ | 待开发 |
| 密码重置功能 | 通过验证码重置密码 | ⭐⭐ | 待开发 |

### Phase 7: 高级功能 (优先级：低)

| 功能 | 描述 | 复杂度 | 状态 |
|------|------|--------|------|
| 两步验证 (2FA) | TOTP 验证器支持 (Google Authenticator 等) | ⭐⭐ | 待开发 |
| 用户邮件模板 | 用户自定义邮件模板，快速发送常用邮件 | ⭐⭐ | 待开发 |
| 多账号管理 | 集成外部 IMAP/SMTP 账号 | ⭐⭐⭐ | 待开发 |
| 联系人管理 | 通讯录、收件人自动补全 | ⭐⭐ | 待开发 |
| 日历集成 | 邮件中的日期自动识别、日历邀请 | ⭐⭐⭐ | 待开发 |

### Phase 8: 生产部署 (优先级：低)

| 功能 | 描述 | 复杂度 | 状态 |
|------|------|--------|------|
| TLS/SSL 配置 | HTTPS、SMTPS (465)、IMAPS (993) | ⭐⭐ | 待开发 |
| Docker Compose 生产配置 | 优化镜像大小、环境变量管理 | ⭐ | 待开发 |
| 监控告警 | 日志收集 (ELK)、性能监控 (Prometheus) | ⭐⭐⭐ | 待开发 |
| 备份恢复 | 数据库备份、附件备份策略 | ⭐⭐ | 待开发 |
| CDN 配置 | 静态资源加速 | ⭐ | 待开发 |

---

## 🎯 推荐下一步开发

### 短期目标 (1-2 周)

#### 1. 密码重置功能 ⭐⭐
利用已完成的验证码系统，实现忘记密码功能：
- 后端：`POST /api/auth/forgot-password` - 发送重置验证码
- 后端：`POST /api/auth/reset-password` - 验证码 + 新密码
- 前端：忘记密码页面

#### 2. 隐私设置持久化 ⭐
将前端的隐私设置保存到后端：
- 后端：用户表添加 `block_external_images` 字段
- 后端：`PATCH /api/users/me` 支持更新隐私设置
- 前端：Privacy.vue 绑定后端 API

#### 3. 联系人管理 ⭐⭐
提升写邮件效率：
- 后端：联系人 CRUD API
- 前端：联系人管理界面
- 前端：写邮件时收件人自动补全

### 中期目标 (2-4 周)

#### 4. 邮件过滤规则 ⭐⭐⭐
自动化邮件处理：
- 后端：过滤规则 CRUD API
- 后端：LMTP 接收邮件时应用规则
- 前端：规则管理界面

#### 5. 两步验证 (2FA) ⭐⭐
提升账户安全：
- 后端：TOTP 密钥生成、验证
- 前端：2FA 设置界面、登录时验证

### 长期目标 (1-2 月)

#### 6. 多账号管理 ⭐⭐⭐
集成外部邮箱：
- 后端：外部账号配置存储
- 后端：IMAP 同步外部邮件
- 后端：SMTP 发送外部邮件
- 前端：账号管理界面

#### 7. 生产部署
准备上线：
- TLS/SSL 配置
- 性能优化
- 监控告警

---

## 📊 当前系统状态

| 服务 | 地址 | 状态 |
|------|------|------|
| 前端 | http://localhost:3000 | ✅ |
| 后端 | http://localhost:8000 | ✅ |
| 数据库 | PostgreSQL:5432 | ✅ |
| 邮件服务器 | SMTP:25, IMAP:143 | ✅ |
| LMTP | port 24 | ✅ |
| WebSocket | ws://localhost:8000/ws | ✅ |

**测试账户**: admin@talenting.test / adminpassword

---

## 📁 项目结构

```
talentmail/
├── backend/                 # FastAPI 后端
│   ├── api/                # API 路由
│   │   ├── auth.py         # 认证 (含验证码)
│   │   ├── email_templates.py  # 邮件模板管理
│   │   ├── billing.py      # 会员订阅
│   │   ├── reserved_prefixes.py  # 保留前缀
│   │   └── ...
│   ├── core/               # 核心功能
│   │   ├── mail.py         # 邮件发送 (含模板渲染)
│   │   └── ...
│   ├── crud/               # 数据库操作
│   ├── db/                 # 数据库模型
│   │   └── models/
│   │       ├── system.py   # 系统模型 (验证码、模板、保留前缀)
│   │       ├── billing.py  # 订阅模型
│   │       └── ...
│   ├── initial/            # 初始化数据
│   │   └── initial_data.py # 默认套餐、前缀、模板
│   └── schemas/            # Pydantic 模型
├── frontend/               # Nuxt3 前端
│   └── app/
│       ├── components/     # Vue 组件
│       │   └── settings/   # 设置页面组件
│       │       ├── EmailTemplates.vue  # 邮件模板管理
│       │       ├── ReservedPrefixes.vue  # 保留前缀管理
│       │       ├── Billing.vue  # 会员订阅
│       │       └── ...
│       ├── composables/    # 组合式函数
│       │   └── useApi.ts   # API 方法
│       ├── layouts/        # 布局
│       └── pages/          # 页面
│           ├── register.vue  # 注册 (含验证码)
│           └── ...
├── config/                 # 配置文件
│   ├── caddy/             # Caddy 反向代理
│   └── mail/              # 邮件服务器配置
└── note/                   # 开发文档
    └── DEVELOPMENT_ROADMAP.md  # 本文件
```

---

## 🔧 技术栈

- **后端**: FastAPI, SQLAlchemy, PostgreSQL
- **前端**: Nuxt3, Vue3, TailwindCSS
- **邮件**: Postfix (SMTP), Dovecot (IMAP), 自定义 LMTP
- **部署**: Docker, Caddy
- **实时通信**: WebSocket

---

## 📈 功能完成度统计

| 模块 | 完成 | 待开发 | 完成率 |
|------|------|--------|--------|
| 核心邮件 | 10 | 0 | 100% |
| 高级邮件 | 5 | 0 | 100% |
| 附件功能 | 6 | 0 | 100% |
| 会员订阅 | 6 | 0 | 100% |
| 用户系统 | 10 | 2 | 83% |
| 账号池 | 5 | 0 | 100% |
| 设置页面 | 7 | 3 | 70% |
| 高级功能 | 0 | 5 | 0% |
| 生产部署 | 0 | 5 | 0% |

**总体完成度**: 约 75%
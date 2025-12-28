<p align="center">
  <img src="logo.png" alt="Talenting Logo" width="400">
</p>

<h1 align="center">TalentMail</h1>

<p align="center">
  <strong>🚀 现代化自托管邮件服务平台</strong>
</p>

<p align="center">
  一个功能完整、安全可靠的企业级邮件解决方案
</p>

---

## ✨ 功能特性

### 📧 核心邮件功能
- **邮件收发** - 完整的 SMTP/IMAP 支持，支持附件、HTML 邮件
- **文件夹管理** - 收件箱、已发送、草稿、垃圾箱、归档等
- **邮件搜索** - 快速全文搜索，支持多条件筛选
- **邮件追踪** - 打开追踪、投递状态实时反馈
- **草稿与定时发送** - 保存草稿，定时发送邮件
- **回复与转发** - 支持引用回复、转发邮件

### 🔐 安全与隐私
- **JWT 认证** - 安全的用户认证机制
- **两步验证 (2FA)** - TOTP 验证器支持
- **登录设备管理** - 查看和管理登录设备
- **隐私设置** - 阻止外部图片、垃圾邮件过滤

### 👥 用户管理
- **邀请码注册** - 可控的用户增长
- **邮箱验证码** - 安全的注册流程
- **会员订阅制度** - 灵活的套餐管理
- **用户权限管理** - 管理员/普通用户角色

### 📮 账号池功能
- **临时邮箱** - 快速创建临时邮箱
- **验证码识别** - 自动提取邮件中的验证码
- **统计分析** - 邮箱使用情况统计

### 🎨 用户体验
- **深色/浅色主题** - 自适应系统主题
- **实时通知** - WebSocket 实时推送
- **响应式设计** - 适配各种屏幕尺寸
- **邮件签名** - 自定义邮件签名

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Nuxt.js 3, Vue.js 3, TypeScript, Tailwind CSS |
| **后端** | FastAPI, Python 3, Pydantic V2, SQLAlchemy |
| **数据库** | PostgreSQL |
| **邮件服务** | docker-mailserver (Postfix + Dovecot) |
| **反向代理** | Caddy |
| **容器化** | Docker, Docker Compose |

---

## 🚀 快速开始

### 环境要求
- Docker & Docker Compose
- Git

### 开发环境部署

#### 第 1 步：配置本地 DNS

编辑 `/etc/hosts` (Linux/macOS) 或 `C:\Windows\System32\drivers\etc\hosts` (Windows)：

```
127.0.0.1   mail.talenting.test
```

#### 第 2 步：启动开发环境

```bash
# 克隆项目
git clone <repository-url>
cd talentmail

# 使用开发脚本启动 (推荐)
chmod +x dev.sh
./dev.sh

# 或手动启动
docker compose -f docker-compose.dev.yml up -d --build
```

#### 第 3 步：初始化数据库（仅首次）

```bash
docker compose -f docker-compose.dev.yml exec backend python -m initial.initial_data
```

#### 第 4 步：访问应用

| 服务 | 地址 |
|------|------|
| 主应用 | https://mail.talenting.test |
| 前端 (备用) | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

**默认管理员账户**: `admin@talenting.test` / `adminpassword`

---

## ⚙️ 配置说明

### 核心配置文件

项目使用 `config.json` 作为核心配置文件（单一事实来源）：

```json
{
  "currentEnvironment": "development",
  "environments": {
    "development": {
      "baseDomain": "talenting.test",
      "webPrefix": "mail",
      "mailServerPrefix": "maillink"
    },
    "production": {
      "baseDomain": "talenting.vip",
      "webPrefix": "mail",
      "mailServerPrefix": "maillink"
    }
  }
}
```

### 环境变量配置 (.env)

复制示例文件并编辑：

```bash
cp .env.example .env
nano .env
```

**必填配置项：**

| 变量 | 说明 | 示例 |
|------|------|------|
| `CURRENT_ENVIRONMENT` | 当前环境 | `development` 或 `production` |
| `SECRET_KEY` | JWT 密钥 | `openssl rand -hex 32` 生成 |
| `POSTGRES_PASSWORD` | 数据库密码 | 设置强密码 |
| `ADMIN_PASSWORD` | 管理员密码 | 设置强密码 |
| `DEFAULT_MAIL_PASSWORD` | 邮件账户默认密码 | 设置强密码 |

---

## 🌐 生产环境部署

### 1. 服务器要求

- **操作系统**: Ubuntu 20.04 LTS 或 22.04 LTS
- **配置**: 至少 2核 CPU, 4GB 内存
- **端口开放**: 80, 443, 25, 143, 587, 993

### 2. DNS 配置 (Cloudflare)

| 类型 | 名称 | 内容 | 代理状态 | 说明 |
|------|------|------|----------|------|
| **A** | `mail` | `服务器IP` | ✅ 已代理 | Web 应用 |
| **A** | `maillink` | `服务器IP` | ❌ 仅 DNS | **必须关闭代理！** |
| **MX** | `@` | `maillink.example.com` | - | 优先级 10 |
| **TXT** | `@` | `v=spf1 mx ~all` | - | SPF 记录 |

> ⚠️ **重要**: `maillink` 子域名必须是 **灰色云朵 (DNS Only)**，否则邮件无法正常收发！

### 3. 一键部署

```bash
# 配置环境变量
cp .env.example .env
nano .env  # 编辑必填项

# 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 4. SSL 证书配置 (可选)

```bash
# 同步 Let's Encrypt 证书到邮件服务器
chmod +x scripts/sync_mail_certs.sh
./scripts/sync_mail_certs.sh
```

---

## 📁 项目结构

```
talentmail/
├── backend/              # FastAPI 后端
│   ├── api/              # API 路由
│   ├── core/             # 核心功能 (配置、安全、邮件)
│   ├── crud/             # 数据库操作
│   ├── db/               # 数据库模型
│   ├── schemas/          # Pydantic 模型
│   └── initial/          # 初始化数据
├── frontend/             # Nuxt.js 前端
│   └── app/
│       ├── components/   # Vue 组件
│       ├── pages/        # 页面
│       ├── layouts/      # 布局
│       └── composables/  # 组合式函数
├── config/               # 配置文件
│   ├── caddy/            # Caddy 反向代理配置
│   └── mail/             # 邮件服务器配置
├── scripts/              # 辅助脚本
├── config.json           # 核心配置文件
├── dev.sh                # 开发环境脚本
└── deploy.sh             # 生产环境部署脚本
```

---

## 🔧 常用命令

```bash
# 开发环境
./dev.sh                                    # 启动开发环境
docker compose -f docker-compose.dev.yml logs -f backend  # 查看后端日志
docker compose -f docker-compose.dev.yml down             # 停止服务

# 生产环境
./deploy.sh                                 # 部署/更新
docker compose logs -f                      # 查看所有日志
docker compose logs -f mailserver           # 查看邮件服务日志

# 数据库
docker compose exec backend alembic upgrade head          # 运行迁移
docker compose exec backend python -m initial.initial_data  # 初始化数据
```

---

## 📊 功能完成度

| 模块 | 状态 |
|------|------|
| 核心邮件功能 | ✅ 100% |
| 高级邮件功能 | ✅ 100% |
| 附件功能 | ✅ 100% |
| 会员订阅 | ✅ 100% |
| 用户系统 | ✅ 83% |
| 账号池 | ✅ 100% |
| 设置页面 | 🔄 70% |

---

## 📜 版权声明

```
Copyright © 2025 Talenting. All Rights Reserved.

本项目为私有项目，保留所有权利。
未经授权，禁止复制、修改、分发或使用本项目的任何部分。

作者: Zevan
```

---

<p align="center">
  <sub>Made with ❤️ by Zevan @ Talenting</sub>
</p>

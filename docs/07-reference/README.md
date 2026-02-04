# 参考资料

本目录包含项目的参考文档和资料。

## 📚 文档列表

- **[更新日志](./changelog.md)** - 版本更新记录
- **[术语表](./glossary.md)** - 技术术语解释（编写中）
- **[API 参考](./api-reference.md)** - API 端点详细文档（编写中）
- **[配置参考](./configuration.md)** - 配置文件说明（编写中）
- **[错误代码](./error-codes.md)** - 错误代码列表（编写中）

## 📋 快速参考

### 环境变量

关键环境变量说明：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `CURRENT_ENVIRONMENT` | 运行环境 | `development` |
| `SECRET_KEY` | JWT 密钥 | 必填 |
| `DATABASE_URL_DOCKER` | 数据库连接 | 必填 |
| `ADMIN_PASSWORD` | 管理员密码 | 必填 |

### 端口列表

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | Nuxt 开发服务器 |
| Backend | 8000 | FastAPI 服务 |
| Backend LMTP | 24 | 邮件接收 |
| PostgreSQL | 5432 | 数据库 |
| SMTP | 25, 587 | 邮件发送 |
| IMAP | 143, 993 | 邮件接收 |
| HTTP/HTTPS | 80, 443 | Web 访问 |

### 目录结构

```
talentmail/
├── backend/        # 后端代码
├── frontend/       # 前端代码
├── config/         # 配置文件
├── scripts/        # 工具脚本
├── docs/          # 文档目录
├── data/          # 数据存储
└── tests/         # 测试代码
```

## 🔗 外部资源

### 技术文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Nuxt 3 文档](https://nuxt.com/)
- [Vue 3 文档](https://vuejs.org/)
- [Docker 文档](https://docs.docker.com/)

### 使用的库
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Vue Flow](https://vueflow.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

## 🛠️ 开发工具

### 推荐工具
- **Postman** - API 测试
- **TablePlus** - 数据库管理
- **Docker Desktop** - 容器管理
- **Git Kraken** - Git GUI

### VS Code 扩展
```json
{
  "recommendations": [
    "ms-python.python",
    "Vue.volar",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens"
  ]
}
```

## 📖 技术决策

### 为什么选择 FastAPI？
- 高性能
- 自动 API 文档
- 类型安全
- 现代 Python

### 为什么选择 Nuxt 3？
- SSR 支持
- Vue 3 生态
- 优秀的 DX
- 内置优化

### 为什么选择 PostgreSQL？
- 成熟稳定
- JSON 支持
- 全文搜索
- 事务支持

## 🔍 常见问题

### Q: 如何重置管理员密码？
A: 参考[故障排查文档](../05-operations/troubleshooting.md#登录认证问题)

### Q: 如何备份数据？
A: 使用 `pg_dump` 备份数据库，参考运维文档

### Q: 支持哪些邮件协议？
A: SMTP, IMAP, POP3（通过 IMAP 模拟）

### Q: 可以使用外部邮件服务器吗？
A: 目前仅支持内置的 docker-mailserver

## 📝 版本历史

### v1.5.0 (当前)
- 添加 PWA 支持
- 工作流系统
- 模板系统
- 更新日志功能

### v1.0.0
- 核心邮件功能
- 用户系统
- 基础 UI

详细更新历史请查看 [CHANGELOG.md](./changelog.md)

---

最后更新：2025-02-01
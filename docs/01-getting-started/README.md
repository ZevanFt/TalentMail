# 快速开始指南

欢迎使用 TalentMail！本指南将帮助你快速了解和部署项目。

## 🎯 选择你的路径

### 👨‍💻 我是开发者
想要在本地搭建开发环境？

➡️ **[开发环境部署指南](./development.md)**

只需一个命令即可启动完整的开发环境：
```bash
./dev.sh
```

### 🚀 我要部署到生产环境
准备将 TalentMail 部署到服务器？

➡️ **[生产环境部署指南](./production.md)**

包含完整的服务器配置、域名设置和 SSL 证书配置。

## ⚡ 超快速开始（3分钟）

### 前置条件
- Docker 和 Docker Compose 已安装
- Git 已安装

### 开发环境快速部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd talentmail

# 2. 启动开发环境
chmod +x dev.sh
./dev.sh

# 3. 访问应用
# 打开浏览器访问: http://localhost:3000
# 默认账号: admin@talenting.test / adminpassword
```

就这么简单！

## 📚 接下来做什么？

### 了解项目
- 📖 阅读[项目 README](../../README.md) 了解功能特性
- 🏗️ 查看[系统架构](../02-architecture/system-design.md)理解技术栈
- 📋 查看[待办事项](../06-roadmap/todo-list.md)了解开发计划

### 开始开发
- 💻 阅读[开发指南](../04-development/README.md)
- 🧪 学习[测试指南](../04-development/testing-guide.md)
- 🔧 遇到问题？查看[故障排查](../05-operations/troubleshooting.md)

### 深入功能
- 📧 [邮件系统文档](../03-features/email-system.md)
- 🔄 [工作流系统文档](../03-features/workflow-system.md)
- 📝 [模板系统文档](../03-features/template-system.md)

## 🆘 需要帮助？

- **文档问题**：在项目仓库提交 Issue
- **技术问题**：查看[故障排查指南](../05-operations/troubleshooting.md)
- **功能建议**：查看[待办事项](../06-roadmap/todo-list.md)并提交建议

## 🎉 准备好了吗？

选择适合你的指南开始吧：
- 🔨 [开发环境部署](./development.md) - 本地开发
- 🌐 [生产环境部署](./production.md) - 线上部署

---

祝你使用愉快！🚀
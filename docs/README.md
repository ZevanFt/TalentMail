# TalentMail 文档中心

欢迎来到 TalentMail 项目文档中心！这里是所有项目相关文档的集中管理地。

## 📚 文档目录结构

```
docs/
├── README.md                 # 文档中心索引（本文件）
├── 01-getting-started/       # 快速开始
│   ├── README.md            # 快速开始概览
│   ├── development.md       # 开发环境部署
│   └── production.md        # 生产环境部署
├── 02-architecture/         # 架构设计
│   ├── README.md           # 架构概览
│   ├── system-design.md    # 系统设计
│   ├── database-schema.md  # 数据库设计
│   └── api-design.md       # API 设计
├── 03-features/            # 功能文档
│   ├── README.md          # 功能概览
│   ├── email-system.md    # 邮件系统
│   ├── workflow-system.md # 工作流系统
│   ├── template-system.md # 模板系统
│   └── automation.md      # 自动化功能
├── 04-development/         # 开发指南
│   ├── README.md          # 开发指南概览
│   ├── coding-standards.md # 编码规范
│   ├── testing-guide.md   # 测试指南
│   └── debugging.md       # 调试技巧
├── 05-operations/          # 运维指南
│   ├── README.md          # 运维概览
│   ├── deployment.md      # 部署指南
│   ├── monitoring.md      # 监控配置
│   └── troubleshooting.md # 故障排查
├── 06-roadmap/            # 项目规划
│   ├── README.md         # 规划概览
│   ├── current-tasks.md  # 当前任务
│   ├── todo-list.md      # 待办事项
│   └── future-plans.md   # 未来计划
└── 07-reference/          # 参考资料
    ├── README.md         # 参考概览
    ├── changelog.md      # 更新日志
    └── glossary.md       # 术语表
```

## 🚀 快速链接

### 新手必读
- [🎯 快速开始指南](./01-getting-started/README.md)
- [🔧 开发环境部署](./01-getting-started/development.md)
- [📋 当前任务列表](./06-roadmap/current-tasks.md)

### 核心文档
- [🏗️ 系统架构设计](./02-architecture/system-design.md)
- [📧 邮件系统文档](./03-features/email-system.md)
- [🔄 工作流系统文档](./03-features/workflow-system.md)

### 开发者资源
- [💻 开发指南](./04-development/README.md)
- [🧪 测试指南](./04-development/testing-guide.md)
- [🐛 故障排查](./05-operations/troubleshooting.md)

### 故障排查记录
- [邮件投递修复 - dual-deliver 链路断裂](./troubleshooting/mail-delivery-fix.md) (2026-03-03)
- [空白页面问题 - CSS/HTTPS](./troubleshooting/CURRENT_ISSUE_SUMMARY.md) (2026-02-07)

## 📝 文档维护说明

1. **文档命名规范**：使用小写字母和连字符，如 `system-design.md`
2. **更新要求**：每次功能更新后，必须同步更新相关文档
3. **审核流程**：重要文档修改需要代码审核
4. **版本管理**：文档变更记录在 `changelog.md` 中

## 🤝 贡献指南

欢迎贡献文档！请遵循以下步骤：
1. Fork 项目仓库
2. 创建文档分支 `docs/your-feature`
3. 提交 Pull Request
4. 等待审核合并

---

最后更新时间：2026-03-03
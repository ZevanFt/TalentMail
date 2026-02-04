# 开发指南

欢迎参与 TalentMail 项目开发！本目录包含开发相关的指南和规范。

## 📚 文档列表

- **[编码规范](./coding-standards.md)** ⭐ - **核心开发原则和编码标准（必读）**
- **[测试指南](./testing-guide.md)** - 如何编写和运行测试
- **[调试技巧](./debugging.md)** - 开发环境调试方法（编写中）
- **[API 开发](./api-development.md)** - 后端 API 开发指南（编写中）
- **[前端开发](./frontend-development.md)** - Vue/Nuxt 开发指南（编写中）

## 🚀 快速开始

### 1. 环境准备

确保你已经按照[开发环境部署指南](../01-getting-started/development.md)搭建好本地环境。

### 2. 开发流程

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **开发功能**
   - 遵循编码规范
   - 编写单元测试
   - 本地测试通过

3. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加新功能"
   git push origin feature/your-feature-name
   ```

4. **创建 PR**
   - 填写 PR 模板
   - 等待代码审查
   - 合并到主分支

## 💻 技术栈详解

### 后端技术
- **FastAPI**: 现代 Python Web 框架
- **SQLAlchemy**: ORM 框架
- **Pydantic**: 数据验证
- **Alembic**: 数据库迁移
- **pytest**: 测试框架

### 前端技术
- **Nuxt 3**: Vue.js 框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 样式框架
- **Pinia**: 状态管理
- **Vite**: 构建工具

## 🛠️ 开发工具

### 推荐的 IDE
- **VS Code** - 配置推荐插件
  - Python
  - Volar (Vue)
  - Tailwind CSS IntelliSense
  - Docker
  - GitLens

### 有用的命令

**后端开发**
```bash
# 进入后端容器
docker-compose -f docker-compose.dev.yml exec backend bash

# 运行测试
pytest

# 创建数据库迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head
```

**前端开发**
```bash
# 进入前端容器
docker-compose -f docker-compose.dev.yml exec frontend sh

# 安装依赖
npm install

# 类型检查
npm run typecheck

# 代码检查
npm run lint
```

## 📝 代码规范概要

### Python 代码
- 使用 Black 格式化
- 遵循 PEP 8
- 类型注解必须
- docstring 必须

### TypeScript/Vue 代码
- 使用 Prettier 格式化
- ESLint 规则
- 组合式 API
- TypeScript 严格模式

### Git 提交
- 使用语义化提交信息
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试相关

## 🧪 测试要求

### 单元测试
- 新功能必须有测试
- 测试覆盖率 > 80%
- 使用 pytest 和 vitest

### 集成测试
- API 端点测试
- 数据库操作测试
- 前后端集成测试

### E2E 测试
- 关键用户流程
- 使用 Playwright（计划中）

## 🐛 调试技巧

### 后端调试
```python
# 使用 print 调试
print(f"Debug: {variable}")

# 使用 pdb
import pdb; pdb.set_trace()

# 使用日志
import logging
logging.info(f"Info: {data}")
```

### 前端调试
```typescript
// 使用 console
console.log('Debug:', data)

// Vue Devtools
// 浏览器扩展自动启用

// 网络请求调试
// 使用浏览器开发者工具
```

## 📦 常用包和库

### 后端常用
- `httpx` - HTTP 客户端
- `celery` - 异步任务（计划）
- `redis` - 缓存（计划）
- `sentry-sdk` - 错误追踪

### 前端常用
- `@vueuse/core` - Vue 组合式工具
- `dayjs` - 日期处理
- `axios` - HTTP 客户端
- `lodash-es` - 工具函数

## 🤝 贡献指南

1. **Fork 项目**
2. **创建特性分支**
3. **编写代码和测试**
4. **提交 Pull Request**
5. **代码审查**
6. **合并**

详细的贡献指南请查看项目根目录的 CONTRIBUTING.md（编写中）。

## 📞 获取帮助

- 查看现有 Issues
- 加入开发者讨论
- 查阅技术文档
- 联系项目维护者

---

最后更新：2025-02-01
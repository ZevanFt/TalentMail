# 工作流系统文档

> 最后更新：2026-02-06

## 概述

TalentMail 工作流系统是一个可视化的自动化引擎，允许用户通过拖拽节点和连接边的方式创建邮件处理自动化流程。系统支持多种触发器、逻辑控制、邮件操作和集成功能。

## 架构

### 技术栈

- **前端**: Vue 3 + Vue Flow（可视化流程编辑器）
- **后端**: FastAPI + SQLAlchemy
- **数据库**: PostgreSQL

### 核心模型

| 模型 | 文件 | 说明 |
|------|------|------|
| `Workflow` | `backend/db/models/workflow.py` | 工作流主表 |
| `WorkflowNode` | `backend/db/models/workflow.py` | 工作流节点 |
| `WorkflowEdge` | `backend/db/models/workflow.py` | 节点连接边 |
| `WorkflowVersion` | `backend/db/models/workflow.py` | 版本历史快照 |
| `NodeType` | `backend/db/models/workflow.py` | 节点类型定义 |
| `WorkflowExecution` | `backend/db/models/workflow.py` | 执行记录 |
| `NodeExecution` | `backend/db/models/workflow.py` | 节点执行记录 |

## 功能状态

### ✅ 已完成功能

#### 1. 可视化编辑器
- **文件**: `frontend/app/pages/workflows/[id].vue`
- **功能**:
  - 拖拽节点到画布
  - 连接节点创建边
  - 节点配置面板
  - 缩放和平移画布
  - 小地图导航
  - SSR 禁用（避免服务端渲染问题）

#### 2. 节点类型系统
- **API**: `GET /api/workflows/node-types`
- **分类**:
  - `trigger` - 触发器节点（邮件接收、定时、手动等）
  - `logic` - 逻辑控制（条件分支、过滤器、延时等）
  - `email_action` - 邮件动作（发送、回复、转发）
  - `email_operation` - 邮件处理（移动、标记、归档）
  - `data` - 数据处理（验证、提取、用户操作）
  - `integration` - 集成（Webhook、API 调用）
  - `end` - 结束节点

#### 3. 触发器选择弹窗
- **功能**: 新建工作流时，弹窗让用户选择触发器类型
- **位置**: 编辑器页面初始化时自动显示
- **触发器类型**:
  - 邮件接收触发器 (`trigger_email_received`)
  - 定时触发器 (`trigger_schedule`)
  - 手动触发器 (`trigger_manual`)
  - Webhook 触发器 (`trigger_webhook`)
  - 用户注册触发器 (`trigger_user_registered`)
  - 等...

#### 4. 保存功能
- **API**: `PUT /api/workflows/{id}/canvas`
- **修复历史**:
  - 扩展 `node_id` 字段长度：50 → 100 字符
  - 扩展 `edge_id` 字段长度：50 → 150 字符
  - 修复 `router.replace()` 导致组件重载问题，改用 `window.history.replaceState()`

#### 5. 版本历史
- **数据库表**: `workflow_versions`
- **API**:
  - `GET /api/workflows/{id}/versions` - 获取版本列表
  - `GET /api/workflows/{id}/versions/{version}` - 获取版本详情
  - `POST /api/workflows/{id}/versions/{version}/restore` - 恢复版本
- **前端功能**:
  - 历史按钮（工具栏）
  - 版本列表弹窗
  - 预览模式（在画布上显示历史版本）
  - 恢复功能（创建新版本记录）

#### 6. 工作流设置面板
- **功能**:
  - 编辑工作流名称和描述
  - 添加全局配置项
  - 配置项绑定到节点字段

### 🚧 待完成功能

#### 1. 工作流运行时
- **文件**: `backend/core/workflow_runtime.py`
- **状态**: 框架已搭建，需要完善节点执行逻辑
- **待实现**:
  - 各类节点的具体执行逻辑
  - 上下文变量传递
  - 错误处理和重试机制

#### 2. 条件分支节点
- **状态**: UI 已支持双输出端口（是/否）
- **待实现**: 条件表达式解析和执行

#### 3. 邮件触发集成
- **文件**: `backend/core/lmtp_server.py`
- **状态**: LMTP 服务器已集成邮件接收
- **待实现**: 触发工作流执行

#### 4. 定时任务调度
- **待实现**: 定时触发器的调度系统

#### 5. 工作流模板
- **数据库表**: `workflow_templates`
- **状态**: 表结构已创建
- **待实现**: 模板市场 UI 和使用功能

## API 参考

### 工作流 CRUD

```
POST   /api/workflows/                    # 创建工作流
GET    /api/workflows/                    # 获取工作流列表
GET    /api/workflows/{id}                # 获取工作流详情
PUT    /api/workflows/{id}                # 更新工作流基本信息
DELETE /api/workflows/{id}                # 删除工作流
PUT    /api/workflows/{id}/canvas         # 保存画布（节点和边）
POST   /api/workflows/{id}/publish        # 发布工作流
```

### 版本历史

```
GET    /api/workflows/{id}/versions                    # 版本列表
GET    /api/workflows/{id}/versions/{version}          # 版本详情
POST   /api/workflows/{id}/versions/{version}/restore  # 恢复版本
```

### 节点类型

```
GET    /api/workflows/node-types           # 获取所有节点类型
GET    /api/workflows/node-types?category=trigger  # 按分类筛选
```

### 执行记录

```
GET    /api/workflows/executions                        # 执行记录列表
GET    /api/workflows/executions/{id}                   # 执行详情
```

## 数据库迁移

| 迁移文件 | 说明 |
|----------|------|
| `c7d8e9f0a1b2_add_workflow_tables.py` | 创建工作流基础表 |
| `b8c7d6e5f4a3_add_workflow_templates_tables.py` | 创建工作流模板表 |
| `d5e6f7a8b9c0_add_workflow_version_history.py` | 创建版本历史表 |
| `e7f8a9b0c1d2_expand_workflow_id_fields.py` | 扩展字段长度 |

## 前端组件

| 文件 | 说明 |
|------|------|
| `frontend/app/pages/workflows/[id].vue` | 工作流编辑器主页面 |
| `frontend/app/pages/workflows/index.vue` | 工作流列表页面 |
| `frontend/app/pages/workflows/tutorial.vue` | 工作流教程页面 |
| `frontend/app/components/workflow/TemplateSelector.vue` | 模板选择器组件 |

## 配置说明

### 页面元数据

```typescript
definePageMeta({
  layout: false,  // 全屏布局
  ssr: false      // 禁用 SSR（Vue Flow 不支持）
})
```

### 节点配置 Schema

节点类型定义包含 `config_schema`，使用 JSON Schema 格式描述配置项：

```json
{
  "type": "object",
  "properties": {
    "template_code": {
      "type": "string",
      "title": "邮件模板",
      "description": "选择要发送的邮件模板"
    },
    "delay_seconds": {
      "type": "integer",
      "title": "延迟时间",
      "default": 0,
      "minimum": 0
    }
  },
  "required": ["template_code"]
}
```

## 已知问题

1. **预览模式退出**: 关闭版本历史弹窗时需要手动退出预览模式
2. **大型工作流性能**: 节点过多时可能影响编辑器性能
3. **节点 ID 长度**: 虽已扩展到 100-150 字符，复杂工作流仍需注意

## 下一步计划

1. 完善工作流运行时，实现各类节点的执行逻辑
2. 集成邮件接收触发器，实现自动化流程
3. 添加定时任务调度器
4. 完善工作流模板市场
5. 添加工作流执行日志和监控
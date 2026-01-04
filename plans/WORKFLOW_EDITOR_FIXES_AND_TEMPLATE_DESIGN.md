# 工作流编辑器修复 & 模板系统设计

## 目录
1. [问题分析](#问题分析)
2. [修复方案](#修复方案)
3. [工作流模板系统设计](#工作流模板系统设计)
4. [实施计划](#实施计划)

---

## 问题分析

### 🔴 问题 1：节点无法连接（严重）

**现象描述**：
- 将节点拖拽到画布后，无法在节点边缘看到连接点
- 无法通过拖拽创建节点之间的连线

**根本原因**：
自定义节点模板中 **缺少 Vue Flow 的 Handle 组件**

**当前代码** ([frontend/app/pages/workflows/[id].vue:668-682](frontend/app/pages/workflows/[id].vue)):
```vue
<template #node-custom="{ data }">
  <div class="px-4 py-3 rounded-xl shadow-lg border-2 min-w-[160px]"
       :style="{ backgroundColor: data.color + '20', borderColor: data.color }">
    <div class="flex items-center gap-2">
      <component :is="getIconComponent(data.icon)" class="w-5 h-5" :style="{ color: data.color }" />
      <span class="font-medium text-gray-800 dark:text-white text-sm">{{ data.label }}</span>
    </div>
  </div>
  <!-- ❌ 缺少 Handle 组件！ -->
</template>
```

**Vue Flow Handle 组件说明**：
- `Handle` 是 Vue Flow 提供的连接点组件
- 必须在自定义节点模板中显式添加
- 支持 `type="source"` (输出) 和 `type="target"` (输入)
- 支持 `position` 属性控制位置 (Top/Bottom/Left/Right)

---

### 🔴 问题 2：系统工作流配置无法修改

**现象描述**：
- 系统工作流页面打开后，右侧配置面板无法保存修改

**可能原因**：
1. 系统工作流使用只读模式加载
2. 保存 API 没有实现系统工作流的配置更新
3. 前端没有调用保存接口

**需要检查的代码**：
- [backend/api/workflows.py](backend/api/workflows.py) - 系统工作流 API
- [frontend/app/pages/workflows/[id].vue](frontend/app/pages/workflows/[id].vue) - 保存逻辑

---

### 🟡 问题 3：节点配置项与实际不匹配

**现象描述**：
- 某些节点类型的 config_schema 定义了配置项，但在 UI 中无法正常显示或使用

**需要进一步排查**：
- 对比 [backend/initial/init_workflow_data.py](backend/initial/init_workflow_data.py) 中的 config_schema
- 与前端配置面板的渲染逻辑

---

## 修复方案

### 方案 1：添加 Handle 组件（节点连接）

**修改文件**: `frontend/app/pages/workflows/[id].vue`

**修改步骤**：

1. **导入 Handle 和 Position**:
```typescript
import { VueFlow, useVueFlow, Panel, MarkerType, Handle, Position } from '@vue-flow/core'
```

2. **修改自定义节点模板**:
```vue
<template #node-custom="{ data }">
  <!-- 输入连接点（顶部） -->
  <Handle
    type="target"
    :position="Position.Top"
    class="!w-3 !h-3 !bg-gray-400 !border-2 !border-white dark:!border-gray-800"
  />
  
  <!-- 节点主体 -->
  <div
    class="px-4 py-3 rounded-xl shadow-lg border-2 min-w-[160px] transition-shadow hover:shadow-xl"
    :style="{
      backgroundColor: data.color + '20',
      borderColor: data.color
    }"
  >
    <div class="flex items-center gap-2">
      <component :is="getIconComponent(data.icon)" class="w-5 h-5" :style="{ color: data.color }" />
      <span class="font-medium text-gray-800 dark:text-white text-sm">{{ data.label }}</span>
    </div>
  </div>
  
  <!-- 输出连接点（底部） -->
  <Handle
    type="source"
    :position="Position.Bottom"
    class="!w-3 !h-3 !bg-gray-400 !border-2 !border-white dark:!border-gray-800"
  />
</template>
```

3. **处理条件分支节点的多输出端口**：

对于如"条件分支"这样有多个输出的节点，需要根据 `output_ports` 配置动态生成多个 Handle：

```vue
<template #node-custom="{ data }">
  <Handle type="target" :position="Position.Top" />
  
  <div class="...">...</div>
  
  <!-- 默认单输出 -->
  <Handle
    v-if="!data.outputPorts || data.outputPorts.length === 0"
    type="source"
    :position="Position.Bottom"
  />
  
  <!-- 多输出端口（条件分支） -->
  <template v-else>
    <Handle
      v-for="(port, index) in data.outputPorts"
      :key="port.id"
      type="source"
      :id="port.id"
      :position="Position.Bottom"
      :style="{ left: `${((index + 1) / (data.outputPorts.length + 1)) * 100}%` }"
    />
  </template>
</template>
```

---

### 方案 2：系统工作流配置保存

**需要实现**：
1. 后端 API：`PUT /api/system-workflows/{code}/config`
2. 前端保存按钮：针对系统工作流调用不同的 API

---

## 工作流模板系统设计

### 数据库设计

#### 表 1: workflow_templates（工作流模板）

```sql
CREATE TABLE workflow_templates (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(100) UNIQUE,          -- 模板代码（系统模板必填）
    name            VARCHAR(200) NOT NULL,        -- 模板名称
    name_en         VARCHAR(200),                 -- 英文名称
    description     TEXT,                         -- 模板描述
    category        VARCHAR(50) NOT NULL,         -- 分类: email/notification/organization/integration
    icon            VARCHAR(50),                  -- Lucide 图标名
    preview_image   VARCHAR(500),                 -- 预览图 URL
    
    -- 来源
    source_type     VARCHAR(20) NOT NULL DEFAULT 'system',  -- 来源: system/user
    source_user_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- 流程定义（与 SystemWorkflow 结构相同）
    nodes           JSONB NOT NULL DEFAULT '[]',
    edges           JSONB NOT NULL DEFAULT '[]',
    config_schema   JSONB,                        -- 可配置项的 JSON Schema
    default_config  JSONB DEFAULT '{}',
    
    -- 统计
    use_count       INTEGER DEFAULT 0,            -- 使用次数
    
    -- 状态
    is_featured     BOOLEAN DEFAULT FALSE,        -- 是否推荐
    is_active       BOOLEAN DEFAULT TRUE,
    
    -- 审核（用户分享的模板需要审核）
    review_status   VARCHAR(20) DEFAULT 'pending', -- pending/approved/rejected
    reviewed_at     TIMESTAMPTZ,
    reviewed_by     INTEGER REFERENCES users(id),
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_workflow_templates_category ON workflow_templates(category);
CREATE INDEX idx_workflow_templates_source_type ON workflow_templates(source_type);
CREATE INDEX idx_workflow_templates_is_featured ON workflow_templates(is_featured);
```

#### 表 2: workflow_template_tags（模板标签）

```sql
CREATE TABLE workflow_template_tags (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL UNIQUE,
    name_en         VARCHAR(50),
    color           VARCHAR(20),
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 模板-标签关联表
CREATE TABLE workflow_template_tag_relations (
    template_id     INTEGER REFERENCES workflow_templates(id) ON DELETE CASCADE,
    tag_id          INTEGER REFERENCES workflow_template_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (template_id, tag_id)
);
```

#### 表 3: workflow_template_favorites（用户收藏）

```sql
CREATE TABLE workflow_template_favorites (
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    template_id     INTEGER REFERENCES workflow_templates(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, template_id)
);
```

---

### 预设模板分类

| 分类 | 代码 | 图标 | 示例模板 |
|------|------|------|----------|
| 📧 邮件处理 | email | Mail | 自动回复、智能转发、垃圾邮件处理 |
| 🔔 通知提醒 | notification | Bell | VIP客户提醒、重要邮件通知 |
| 📁 自动整理 | organization | FolderInput | 自动归档、标签自动添加、定时清理 |
| 🔗 外部集成 | integration | Link | Webhook通知、第三方同步 |

---

### 预设模板列表

#### 1. 自动回复模板
```json
{
  "code": "auto_reply_basic",
  "name": "基础自动回复",
  "category": "email",
  "icon": "Reply",
  "description": "收到邮件后自动发送回复，适合休假或工作繁忙时使用",
  "nodes": [
    {"node_id": "trigger", "node_type": "trigger", "node_subtype": "trigger_email_received"},
    {"node_id": "reply", "node_type": "email_action", "node_subtype": "action_reply", "config": {"template_code": "auto_reply"}}
  ],
  "edges": [
    {"source_node_id": "trigger", "target_node_id": "reply"}
  ]
}
```

#### 2. VIP客户优先处理
```json
{
  "code": "vip_priority",
  "name": "VIP客户优先处理",
  "category": "notification",
  "icon": "Star",
  "description": "当VIP客户发送邮件时，自动标记星标并发送通知",
  "nodes": [
    {"node_id": "trigger", "node_type": "trigger", "node_subtype": "trigger_email_received"},
    {"node_id": "check_vip", "node_type": "logic", "node_subtype": "logic_condition", "config": {"conditions": [{"field": "sender_email", "operator": "contains", "value": "@vip.com"}]}},
    {"node_id": "mark_star", "node_type": "email_operation", "node_subtype": "operation_mark_starred"},
    {"node_id": "notify", "node_type": "integration", "node_subtype": "integration_notify"}
  ],
  "edges": [
    {"source_node_id": "trigger", "target_node_id": "check_vip"},
    {"source_node_id": "check_vip", "target_node_id": "mark_star", "source_handle": "true"},
    {"source_node_id": "mark_star", "target_node_id": "notify"}
  ]
}
```

#### 3. 邮件自动归档
```json
{
  "code": "auto_archive",
  "name": "邮件自动归档",
  "category": "organization",
  "icon": "Archive",
  "description": "根据发件人或主题自动将邮件归档到指定文件夹"
}
```

---

### 前端交互设计

#### 创建工作流弹窗

```
┌─────────────────────────────────────────────────────────────┐
│  创建工作流                                            [×] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [空白工作流]  从零开始，自由设计流程                        │
│                                                             │
│  ─────────── 或选择模板 ───────────                         │
│                                                             │
│  [📧 邮件处理]  [🔔 通知]  [📁 整理]  [🔗 集成]  [⭐ 收藏]   │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ 自动回复  │  │ VIP优先  │  │ 自动归档  │                  │
│  │ [预览图]  │  │ [预览图]  │  │ [预览图]  │                  │
│  │ 使用:128  │  │ 使用:89   │  │ 使用:56   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                             │
│                              [取消]  [使用此模板]            │
└─────────────────────────────────────────────────────────────┘
```

---

## 实施计划

### 阶段 1：修复节点连接（紧急）
- [ ] 导入 Handle 和 Position 组件
- [ ] 修改自定义节点模板，添加输入/输出连接点
- [ ] 支持条件节点的多输出端口
- [ ] 测试节点连接功能

### 阶段 2：修复系统工作流配置
- [ ] 检查系统工作流保存 API
- [ ] 实现配置更新接口
- [ ] 前端绑定保存逻辑

### 阶段 3：工作流模板系统
- [ ] 创建数据库迁移文件
- [ ] 实现后端 CRUD API
- [ ] 实现前端模板选择弹窗
- [ ] 添加预设模板数据

### 阶段 4：模板增强功能
- [ ] 模板收藏功能
- [ ] 模板标签筛选
- [ ] 用户分享模板
- [ ] 模板预览图生成
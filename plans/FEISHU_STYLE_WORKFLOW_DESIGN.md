# 飞书风格自动化工作流设计方案

> 基于飞书审批工作流的设计理念，为 TalentMail 打造可视化自动化工作流系统
> 最后更新: 2026-01-02

---

## 一、飞书审批工作流核心特点分析

### 1.1 飞书工作流的设计亮点

| 特点 | 描述 | 对 TalentMail 的启示 |
|------|------|---------------------|
| **可视化画布** | 流程图式的拖拽编辑器，节点之间用线连接 | 采用类似的画布式设计 |
| **节点化设计** | 每个步骤是一个独立节点（触发器、条件、动作） | 将规则拆分为可组合的节点 |
| **分支逻辑** | 支持 IF/ELSE 条件分支，走不同路径 | 增加条件分支节点 |
| **并行执行** | 支持多个动作同时执行 | 添加并行节点支持 |
| **表单驱动** | 动态表单配置，字段可自定义 | 动作配置采用动态表单 |
| **实时预览** | 编辑时可预览流程效果 | 添加流程模拟功能 |
| **模板市场** | 预设的工作流模板，一键使用 | 创建工作流模板库 |
| **版本管理** | 支持版本回滚和历史查看 | 实现版本控制 |

### 1.2 飞书工作流的节点类型

```
┌─────────────────────────────────────────────────────────────────┐
│                     飞书工作流节点类型                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🟢 触发节点 (Trigger)                                           │
│  ├── 表单提交触发                                                │
│  ├── 定时触发                                                    │
│  ├── 事件触发                                                    │
│  └── Webhook 触发                                                │
│                                                                  │
│  🔵 条件节点 (Condition)                                         │
│  ├── 条件分支 (IF/ELSE)                                          │
│  ├── 多条件分支 (SWITCH)                                         │
│  └── 循环节点 (FOR EACH)                                         │
│                                                                  │
│  🟡 审批节点 (Approval) - 飞书特有                               │
│  ├── 单人审批                                                    │
│  ├── 多人会签                                                    │
│  ├── 多人或签                                                    │
│  └── 自动审批                                                    │
│                                                                  │
│  🟣 动作节点 (Action)                                            │
│  ├── 发送消息                                                    │
│  ├── 发送邮件                                                    │
│  ├── 更新数据                                                    │
│  ├── 调用 API                                                    │
│  ├── 创建任务                                                    │
│  └── 触发其他工作流                                              │
│                                                                  │
│  🔴 结束节点 (End)                                               │
│  ├── 正常结束                                                    │
│  ├── 拒绝结束                                                    │
│  └── 终止流程                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、TalentMail 飞书风格工作流设计

### 2.1 节点类型定义

针对邮件系统场景，我们定义以下节点类型：

```
┌─────────────────────────────────────────────────────────────────┐
│                   TalentMail 工作流节点类型                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🟢 触发节点 (Trigger) - 工作流入口                              │
│  ├── 📧 收到邮件                                                 │
│  ├── 📤 发送邮件                                                 │
│  ├── 👤 用户事件（注册/登录/修改密码）                           │
│  ├── ⏰ 定时触发                                                 │
│  ├── 🔗 Webhook 触发                                             │
│  └── 🖱️ 手动触发                                                 │
│                                                                  │
│  🔵 逻辑节点 (Logic) - 流程控制                                  │
│  ├── 🔀 条件分支 (IF/ELSE)                                       │
│  ├── 🔢 多条件分支 (SWITCH)                                      │
│  ├── ⏳ 延迟执行 (DELAY)                                         │
│  └── 🔄 并行执行 (PARALLEL)                                      │
│                                                                  │
│  🟡 邮件动作 (Email Actions)                                     │
│  ├── 📧 发送邮件                                                 │
│  ├── 📋 发送模板邮件                                             │
│  ├── ↩️ 回复邮件                                                 │
│  ├── ➡️ 转发邮件                                                 │
│  └── 📎 添加附件                                                 │
│                                                                  │
│  🟣 邮件处理 (Email Operations)                                  │
│  ├── 📁 移动到文件夹                                             │
│  ├── 🏷️ 添加/移除标签                                            │
│  ├── ⭐ 标记星标                                                  │
│  ├── ✅ 标记已读                                                  │
│  ├── 🗑️ 删除邮件                                                 │
│  └── 📦 归档邮件                                                 │
│                                                                  │
│  🔴 集成动作 (Integrations)                                      │
│  ├── 🌐 Webhook 调用                                             │
│  ├── 📝 记录日志                                                 │
│  ├── 🔔 发送通知                                                 │
│  └── ⚡ 触发其他工作流                                           │
│                                                                  │
│  ⚫ 结束节点 (End)                                               │
│  ├── ✅ 成功结束                                                 │
│  └── ❌ 失败结束                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 可视化画布设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  📋 工作流编辑器                                    [保存] [测试] [发布]    │
├────────────────────┬────────────────────────────────────────────────────────┤
│                    │                                                        │
│  📦 节点面板        │                    画布区域                            │
│  ─────────────     │                                                        │
│                    │     ┌─────────────┐                                    │
│  ▼ 触发器          │     │  🟢 触发器   │                                    │
│    📧 收到邮件     │     │  用户注册    │                                    │
│    👤 用户事件     │     └──────┬──────┘                                    │
│    ⏰ 定时触发     │            │                                           │
│                    │            ▼                                           │
│  ▼ 逻辑控制        │     ┌─────────────┐                                    │
│    🔀 条件分支     │     │  🔵 条件     │                                    │
│    ⏳ 延迟         │     │ 邮箱含@vip  │                                    │
│    🔄 并行         │     └──────┬──────┘                                    │
│                    │        ┌───┴───┐                                       │
│  ▼ 邮件动作        │        │       │                                       │
│    📋 发送模板     │    是 ▼       ▼ 否                                     │
│    ↩️ 回复         │  ┌────────┐ ┌────────┐                                 │
│    ➡️ 转发         │  │🟡VIP模板│ │🟡普通模板│                                │
│                    │  │ 发送   │ │  发送   │                                 │
│  ▼ 邮件处理        │  └───┬────┘ └────┬───┘                                 │
│    📁 移动文件夹   │      │           │                                     │
│    🏷️ 添加标签     │      └─────┬─────┘                                     │
│    ⭐ 星标         │            │                                           │
│                    │            ▼                                           │
│  ▼ 集成           │     ┌─────────────┐                                    │
│    🌐 Webhook     │     │  🟣 添加标签 │                                    │
│    📝 日志        │     │   新用户     │                                    │
│                    │     └──────┬──────┘                                    │
│                    │            │                                           │
│                    │            ▼                                           │
│                    │     ┌─────────────┐                                    │
│                    │     │  ⚫ 结束    │                                    │
│                    │     │   成功      │                                    │
│                    │     └─────────────┘                                    │
│                    │                                                        │
├────────────────────┴────────────────────────────────────────────────────────┤
│  节点配置面板（选中节点时显示）                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  📋 发送模板邮件                                                        │ │
│  │  ─────────────────────────────────────────────────────────────────     │ │
│  │  模板：[欢迎邮件 - VIP版 ▼]                                            │ │
│  │  发送给：● 触发用户  ○ 指定邮箱  ○ 管理员                              │ │
│  │  变量覆盖：                                                             │ │
│  │    user_name: [使用触发数据 ▼]                                         │ │
│  │    vip_level: [自定义值: 黄金会员]                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 条件分支节点详细设计

飞书的条件分支非常直观，我们采用类似设计：

```
┌─────────────────────────────────────────────────────────────────┐
│  🔀 条件分支配置                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  分支 1: VIP 用户                                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  当 [user_email ▼] [包含 ▼] [@vip.com          ]             │ │
│  │  并且 [subscription ▼] [不等于 ▼] [free           ]          │ │
│  │                                            [+ 添加条件]      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  分支 2: 企业用户                                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  当 [user_email ▼] [包含 ▼] [@company.com      ]             │ │
│  │                                            [+ 添加条件]      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [+ 添加分支]                                                    │
│                                                                  │
│  默认分支（以上条件都不满足时）:                                 │
│  ● 执行默认动作  ○ 跳过后续节点                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、数据库架构设计

### 3.1 节点定义表

```sql
-- 工作流定义表
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    scope VARCHAR(20) DEFAULT 'system',      -- system/personal
    category VARCHAR(50),                    -- 分类
    
    -- 状态
    status VARCHAR(20) DEFAULT 'draft',      -- draft/published/disabled
    is_active BOOLEAN DEFAULT FALSE,
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    published_version INTEGER,
    
    -- 统计
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 工作流节点表
CREATE TABLE workflow_nodes (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    
    -- 节点信息
    node_id VARCHAR(50) NOT NULL,            -- 前端生成的唯一 ID
    node_type VARCHAR(50) NOT NULL,          -- trigger/condition/action/end
    node_subtype VARCHAR(50) NOT NULL,       -- email_received/send_template/etc
    name VARCHAR(100),
    
    -- 位置信息（画布坐标）
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    
    -- 配置
    config JSONB DEFAULT '{}',
    
    -- 排序
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(workflow_id, node_id)
);

-- 工作流连接表（节点之间的连线）
CREATE TABLE workflow_edges (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    
    -- 连接信息
    edge_id VARCHAR(50) NOT NULL,            -- 前端生成的唯一 ID
    source_node_id VARCHAR(50) NOT NULL,     -- 源节点 ID
    target_node_id VARCHAR(50) NOT NULL,     -- 目标节点 ID
    source_handle VARCHAR(50),               -- 源节点的输出端口
    target_handle VARCHAR(50),               -- 目标节点的输入端口
    
    -- 条件分支时的标签
    label VARCHAR(100),                      -- 如 "是" / "否"
    condition_key VARCHAR(50),               -- 条件键，如 "branch_1"
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(workflow_id, edge_id)
);

-- 节点类型定义表
CREATE TABLE node_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,        -- email_received/send_template
    name VARCHAR(100) NOT NULL,              -- 收到邮件/发送模板邮件
    name_en VARCHAR(100),
    category VARCHAR(50) NOT NULL,           -- trigger/logic/email_action/etc
    icon VARCHAR(50),                        -- emoji 或图标名
    color VARCHAR(20),                       -- 节点颜色
    description TEXT,
    
    -- 端口定义
    input_ports JSONB DEFAULT '[]',          -- 输入端口
    output_ports JSONB DEFAULT '[]',         -- 输出端口
    
    -- 配置 Schema
    config_schema JSONB,                     -- JSON Schema
    
    -- 可用变量
    available_variables JSONB,
    output_variables JSONB,
    
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 工作流执行日志表
CREATE TABLE workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id),
    version INTEGER,
    
    -- 触发信息
    trigger_type VARCHAR(50),
    trigger_data JSONB,
    
    -- 执行状态
    status VARCHAR(20),                      -- running/success/failed/cancelled
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP,
    
    -- 执行结果
    result JSONB,
    error_message TEXT
);

-- 节点执行日志表
CREATE TABLE workflow_node_executions (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_id VARCHAR(50) NOT NULL,
    
    -- 执行信息
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    status VARCHAR(20),                      -- pending/running/success/failed/skipped
    
    -- 输入输出
    input_data JSONB,
    output_data JSONB,
    error_message TEXT
);
```

### 3.2 初始节点类型数据

```sql
-- 触发器节点
INSERT INTO node_types (code, name, category, icon, config_schema) VALUES
('trigger_email_received', '收到邮件', 'trigger', '📧', '{
  "type": "object",
  "properties": {
    "filter_sender": {"type": "string", "title": "发件人过滤"},
    "filter_subject": {"type": "string", "title": "主题过滤"}
  }
}'),
('trigger_user_event', '用户事件', 'trigger', '👤', '{
  "type": "object",
  "properties": {
    "event_type": {
      "type": "string",
      "title": "事件类型",
      "enum": ["user.registered", "user.login", "user.password_changed"],
      "enumNames": ["用户注册", "用户登录", "密码修改"]
    }
  },
  "required": ["event_type"]
}'),
('trigger_scheduled', '定时触发', 'trigger', '⏰', '{
  "type": "object",
  "properties": {
    "cron": {"type": "string", "title": "Cron 表达式"},
    "timezone": {"type": "string", "title": "时区", "default": "Asia/Shanghai"}
  },
  "required": ["cron"]
}'),
('trigger_webhook', 'Webhook 触发', 'trigger', '🔗', '{
  "type": "object",
  "properties": {
    "secret": {"type": "string", "title": "验证密钥"}
  }
}'),
('trigger_manual', '手动触发', 'trigger', '🖱️', '{}');

-- 逻辑节点
INSERT INTO node_types (code, name, category, icon, output_ports, config_schema) VALUES
('logic_condition', '条件分支', 'logic', '🔀', 
 '[{"id": "true", "label": "是"}, {"id": "false", "label": "否"}]',
 '{
  "type": "object",
  "properties": {
    "conditions": {
      "type": "array",
      "title": "条件列表",
      "items": {
        "type": "object",
        "properties": {
          "field": {"type": "string"},
          "operator": {"type": "string"},
          "value": {"type": "string"}
        }
      }
    }
  }
}'),
('logic_switch', '多条件分支', 'logic', '🔢', '[]', '{
  "type": "object",
  "properties": {
    "branches": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "conditions": {"type": "array"}
        }
      }
    }
  }
}'),
('logic_delay', '延迟执行', 'logic', '⏳', '[]', '{
  "type": "object",
  "properties": {
    "delay_value": {"type": "integer", "title": "延迟时间", "default": 5},
    "delay_unit": {
      "type": "string", 
      "title": "时间单位",
      "enum": ["seconds", "minutes", "hours", "days"],
      "default": "minutes"
    }
  }
}'),
('logic_parallel', '并行执行', 'logic', '🔄', '[]', '{}');

-- 邮件动作节点
INSERT INTO node_types (code, name, category, icon, config_schema) VALUES
('action_send_email', '发送邮件', 'email_action', '📧', '{
  "type": "object",
  "properties": {
    "to": {"type": "string", "title": "收件人"},
    "subject": {"type": "string", "title": "主题"},
    "body": {"type": "string", "title": "正文", "format": "html"}
  },
  "required": ["to", "subject", "body"]
}'),
('action_send_template', '发送模板邮件', 'email_action', '📋', '{
  "type": "object",
  "properties": {
    "template_code": {"type": "string", "title": "模板"},
    "to_type": {
      "type": "string",
      "title": "发送给",
      "enum": ["trigger_user", "fixed_email", "admin"],
      "enumNames": ["触发用户", "指定邮箱", "管理员"]
    },
    "to_email": {"type": "string", "title": "收件人邮箱"},
    "variables": {"type": "object", "title": "变量覆盖"}
  },
  "required": ["template_code", "to_type"]
}'),
('action_reply', '回复邮件', 'email_action', '↩️', '{
  "type": "object",
  "properties": {
    "body": {"type": "string", "title": "回复内容", "format": "html"}
  },
  "required": ["body"]
}'),
('action_forward', '转发邮件', 'email_action', '➡️', '{
  "type": "object",
  "properties": {
    "to": {"type": "string", "title": "转发给"}
  },
  "required": ["to"]
}');

-- 邮件处理节点
INSERT INTO node_types (code, name, category, icon, config_schema) VALUES
('operation_move_folder', '移动到文件夹', 'email_operation', '📁', '{
  "type": "object",
  "properties": {
    "folder": {"type": "string", "title": "目标文件夹"}
  },
  "required": ["folder"]
}'),
('operation_add_tag', '添加标签', 'email_operation', '🏷️', '{
  "type": "object",
  "properties": {
    "tag": {"type": "string", "title": "标签名"}
  },
  "required": ["tag"]
}'),
('operation_mark_starred', '标记星标', 'email_operation', '⭐', '{}'),
('operation_mark_read', '标记已读', 'email_operation', '✅', '{}'),
('operation_delete', '删除邮件', 'email_operation', '🗑️', '{}'),
('operation_archive', '归档邮件', 'email_operation', '📦', '{}');

-- 集成节点
INSERT INTO node_types (code, name, category, icon, config_schema) VALUES
('integration_webhook', 'Webhook 调用', 'integration', '🌐', '{
  "type": "object",
  "properties": {
    "url": {"type": "string", "title": "URL"},
    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
    "headers": {"type": "object"},
    "body": {"type": "object"}
  },
  "required": ["url", "method"]
}'),
('integration_log', '记录日志', 'integration', '📝', '{
  "type": "object",
  "properties": {
    "message": {"type": "string", "title": "日志内容"},
    "level": {"type": "string", "enum": ["info", "warning", "error"]}
  }
}'),
('integration_trigger_workflow', '触发其他工作流', 'integration', '⚡', '{
  "type": "object",
  "properties": {
    "workflow_id": {"type": "integer", "title": "目标工作流"},
    "pass_data": {"type": "boolean", "title": "传递当前数据"}
  }
}');

-- 结束节点
INSERT INTO node_types (code, name, category, icon, config_schema) VALUES
('end_success', '成功结束', 'end', '✅', '{}'),
('end_failure', '失败结束', 'end', '❌', '{
  "type": "object",
  "properties": {
    "error_message": {"type": "string", "title": "错误信息"}
  }
}');
```

---

## 四、前端技术方案

### 4.1 技术选型

采用 **Vue Flow** 作为画布引擎，它是一个基于 Vue 3 的流程图库：

```bash
npm install @vue-flow/core @vue-flow/background @vue-flow/controls @vue-flow/minimap
```

### 4.2 核心组件结构

```
frontend/app/components/workflow/
├── WorkflowEditor.vue        # 主编辑器组件
├── WorkflowCanvas.vue        # 画布组件（使用 Vue Flow）
├── NodePalette.vue           # 左侧节点面板
├── NodeConfig.vue            # 右侧节点配置面板
├── nodes/                    # 自定义节点组件
│   ├── TriggerNode.vue       # 触发器节点
│   ├── ConditionNode.vue     # 条件节点
│   ├── ActionNode.vue        # 动作节点
│   └── EndNode.vue           # 结束节点
├── forms/                    # 动态配置表单
│   ├── DynamicForm.vue       # 根据 JSON Schema 生成表单
│   ├── TemplateSelect.vue    # 模板选择器
│   └── VariableInput.vue     # 变量输入框
└── modals/
    ├── TestWorkflowModal.vue # 测试工作流弹窗
    └── VersionHistoryModal.vue # 版本历史弹窗
```

### 4.3 WorkflowCanvas 组件示例

```vue
<template>
  <VueFlow
    v-model="elements"
    :node-types="nodeTypes"
    :connection-mode="ConnectionMode.Loose"
    @connect="onConnect"
    @node-click="onNodeClick"
    class="workflow-canvas"
  >
    <Background />
    <Controls />
    <MiniMap />
    
    <!-- 自定义连接线样式 -->
    <template #edge-default="{ sourceX, sourceY, targetX, targetY }">
      <path
        :d="getSmoothStepPath({ sourceX, sourceY, targetX, targetY })"
        class="edge-path"
      />
    </template>
  </VueFlow>
</template>

<script setup>
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'

import TriggerNode from './nodes/TriggerNode.vue'
import ConditionNode from './nodes/ConditionNode.vue'
import ActionNode from './nodes/ActionNode.vue'
import EndNode from './nodes/EndNode.vue'

const nodeTypes = {
  trigger: TriggerNode,
  condition: ConditionNode,
  action: ActionNode,
  end: EndNode,
}

const elements = ref([])

const onConnect = (params) => {
  // 处理节点连接
}

const onNodeClick = (event, node) => {
  // 点击节点时显示配置面板
  emit('select-node', node)
}
</script>
```

### 4.4 自定义节点组件示例

```vue
<!-- TriggerNode.vue -->
<template>
  <div 
    class="workflow-node trigger-node"
    :class="{ selected: selected }"
  >
    <div class="node-header">
      <span class="node-icon">{{ nodeData.icon }}</span>
      <span class="node-title">{{ nodeData.name }}</span>
    </div>
    <div class="node-body">
      <div class="node-description">
        {{ nodeData.description || '点击配置触发条件' }}
      </div>
    </div>
    
    <!-- 输出端口 -->
    <Handle type="source" position="bottom" />
  </div>
</template>

<script setup>
import { Handle } from '@vue-flow/core'

const props = defineProps({
  data: Object,
  selected: Boolean,
})

const nodeData = computed(() => props.data || {})
</script>

<style scoped>
.trigger-node {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 12px;
  padding: 12px 16px;
  min-width: 180px;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.trigger-node.selected {
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px #10b981;
}
</style>
```

---

## 五、API 设计

### 5.1 工作流 CRUD

```yaml
# 工作流管理
GET    /api/workflows                      # 获取工作流列表
POST   /api/workflows                      # 创建工作流
GET    /api/workflows/{id}                 # 获取工作流详情（含节点和连接）
PUT    /api/workflows/{id}                 # 更新工作流
DELETE /api/workflows/{id}                 # 删除工作流
POST   /api/workflows/{id}/publish         # 发布工作流
POST   /api/workflows/{id}/disable         # 禁用工作流
POST   /api/workflows/{id}/duplicate       # 复制工作流

# 工作流版本
GET    /api/workflows/{id}/versions        # 获取版本历史
POST   /api/workflows/{id}/rollback/{ver}  # 回滚到指定版本

# 工作流测试
POST   /api/workflows/{id}/test            # 测试执行
GET    /api/workflows/{id}/test-data       # 获取测试数据模板

# 工作流执行
POST   /api/workflows/{id}/execute         # 手动执行
GET    /api/workflows/{id}/executions      # 获取执行历史
GET    /api/workflow-executions/{id}       # 获取执行详情

# 节点类型
GET    /api/workflows/node-types           # 获取所有节点类型
GET    /api/workflows/node-types/{code}    # 获取节点类型详情
```

### 5.2 请求/响应示例

```json
// POST /api/workflows
{
  "name": "新用户欢迎流程",
  "description": "用户注册后自动发送欢迎邮件",
  "nodes": [
    {
      "node_id": "trigger_1",
      "node_type": "trigger",
      "node_subtype": "trigger_user_event",
      "name": "用户注册",
      "position_x": 100,
      "position_y": 50,
      "config": {
        "event_type": "user.registered"
      }
    },
    {
      "node_id": "action_1",
      "node_type": "action",
      "node_subtype": "action_send_template",
      "name": "发送欢迎邮件",
      "position_x": 100,
      "position_y": 200,
      "config": {
        "template_code": "welcome_email",
        "to_type": "trigger_user"
      }
    },
    {
      "node_id": "end_1",
      "node_type": "end",
      "node_subtype": "end_success",
      "name": "完成",
      "position_x": 100,
      "position_y": 350,
      "config": {}
    }
  ],
  "edges": [
    {
      "edge_id": "edge_1",
      "source_node_id": "trigger_1",
      "target_node_id": "action_1"
    },
    {
      "edge_id": "edge_2",
      "source_node_id": "action_1",
      "target_node_id": "end_1"
    }
  ]
}
```

---

## 六、工作流引擎设计

### 6.1 执行引擎核心逻辑

```python
# backend/core/workflow_engine.py

class WorkflowEngine:
    """飞书风格的工作流执行引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.node_handlers = self._register_handlers()
    
    async def execute(
        self, 
        workflow_id: int, 
        trigger_data: Dict,
        user: Optional[User] = None
    ) -> WorkflowExecution:
        """执行工作流"""
        
        # 1. 加载工作流定义
        workflow = self._load_workflow(workflow_id)
        
        # 2. 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            version=workflow.version,
            trigger_data=trigger_data,
            status="running"
        )
        self.db.add(execution)
        self.db.flush()
        
        # 3. 构建执行图
        graph = self._build_execution_graph(workflow)
        
        # 4. 找到触发节点开始执行
        trigger_node = self._find_trigger_node(graph)
        
        # 5. 执行流程
        context = ExecutionContext(
            data=trigger_data,
            user=user,
            execution_id=execution.id
        )
        
        try:
            await self._execute_node(trigger_node, graph, context)
            execution.status = "success"
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
        
        execution.finished_at = datetime.utcnow()
        self.db.commit()
        
        return execution
    
    async def _execute_node(
        self, 
        node: WorkflowNode, 
        graph: Dict, 
        context: ExecutionContext
    ):
        """执行单个节点"""
        
        # 记录节点执行开始
        node_execution = WorkflowNodeExecution(
            execution_id=context.execution_id,
            node_id=node.node_id,
            started_at=datetime.utcnow(),
            status="running",
            input_data=context.data
        )
        self.db.add(node_execution)
        
        try:
            # 获取节点处理器
            handler = self.node_handlers.get(node.node_subtype)
            if not handler:
                raise ValueError(f"Unknown node type: {node.node_subtype}")
            
            # 执行节点
            result = await handler(node.config, context)
            
            # 记录执行结果
            node_execution.status = "success"
            node_execution.output_data = result
            node_execution.finished_at = datetime.utcnow()
            
            # 更新上下文
            context.data.update(result.get("output", {}))
            
            # 确定下一个节点
            next_nodes = self._get_next_nodes(node, graph, result)
            
            # 执行后续节点
            for next_node in next_nodes:
                await self._execute_node(next_node, graph, context)
                
        except Exception as e:
            node_execution.status = "failed"
            node_execution.error_message = str(e)
            node_execution.finished_at = datetime.utcnow()
            raise
    
    def _get_next_nodes(
        self, 
        current_node: WorkflowNode, 
        graph: Dict,
        result: Dict
    ) -> List[WorkflowNode]:
        """获取下一个要执行的节点"""
        
        edges = graph["edges"].get(current_node.node_id, [])
        
        if current_node.node_subtype == "logic_condition":
            # 条件节点：根据结果选择分支
            branch = "true" if result.get("condition_met") else "false"
            for edge in edges:
                if edge.source_handle == branch:
                    return [graph["nodes"][edge.target_node_id]]
            return []
        
        elif current_node.node_subtype == "logic_parallel":
            # 并行节点：返回所有后续节点
            return [graph["nodes"][edge.target_node_id] for edge in edges]
        
        else:
            # 普通节点：返回第一个后续节点
            if edges:
                return [graph["nodes"][edges[0].target_node_id]]
            return []
```

### 6.2 节点处理器注册

```python
def _register_handlers(self) -> Dict[str, Callable]:
    """注册节点处理器"""
    return {
        # 触发器
        "trigger_email_received": self._handle_trigger_email,
        "trigger_user_event": self._handle_trigger_user_event,
        "trigger_scheduled": self._handle_trigger_scheduled,
        "trigger_webhook": self._handle_trigger_webhook,
        "trigger_manual": self._handle_trigger_manual,
        
        # 逻辑
        "logic_condition": self._handle_condition,
        "logic_switch": self._handle_switch,
        "logic_delay": self._handle_delay,
        "logic_parallel": self._handle_parallel,
        
        # 邮件动作
        "action_send_email": self._handle_send_email,
        "action_send_template": self._handle_send_template,
        "action_reply": self._handle_reply,
        "action_forward": self._handle_forward,
        
        # 邮件处理
        "operation_move_folder": self._handle_move_folder,
        "operation_add_tag": self._handle_add_tag,
        "operation_mark_starred": self._handle_mark_starred,
        "operation_mark_read": self._handle_mark_read,
        "operation_delete": self._handle_delete,
        "operation_archive": self._handle_archive,
        
        # 集成
        "integration_webhook": self._handle_webhook,
        "integration_log": self._handle_log,
        "integration_trigger_workflow": self._handle_trigger_workflow,
        
        # 结束
        "end_success": self._handle_end_success,
        "end_failure": self._handle_end_failure,
    }
```

---

## 七、实施路线图

### 阶段一：基础架构（1周）

- [ ] 创建数据库迁移（workflows, workflow_nodes, workflow_edges, node_types）
- [ ] 实现工作流 CRUD API
- [ ] 初始化节点类型数据
- [ ] 创建 WorkflowEngine 基础框架

### 阶段二：前端画布（2周）

- [ ] 集成 Vue Flow
- [ ] 实现节点面板（拖拽）
- [ ] 实现自定义节点组件
- [ ] 实现节点配置面板（动态表单）
- [ ] 实现保存/加载工作流

### 阶段三：节点处理器（1周）

- [ ] 实现所有触发器处理器
- [ ] 实现条件/分支处理器
- [ ] 实现邮件动作处理器
- [ ] 实现集成动作处理器

### 阶段四：测试与优化（1周）

- [ ] 工作流测试功能
- [ ] 执行日志可视化
- [ ] 版本控制
- [ ] 预设模板库

---

## 八、与现有系统的关系

### 8.1 兼容策略

| 现有组件 | 新组件 | 关系 |
|---------|--------|------|
| AutomationRule | Workflow | 并存，逐步迁移 |
| RuleEngine | WorkflowEngine | 并存，共享处理器 |
| AutomationLog | WorkflowExecution | 新增，更详细 |

### 8.2 迁移路径

1. **短期**：新的可视化工作流与现有规则系统并存
2. **中期**：提供迁移工具，将 AutomationRule 转换为 Workflow
3. **长期**：废弃旧的规则编辑器，统一使用可视化工作流

---

## 九、总结

飞书风格的工作流设计具有以下优势：

1. **直观可视化**：画布式编辑器，所见即所得
2. **灵活的分支**：支持条件分支、多分支、并行执行
3. **强大的扩展性**：节点类型可动态添加
4. **完整的日志**：每个节点的执行都有详细记录
5. **版本控制**：支持回滚和历史查看

这个设计将 TalentMail 的自动化能力提升到一个新的高度，让管理员能够像搭积木一样构建复杂的邮件自动化流程！
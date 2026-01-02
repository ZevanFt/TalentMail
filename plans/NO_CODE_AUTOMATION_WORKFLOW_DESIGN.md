# 无代码邮件自动化工作流设计方案

> 最后更新: 2026-01-01
> 版本: 2.0

---

## 一、当前系统分析

### 1.1 现有自动化规则系统

TalentMail 已实现完整的自动化规则引擎，核心组件包括：

| 组件 | 文件 | 功能 |
|------|------|------|
| RuleEngine | `backend/core/rule_engine.py` | 规则执行引擎 |
| EventPublisher | `backend/core/event_publisher.py` | 事件发布器 |
| AutomationRule | `backend/db/models/automation.py` | 规则数据模型 |
| AutomationLog | `backend/db/models/automation.py` | 执行日志模型 |

### 1.2 已支持的触发器类型

```python
class TriggerType:
    EMAIL_RECEIVED = "email_received"      # 收到邮件时触发
    EMAIL_SENT = "email_sent"              # 发送邮件时触发
    SCHEDULED = "scheduled"                # 定时触发（待实现）
    USER_EVENT = "user_event"              # 用户事件触发
    MANUAL = "manual"                      # 手动触发
```

### 1.3 已支持的条件操作符

```python
class ConditionOperator:
    EQUALS = "equals"                      # 等于
    NOT_EQUALS = "not_equals"              # 不等于
    CONTAINS = "contains"                  # 包含
    NOT_CONTAINS = "not_contains"          # 不包含
    STARTS_WITH = "starts_with"            # 以...开头
    ENDS_WITH = "ends_with"                # 以...结尾
    MATCHES_REGEX = "matches_regex"        # 正则匹配
    GREATER_THAN = "greater_than"          # 大于
    LESS_THAN = "less_than"                # 小于
    IS_EMPTY = "is_empty"                  # 为空
    IS_NOT_EMPTY = "is_not_empty"          # 不为空
    IN_LIST = "in_list"                    # 在列表中
    NOT_IN_LIST = "not_in_list"            # 不在列表中
```

### 1.4 已支持的动作类型

```python
class ActionType:
    SEND_EMAIL = "send_email"              # 发送邮件
    SEND_TEMPLATE_EMAIL = "send_template_email"  # 发送模板邮件 ✨
    FORWARD_EMAIL = "forward_email"        # 转发邮件
    REPLY_EMAIL = "reply_email"            # 回复邮件
    ADD_TAG = "add_tag"                    # 添加标签
    REMOVE_TAG = "remove_tag"              # 移除标签
    MOVE_TO_FOLDER = "move_to_folder"      # 移动到文件夹
    MARK_AS_READ = "mark_as_read"          # 标记已读
    MARK_AS_STARRED = "mark_as_starred"    # 标记星标
    DELETE_EMAIL = "delete_email"          # 删除邮件
    ARCHIVE_EMAIL = "archive_email"        # 归档邮件
    SET_VARIABLE = "set_variable"          # 设置变量
    LOG_MESSAGE = "log_message"            # 记录日志
    WEBHOOK = "webhook"                    # 调用 Webhook
```

### 1.5 已定义的系统事件

```python
class EventType:
    # 用户事件
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGIN_NEW_DEVICE = "user.login_new_device"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_SUBSCRIPTION_CHANGED = "user.subscription_changed"
    
    # 邮件事件
    EMAIL_RECEIVED = "email.received"
    EMAIL_SENT = "email.sent"
    EMAIL_BOUNCED = "email.bounced"
    EMAIL_OPENED = "email.opened"
    EMAIL_LINK_CLICKED = "email.link_clicked"
    
    # 文件事件
    FILE_UPLOADED = "drive.file_uploaded"
    FILE_SHARED = "drive.file_shared"
    FILE_DOWNLOADED = "drive.file_downloaded"
    
    # 管理事件
    INVITE_CREATED = "admin.invite_created"
    INVITE_USED = "admin.invite_used"
    USER_CREATED_BY_ADMIN = "admin.user_created"
    
    # 系统事件
    STORAGE_LIMIT_WARNING = "system.storage_limit_warning"
    SUBSCRIPTION_EXPIRING = "system.subscription_expiring"
```

---

## 二、用户分层设计

### 2.1 权限分离原则

```
┌─────────────────────────────────────────────────────────────────┐
│                      管理员专属功能                              │
├─────────────────────────────────────────────────────────────────┤
│  📧 系统邮件模板管理                                             │
│     • 创建/编辑/删除系统模板                                     │
│     • 配置模板变量                                               │
│     • 预览和测试模板                                             │
│                                                                  │
│  ⚡ 模板触发规则配置                                             │
│     • 系统事件 → 发送模板邮件                                    │
│     • 配置触发条件                                               │
│     • 设置发送目标                                               │
│                                                                  │
│  🌐 全局变量管理                                                 │
│     • 系统级变量（公司名、网站URL等）                            │
│                                                                  │
│  🔧 系统级自动化规则                                             │
│     • 影响所有用户的规则                                         │
│     • 系统通知规则                                               │
│                                                                  │
│  📊 执行日志和统计                                               │
│     • 查看所有规则执行记录                                       │
│     • 统计分析                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      普通用户功能                                │
├─────────────────────────────────────────────────────────────────┤
│  📬 个人邮件过滤规则                                             │
│     • 收到邮件 → 自动分类                                        │
│     • 收到邮件 → 自动标记                                        │
│     • 收到邮件 → 自动移动到文件夹                                │
│                                                                  │
│  ↩️ 个人自动回复设置                                             │
│     • 休假自动回复                                               │
│     • 特定发件人自动回复                                         │
│                                                                  │
│  ➡️ 个人邮件转发规则                                             │
│     • 条件转发到其他邮箱                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 前端入口设计

**管理员视角**：
```
设置 → 系统管理
├── 邮件模板          # EmailTemplates.vue
├── 自动化规则        # AutomationRules.vue（系统级）
├── 用户管理          # UserManagement.vue
├── 邀请码管理        # InviteCodes.vue
└── 订阅管理          # Billing.vue
```

**普通用户视角**：
```
设置 → 邮件设置
├── 邮件规则          # PersonalRules.vue（待开发）
│   ├── 过滤规则
│   ├── 自动回复
│   └── 转发规则
├── 签名管理
└── 通知设置
```

---

## 三、无代码工作流核心设计

### 3.1 设计目标

让非技术人员（管理员）能够通过可视化界面配置复杂的邮件自动化流程，无需编写任何代码。

### 3.2 关键设计原则

| 原则 | 说明 |
|------|------|
| **数据库驱动** | 所有配置存储在数据库中，而非代码 |
| **可视化编辑** | 拖拽式流程设计器 |
| **模块化组件** | 触发器、条件、动作都是可组合的模块 |
| **实时预览** | 配置时可预览效果 |
| **版本控制** | 支持规则版本回滚 |

### 3.3 数据库架构扩展

#### 阶段一：使用现有表（当前）

```sql
-- 现有表结构已满足基本需求
automation_rules:
  - id, name, description
  - owner_id, is_system, is_active
  - trigger_type, trigger_config (JSON)
  - conditions (JSON)
  - actions (JSON)
  - priority, execution_count, last_executed_at

automation_logs:
  - id, rule_id, trigger_type
  - trigger_data, conditions_matched
  - actions_executed, status, error_message
  - execution_time_ms, created_at
```

#### 阶段二：数据库驱动的类型定义（中期）

```sql
-- 事件类型定义表
CREATE TABLE event_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,      -- 如 'user.registered'
    name VARCHAR(100) NOT NULL,              -- 如 '用户注册成功'
    name_en VARCHAR(100),                    -- 英文名称
    category VARCHAR(50) NOT NULL,           -- 如 'user', 'email', 'system'
    category_label VARCHAR(50),              -- 如 '👤 用户事件'
    description TEXT,
    available_variables JSONB,               -- 可用变量列表
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT TRUE,          -- 系统内置 vs 用户自定义
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 动作类型定义表
CREATE TABLE action_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,      -- 如 'send_template_email'
    name VARCHAR(100) NOT NULL,              -- 如 '发送模板邮件'
    name_en VARCHAR(100),
    category VARCHAR(50) NOT NULL,           -- 如 'email', 'tag', 'folder'
    description TEXT,
    config_schema JSONB,                     -- 配置项的 JSON Schema
    handler_class VARCHAR(200),              -- 处理器类名
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 条件操作符定义表
CREATE TABLE condition_operators (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,       -- 如 'equals', 'contains'
    name VARCHAR(50) NOT NULL,               -- 如 '等于', '包含'
    name_en VARCHAR(50),
    description TEXT,
    applicable_types JSONB,                  -- 适用的数据类型
    sort_order INTEGER DEFAULT 0
);
```

#### 阶段三：增强版工作流表（长期）

```sql
-- 工作流定义表（增强版 AutomationRule）
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    
    -- 分类
    scope VARCHAR(20) DEFAULT 'system',      -- 'system' / 'personal'
    category VARCHAR(50),                    -- 'email_filter', 'notification', 'template_trigger'
    
    -- 触发器配置
    trigger_type VARCHAR(50) NOT NULL,
    trigger_event_id INTEGER REFERENCES event_types(id),
    trigger_config JSONB,
    
    -- 条件和动作
    conditions JSONB,
    actions JSONB,
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    
    -- 执行控制
    cooldown_seconds INTEGER DEFAULT 0,
    max_executions_per_day INTEGER,
    
    -- 统计
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP,
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    parent_version_id INTEGER REFERENCES workflows(id),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 工作流执行日志表
CREATE TABLE workflow_logs (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id),
    trigger_type VARCHAR(50),
    trigger_data JSONB,
    conditions_matched BOOLEAN,
    actions_executed JSONB,
    status VARCHAR(20),                      -- 'success', 'failed', 'skipped', 'partial'
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 四、前端可视化设计器

### 4.1 工作流编辑器界面

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📋 工作流编辑器 - 新用户欢迎邮件                              [保存] [测试] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ⚡ 触发器                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  当 [👤 用户事件 ▼] → [用户注册成功 ▼] 时                │    │   │
│  │  │                                                          │    │   │
│  │  │  📝 可用变量:                                            │    │   │
│  │  │  • {{user_name}} - 用户名                                │    │   │
│  │  │  • {{user_email}} - 邮箱地址                             │    │   │
│  │  │  • {{register_time}} - 注册时间                          │    │   │
│  │  │  • {{login_url}} - 登录链接                              │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🔍 条件 (可选)                                    [+ 添加条件]  │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  如果 [user_email ▼] [包含 ▼] [@company.com        ]    │    │   │
│  │  │                                              [× 删除]   │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  并且 [user_name ▼] [不为空 ▼] [                    ]   │    │   │
│  │  │                                              [× 删除]   │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🎯 动作                                          [+ 添加动作]  │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  1. 📧 发送模板邮件                              [⋮] [×] │    │   │
│  │  │     ├─ 模板: [欢迎邮件 ▼]                               │    │   │
│  │  │     ├─ 发送给: [○ 触发用户 ○ 指定邮箱 ○ 管理员]         │    │   │
│  │  │     └─ 延迟: [0] 分钟后发送                             │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  2. 🏷️ 添加标签                                  [⋮] [×] │    │   │
│  │  │     └─ 标签名: [新用户                              ]   │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ⚙️ 高级设置                                          [展开 ▼]  │   │
│  │  ├─ ☑ 启用此工作流                                              │   │
│  │  ├─ 优先级: [10] (数字越大优先级越高)                           │   │
│  │  ├─ 冷却时间: [24] 小时 (同一用户不重复触发)                    │   │
│  │  └─ 每日最大执行: [100] 次                                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📊 执行统计                                                     │   │
│  │  ├─ 总执行次数: 1,234                                           │   │
│  │  ├─ 成功率: 98.5%                                               │   │
│  │  └─ 最后执行: 2026-01-01 12:00:00                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 动作配置表单（动态生成）

根据 `action_types.config_schema` 动态生成配置表单：

```json
// send_template_email 的 config_schema
{
  "type": "object",
  "properties": {
    "template_code": {
      "type": "string",
      "title": "邮件模板",
      "ui:widget": "template-select",
      "description": "选择要发送的邮件模板"
    },
    "to_type": {
      "type": "string",
      "title": "发送目标",
      "enum": ["trigger_user", "fixed_email", "admin"],
      "enumNames": ["触发用户", "指定邮箱", "管理员"],
      "default": "trigger_user"
    },
    "to": {
      "type": "string",
      "title": "收件人邮箱",
      "ui:visible": {"to_type": "fixed_email"},
      "description": "支持 {{variable}} 语法"
    },
    "delay_minutes": {
      "type": "integer",
      "title": "延迟发送",
      "default": 0,
      "minimum": 0,
      "maximum": 1440,
      "description": "延迟多少分钟后发送"
    }
  },
  "required": ["template_code", "to_type"]
}
```

### 4.3 条件编辑器

```vue
<!-- ConditionEditor.vue -->
<template>
  <div class="condition-editor">
    <div v-for="(condition, index) in conditions" :key="index" class="condition-row">
      <span v-if="index > 0" class="logic-operator">并且</span>
      
      <!-- 字段选择 -->
      <select v-model="condition.field" class="field-select">
        <optgroup v-for="group in fieldGroups" :label="group.label">
          <option v-for="field in group.fields" :value="field.value">
            {{ field.label }}
          </option>
        </optgroup>
      </select>
      
      <!-- 操作符选择 -->
      <select v-model="condition.operator" class="operator-select">
        <option v-for="op in availableOperators" :value="op.code">
          {{ op.name }}
        </option>
      </select>
      
      <!-- 值输入 -->
      <input 
        v-if="needsValue(condition.operator)"
        v-model="condition.value" 
        class="value-input"
        :placeholder="getPlaceholder(condition.field)"
      />
      
      <button @click="removeCondition(index)" class="remove-btn">×</button>
    </div>
    
    <button @click="addCondition" class="add-btn">+ 添加条件</button>
  </div>
</template>
```

---

## 五、API 设计

### 5.1 现有 API（已实现）

```yaml
# 自动化规则 CRUD
GET    /api/automation/rules              # 获取规则列表
POST   /api/automation/rules              # 创建规则
GET    /api/automation/rules/{id}         # 获取规则详情
PUT    /api/automation/rules/{id}         # 更新规则
DELETE /api/automation/rules/{id}         # 删除规则
POST   /api/automation/rules/{id}/execute # 手动执行规则

# 执行日志
GET    /api/automation/logs               # 获取执行日志

# 模板触发规则
GET    /api/email-templates/events/available        # 获取可用事件
GET    /api/email-templates/by-code/{code}/rules    # 获取模板触发规则
POST   /api/email-templates/by-code/{code}/rules    # 创建触发规则
DELETE /api/email-templates/rules/{id}              # 删除触发规则
```

### 5.2 计划新增 API（中期）

```yaml
# 事件类型管理（管理员）
GET    /api/workflows/event-types           # 获取所有事件类型
POST   /api/workflows/event-types           # 创建事件类型
PUT    /api/workflows/event-types/{id}      # 更新事件类型
DELETE /api/workflows/event-types/{id}      # 删除事件类型

# 动作类型管理（管理员）
GET    /api/workflows/action-types          # 获取所有动作类型
POST   /api/workflows/action-types          # 创建动作类型
PUT    /api/workflows/action-types/{id}     # 更新动作类型

# 条件操作符（只读）
GET    /api/workflows/operators             # 获取所有操作符

# 工作流管理（增强版）
GET    /api/workflows                       # 获取工作流列表
POST   /api/workflows                       # 创建工作流
GET    /api/workflows/{id}                  # 获取工作流详情
PUT    /api/workflows/{id}                  # 更新工作流
DELETE /api/workflows/{id}                  # 删除工作流
POST   /api/workflows/{id}/toggle           # 启用/禁用
POST   /api/workflows/{id}/test             # 测试执行
GET    /api/workflows/{id}/logs             # 获取执行日志
GET    /api/workflows/{id}/versions         # 获取版本历史
POST   /api/workflows/{id}/rollback/{ver}   # 回滚到指定版本

# 工作流模板（预设）
GET    /api/workflows/templates             # 获取预设模板
POST   /api/workflows/from-template/{code}  # 从模板创建
```

---

## 六、实施路线图

### 阶段一：完成现有系统集成（本周）

**目标**：让现有自动化规则系统真正生效

**任务清单**：
- [ ] 在 `backend/api/auth.py` 中集成事件发布
  - [ ] 注册成功后发布 `user.registered` 事件
  - [ ] 登录成功后发布 `user.login` 事件
  - [ ] 新设备登录发布 `user.login_new_device` 事件
  - [ ] 密码修改后发布 `user.password_changed` 事件
- [ ] 端到端测试
  - [ ] 创建测试规则：用户注册 → 发送欢迎邮件
  - [ ] 验证触发 → 条件匹配 → 动作执行完整流程
- [ ] 修复可能的 Bug

**代码示例**：
```python
# backend/api/auth.py

@router.post("/register")
async def register_user_with_verification(...):
    # ... 现有注册逻辑 ...
    
    # 发布注册成功事件
    await EventPublisher.publish(
        event_type=EventType.USER_REGISTERED,
        data={
            "user_name": user.display_name or user.email.split('@')[0],
            "user_email": user.email,
            "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "login_url": f"https://{settings.BASE_DOMAIN}/login"
        },
        user=user,
        db=db
    )
    
    return {"success": True, ...}
```

### 阶段二：数据库驱动的类型定义（2周内）

**目标**：将硬编码的事件类型、动作类型迁移到数据库

**任务清单**：
- [ ] 创建数据库迁移
  - [ ] `event_types` 表
  - [ ] `action_types` 表
  - [ ] `condition_operators` 表
- [ ] 初始化数据脚本
- [ ] 修改 `EventPublisher` 从数据库读取事件类型
- [ ] 修改 `RuleEngine` 动态加载动作处理器
- [ ] 管理员界面
  - [ ] 事件类型管理页面
  - [ ] 动作类型管理页面

### 阶段三：可视化工作流编辑器（1个月内）

**目标**：提供拖拽式的工作流设计器

**任务清单**：
- [ ] 前端组件开发
  - [ ] `WorkflowEditor.vue` - 主编辑器
  - [ ] `TriggerSelector.vue` - 触发器选择
  - [ ] `ConditionBuilder.vue` - 条件构建器
  - [ ] `ActionConfigurator.vue` - 动作配置器
  - [ ] `VariableInserter.vue` - 变量插入器
- [ ] 后端 API
  - [ ] 工作流 CRUD
  - [ ] 版本控制
  - [ ] 测试执行
- [ ] 高级功能
  - [ ] 实时预览
  - [ ] 执行日志可视化
  - [ ] 预设模板库

### 阶段四：高级功能（2个月内）

**目标**：完善工作流系统

**任务清单**：
- [ ] 定时触发器实现
- [ ] 工作流版本控制和回滚
- [ ] 导入/导出功能
- [ ] 执行统计和分析
- [ ] 普通用户的简化版邮件规则

---

## 七、与现有系统的整合

### 7.1 保持向后兼容

现有的 `AutomationRule` 表继续使用，新的 `workflows` 表作为增强版本：

```python
class WorkflowMigration:
    @staticmethod
    def migrate_automation_rule_to_workflow(rule: AutomationRule) -> Workflow:
        """将旧规则迁移到新工作流"""
        return Workflow(
            name=rule.name,
            description=rule.description,
            owner_id=rule.owner_id,
            scope='system' if rule.is_system else 'personal',
            trigger_type=rule.trigger_type,
            trigger_config=rule.trigger_config,
            conditions=rule.conditions,
            actions=rule.actions,
            is_active=rule.is_active,
            priority=rule.priority
        )
```

### 7.2 统一的规则引
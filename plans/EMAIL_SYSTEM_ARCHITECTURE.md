
# TalentMail 邮件系统架构设计文档

## 版本历史
| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| 1.0 | 2024-12-29 | Architect | 初始设计 |

---

## 一、设计理念与核心原则

### 1.1 核心开发原则
1. **零硬编码原则** - 所有配置、模板、规则均存储在数据库，通过 API 管理
2. **完整实现原则** - 不留 TODO，不留半成品，功能要么不做，要做就做完整
3. **代码即法律原则** - 先读代码再动手，基于现有架构，保持一致性
4. **不留烂摊子原则** - 所有功能都要测试，所有 API 都要对接

### 1.2 架构设计原则
1. **分层解耦** - 模板层、规则层、执行层相互独立
2. **向前兼容** - 每个阶段的设计都为下一阶段预留扩展点
3. **最小改动** - 新阶段尽量复用已有代码，避免重构
4. **配置驱动** - 业务逻辑通过配置而非代码控制

---

## 二、三阶段架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TalentMail 邮件系统                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   阶段一    │───▶│   阶段二    │───▶│   阶段三    │             │
│  │  邮件模板   │    │ 自动化规则  │    │ 角色权限   │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                  │                  │                      │
│        ▼                  ▼                  ▼                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ 模板引擎   │    │ 规则引擎   │    │ 权限引擎   │             │
│  │ (渲染变量) │    │ (条件匹配) │    │ (访问控制) │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                  │                  │                      │
│        └──────────────────┴──────────────────┘                      │
│                           │                                         │
│                           ▼                                         │
│                  ┌─────────────────┐                                │
│                  │   邮件发送服务   │                                │
│                  │  (SMTP/LMTP)    │                                │
│                  └─────────────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、阶段一：邮件模板系统 (v1.0)

### 3.1 目标
- 管理员可视化编辑系统邮件模板
- 支持变量插入，所见即所得
- 模板按业务场景分类
- 支持测试发送

### 3.2 数据模型

#### 3.2.1 现有表结构 (保持不变)
```sql
-- 已存在: system_email_templates
CREATE TABLE system_email_templates (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 模板代码 (系统内部使用)
    name VARCHAR(100) NOT NULL,            -- 模板名称 (用户可见)
    category VARCHAR(50) NOT NULL,         -- 分类
    description VARCHAR(255),              -- 描述
    subject VARCHAR(255) NOT NULL,         -- 邮件主题
    body_html TEXT NOT NULL,               -- HTML 内容
    body_text TEXT,                        -- 纯文本内容
    variables JSON,                        -- 可用变量列表
    is_active BOOLEAN DEFAULT TRUE,        -- 是否启用
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### 3.2.2 新增表: 模板元数据 (template_metadata)
```sql
-- 新增: 模板元数据定义表
-- 定义系统支持的所有模板类型及其变量
CREATE TABLE template_metadata (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 模板代码 (与 system_email_templates.code 对应)
    name VARCHAR(100) NOT NULL,            -- 显示名称
    category VARCHAR(50) NOT NULL,         -- 业务分类: auth/notification/marketing
    description TEXT,                      -- 详细描述 (触发时机等)
    trigger_description TEXT,              -- 触发时机说明
    variables JSON NOT NULL,               -- 变量定义 (见下方结构)
    default_subject VARCHAR(255),          -- 默认主题
    default_body_html TEXT,                -- 默认 HTML 内容
    default_body_text TEXT,                -- 默认纯文本内容
    is_system BOOLEAN DEFAULT TRUE,        -- 是否系统内置 (内置不可删除)
    sort_order INT DEFAULT 0,              -- 排序
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- variables JSON 结构示例:
-- [
--   {"key": "code", "label": "验证码", "type": "string", "example": "123456", "required": true},
--   {"key": "expires_minutes", "label": "过期时间(分钟)", "type": "number", "example": "10", "required": true},
--   {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": false}
-- ]
```

#### 3.2.3 新增表: 全局变量 (global_variables)
```sql
-- 新增: 全局变量表
-- 所有模板都可以使用的变量
CREATE TABLE global_variables (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,       -- 变量名
    label VARCHAR(100) NOT NULL,           -- 显示名称
    value TEXT NOT NULL,                   -- 变量值 (可以是静态值或表达式)
    value_type VARCHAR(20) DEFAULT 'static', -- static/dynamic/config
    description VARCHAR(255),              -- 说明
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 初始数据:
-- INSERT INTO global_variables (key, label, value, value_type, description) VALUES
-- ('app_name', '应用名称', 'TalentMail', 'config', '从 config.json 读取'),
-- ('site_url', '网站地址', 'https://mail.example.com', 'config', '从 config.json 读取'),
-- ('support_email', '支持邮箱', 'support@example.com', 'config', '从 config.json 读取'),
-- ('current_year', '当前年份', '{{YEAR}}', 'dynamic', '动态计算');
```

### 3.3 API 设计

#### 3.3.1 模板元数据 API
```
GET  /api/email-templates/metadata
     返回所有模板类型定义及其变量

GET  /api/email-templates/metadata/{code}
     返回单个模板类型的详细定义

GET  /api/email-templates/global-variables
     返回所有全局变量
```

#### 3.3.2 模板管理 API (已有，保持不变)
```
GET    /api/email-templates/
POST   /api/email-templates/
GET    /api/email-templates/{id}
PUT    /api/email-templates/{id}
DELETE /api/email-templates/{id}
POST   /api/email-templates/{id}/preview
POST   /api/email-templates/{id}/test      -- 发送测试邮件
```

### 3.4 前端设计

#### 3.4.1 页面结构
```
邮件模板管理
├── 认证与安全
│   ├── [注册验证码] - 编辑/预览/测试
│   ├── [重置密码] - 编辑/预览/测试
│   └── [异地登录提醒] - 编辑/预览/测试
├── 运营通知
│   ├── [欢迎新用户] - 编辑/预览/测试
│   └── [存储空间警告] - 编辑/预览/测试
└── 协作分享
    ├── [文件分享通知] - 编辑/预览/测试
    └── [邀请注册] - 编辑/预览/测试
```

#### 3.4.2 编辑器界面
```
┌─────────────────────────────────────────────────────────────┐
│ 编辑模板: 注册验证码                                         │
├─────────────────────────────────────────────────────────────┤
│ 触发时机: 用户在注册页面点击"获取验证码"时发送               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────┐  ┌─────────────────┐  │
│  │                                 │  │ 可用变量        │  │
│  │  [B] [I] [U] [列表] [清除]      │  │                 │  │
│  │  ─────────────────────────────  │  │ 场景变量:       │  │
│  │                                 │  │ [code] 验证码   │  │
│  │  富文本编辑区域                  │  │ [expires] 过期  │  │
│  │                                 │  │                 │  │
│  │  您的验证码是: {{code}}         │  │ 全局变量:       │  │
│  │  有效期 {{expires_minutes}} 分钟│  │ [app_name]      │  │
│  │                                 │  │ [site_url]      │  │
│  │                                 │  │ [current_year]  │  │
│  └─────────────────────────────────┘  └─────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [预览] [发送测试邮件] [保存]                                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 后端实现要点

#### 3.5.1 模板渲染服务 (core/template_engine.py)
```python
# 新建文件: backend/core/template_engine.py

class TemplateEngine:
    """模板渲染引擎 - 阶段一核心组件，阶段二复用"""
    
    def __init__(self, db: Session):
        self.db = db
        self._global_vars_cache = None
    
    def get_global_variables(self) -> dict:
        """获取全局变量"""
        # 从数据库 + config 获取
        pass
    
    def render(self, template_str: str, context: dict) -> str:
        """渲染模板字符串"""
        # 合并全局变量和上下文变量
        # 替换 {{variable}} 格式
        pass
    
    def render_template(self, template_code: str, context: dict) -> dict:
        """渲染完整模板，返回 subject, body_html, body_text"""
        pass
```

#### 3.5.2 邮件发送服务重构 (core/mail_service.py)
```python
# 重构: backend/core/mail_service.py

class MailService:
    """邮件发送服务 - 统一入口"""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = TemplateEngine(db)
    
    async def send_by_template(
        self,
        template_code: str,
        to_email: str,
        context: dict,
        from_email: str = None  # 默认使用系统邮箱
    ) -> bool:
        """通过模板发送邮件"""
        pass
    
    async def send_raw(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = None,
        from_email: str = None
    ) -> bool:
        """直接发送邮件 (不使用模板)"""
        pass
```

### 3.6 初始化数据

#### 3.6.1 模板元数据初始化
```python
# backend/initial/template_metadata.py

TEMPLATE_METADATA = [
    {
        "code": "verification_code_register",
        "name": "注册验证码",
        "category": "auth",
        "description": "用户注册时发送的验证码邮件",
        "trigger_description": "用户在注册页面输入邮箱并点击"获取验证码"时触发",
        "variables": [
            {"key": "code", "label": "验证码", "type": "string", "example": "123456", "required": True},
            {"key": "expires_minutes", "label": "过期时间(分钟)", "type": "number", "example": "10", "required": True}
        ],
        "is_system": True,
        "sort_order": 1
    },
    {
        "code": "verification_code_reset_password",
        "name": "重置密码验证码",
        "category": "auth",
        "description": "用户忘记密码时发送的验证码邮件",
        "trigger_description": "用户在忘记密码页面输入邮箱并点击"获取验证码"时触发",
        "variables": [
            {"key": "code", "label": "验证码", "type": "string", "example": "888888", "required": True},
            {"key": "expires_minutes", "label": "过期时间(分钟)", "type": "number", "example": "10", "required": True}
        ],
        "is_system": True,
        "sort_order": 2
    },
    {
        "code": "welcome_email",
        "name": "欢迎新用户",
        "category": "notification",
        "description": "用户注册成功后发送的欢迎邮件",
        "trigger_description": "用户完成注册后自动发送",
        "variables": [
            {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": False},
            {"key": "user_email", "label": "用户邮箱", "type": "string", "example": "user@example.com", "required": True},
            {"key": "login_url", "label": "登录链接", "type": "url", "example": "https://mail.example.com/login", "required": True}
        ],
        "is_system": True,
        "sort_order": 10
    },
    {
        "code": "login_alert",
        "name": "异地登录提醒",
        "category": "auth",
        "description": "检测到新设备或异地登录时发送的安全提醒",
        "trigger_description": "用户从新设备或新IP登录时触发",
        "variables": [
            {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": False},
            {"key": "login_time", "label": "登录时间", "type": "datetime", "example": "2024-12-29 10:30:00", "required": True},
            {"key": "login_ip", "label": "登录IP", "type": "string", "example": "192.168.1.1", "required": True},
            {"key": "login_device", "label": "登录设备", "type": "string", "example": "Chrome on Windows", "required": True},
            {"key": "login_location", "label": "登录地点", "type": "string", "example": "北京市", "required": False}
        ],
        "is_system": True,
        "sort_order": 3
    },
    {
        "code": "storage_warning",
        "name": "存储空间警告",
        "category": "notification",
        "description": "用户存储空间即将用尽时发送的警告",
        "trigger_description": "用户存储空间使用超过80%时触发",
        "variables": [
            {"key": "user_name", "label": "用户名", "type": "string", "example": "张三", "required": False},
            {"key": "used_percent", "label": "已用百分比", "type": "number", "example": "85", "required": True},
            {"key": "used_space", "label": "已用空间", "type": "string", "example": "850MB", "required": True},
            {"key": "total_space", "label": "总空间", "type": "string", "example": "1GB", "required": True},
            {"key": "upgrade_url", "label": "升级链接", "type": "url", "example": "https://...", "required": False}
        ],
        "is_system": True,
        "sort_order": 11
    },
    {
        "code": "file_share_notification",
        "name": "文件分享通知",
        "category": "collaboration",
        "description": "用户分享文件给他人时发送的通知",
        "trigger_description": "用户在网盘中分享文件并填写接收者邮箱时触发",
        "variables": [
            {"key": "sender_name", "label": "分享者名称", "type": "string", "example": "张三", "required": True},
            {"key": "sender_email", "label": "分享者邮箱", "type": "string", "example": "zhangsan@example.com", "required": True},
            {"key": "file_name", "label": "文件名", "type": "string", "example": "季度报表.pdf", "required": True},
            {"key": "file_size", "label": "文件大小", "type": "string", "example": "2.5MB", "required": False},
            {"key": "share_url", "label": "分享链接", "type": "url", "example": "https://...", "required": True},
            {"key": "share_password", "label": "访问密码", "type": "string", "example": "1234", "required": False},
            {"key": "expires_at", "label": "过期时间", "type": "datetime", "example": "2024-12-31", "required": False}
        ],
        "is_system": True,
        "sort_order": 20
    },
    {
        "code": "invite_registration",
        "name": "邀请注册",
        "category": "collaboration",
        "description": "邀请他人注册 TalentMail 时发送的邀请函",
        "trigger_description": "管理员或用户生成邀请链接并发送时触发",
        "variables": [
            {"key": "inviter_name", "label": "邀请人名称", "type": "string", "example": "张三", "required": True},
            {"key": "inviter_email", "label": "邀请人邮箱", "type": "string", "example": "zhangsan@example.com", "required": True},
            {"key": "invite_url", "label": "邀请链接", "type": "url", "example": "https://...", "required": True},
            {"key": "invite_code", "label": "邀请码", "type": "string", "example": "ABC123", "required": True},
            {"key": "expires_at", "label": "过期时间", "type": "datetime", "example": "2024-12-31", "required": False}
        ],
        "is_system": True,
        "sort_order": 21
    }
]

GLOBAL_VARIABLES = [
    {"key": "app_name", "label": "应用名称", "value": "TalentMail", "value_type": "config", "description": "从 config.json 读取 appName"},
    {"key": "site_url", "label": "网站地址", "value": "", "value_type": "config", "description": "从 config.json 读取"},
    {"key": "support_email", "label": "支持邮箱", "value": "", "value_type": "config", "description": "从 config.json 读取"},
    {"key": "current_year", "label": "当前年份", "value": "", "value_type": "dynamic", "description": "动态计算当前年份"},
    {"key": "company_name", "label": "公司名称", "value": "", "value_type": "config", "description": "从 config.json 读取"}
]
```

---

## 四、阶段二：自动化规则引擎 (v2.0)

### 4.1 目标
- 管理员可创建自动化规则
- 支持多种触发器（收到邮件、定时、用户行为）
- 支持条件判断（发件人、主题、内容匹配）
- 支持多种动作（发邮件、转发、打标签、移动）
- **复用阶段一的模板系统**

### 4.2 数据模型

#### 4.2.1 自动化规则表 (automation_rules)
```sql
CREATE TABLE automation_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,            -- 规则名称
    description TEXT,                      -- 规则描述
    owner_id INT REFERENCES users(id),     -- 创建者 (NULL 表示系统规则)
    is_system BOOLEAN DEFAULT FALSE,       -- 是否系统规则
    is_active BOOLEAN DEFAULT TRUE,        -- 是否启用
    priority INT DEFAULT 0,                -- 优先级 (数字越大越先执行)
    
    -- 触发器配置
    trigger_type VARCHAR(50) NOT NULL,     -- email_received/scheduled/user_event
    trigger_config JSON NOT NULL,          -- 触发器详细配置
    
    -- 条件配置
    conditions JSON,                       -- 条件列表 (AND 关系)
    
    -- 动作配置
    actions JSON NOT NULL,                 -- 动作列表 (顺序执行)
    
    -- 统计
    execution_count INT DEFAULT 0,         -- 执行次数
    last_executed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- trigger_config 示例:
-- email_received: {"mailboxes": ["support@", "finance@"], "include_spam": false}
-- scheduled: {"cron": "0 9 * * 1-5", "timezone": "Asia/Shanghai"}
-- user_event: {"event": "user_inactive", "days": 7}

-- conditions 示例:
-- [
--   {"field": "from", "operator": "contains", "value": "@company.com"},
--   {"field": "subject", "operator": "contains", "value": "发票"},
--   {"field": "received_at", "operator": "between", "value": ["09:00", "18:00"]}
-- ]

-- actions 示例:
-- [
--   {"type": "send_email", "config": {"template_code": "auto_reply_support", "to": "{{from}}"}},
--   {"type": "add_tag", "config": {"tag_id": 5}},
--   {"type": "forward", "config": {"to": "finance@company.com"}},
--   {"type": "move_to_folder", "config": {"folder_id": 10}}
-- ]
```

#### 4.2.2 规则执行日志表 (automation_logs)
```sql
CREATE TABLE automation_logs (
    id BIGSERIAL PRIMARY KEY,
    rule_id INT REFERENCES automation_rules(id),
    trigger_type VARCHAR(50),
    trigger_data JSON,                     -- 触发时的上下文数据
    conditions_matched BOOLEAN,            -- 条件是否匹配
    actions_executed JSON,                 -- 执行的动作及结果
    status VARCHAR(20),                    -- success/failed/partial
    error_message TEXT,
    execution_time_ms INT,                 -- 执行耗时
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4.3 规则引擎架构

```
┌─────────────────────────────────────────────────────────────┐
│                      规则引擎 (RuleEngine)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ 触发器管理  │    │ 条件匹配器  │    │ 动作执行器  │     │
│  │ TriggerMgr │    │ ConditionMgr│    │ ActionMgr  │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │EmailTrigger│    │FieldMatcher│    │SendEmailAct│     │
│  │SchedTrigger│    │ TimeMatcher│    │ForwardAct  │     │
│  │EventTrigger│    │ RegexMatcher│    │TagAct      │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                              │              │
│                                              ▼              │
│                                    ┌─────────────────┐     │
│                                    │ TemplateEngine │     │
│                                    │   (阶段一复用)   │     │
│                                    └─────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 与阶段一的复用点

1. **TemplateEngine** - 规则动作 `send_email` 直接调用阶段一的模板引擎
2. **MailService** - 规则动作 `send_email` 和 `forward` 复用邮件发送服务
3. **template_metadata** - 规则可以创建新的模板类型（如 `auto_reply_support`）
4. **global_variables** - 规则动作中的变量可以使用全局变量

### 4.5 前端设计

```
自动化规则
├── 我的规则
│   ├── [新建规则]
│   └── 规则列表 (卡片式)
│       ├── 规则名称 | 触发器 | 状态 | 执行次数
│       └── [编辑] [启用/禁用] [删除] [查看日志]
└── 系统规则 (仅管理员可见)
    └── 规则列表

规则编辑器:
┌─────────────────────────────────────────────────────────────┐
│ 创建自动化规则                                               │
├─────────────────────────────────────────────────────────────┤
│ 规则名称: [客服自动回复                              ]       │
├─────────────────────────────────────────────────────────────┤
│ 当...                                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 触发器: [收到新邮件 ▼]                                   │ │
│ │ 邮箱:   [support@example.com ▼]                         │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 如果满足...                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [发件人] [不包含] [@example.com]              [+ 添加]   │ │
│ │ [主题]   [包含]   [咨询|问题|帮助]            [× 删除]   │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 则执行...                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. [发送邮件 ▼] 使用模板: [客服自动回复 ▼]    [× 删除]   │ │
│ │ 2. [添加标签 ▼] 标签: [客户咨询 ▼]            [× 删除]   │ │
│ │                                              [+ 添加动作] │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ [取消]                                            [保存规则] │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、阶段三：角色与权限系统 (v3.0)

### 5.1 目标
- 支持自定义角色
- 细粒度权限控制
- 权限继承机制
- **复用阶段一、二的基础设施**

### 5.2 数据模型

#### 5.2.1 角色表 (roles)
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,       -- 角色名称
    display_name VARCHAR(100) NOT NULL,     -- 显示名称
    description TEXT,                       -- 角色描述
    is_system BOOLEAN DEFAULT FALSE,        -- 是否系统内置
    parent_id INT REFERENCES roles(id),     -- 父角色 (继承权限)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 初始角色:
-- INSERT INTO roles (name, display_name, is_system) VALUES
-- ('super_admin', '超级管理员', TRUE),
-- ('admin', '管理员', TRUE),
-- ('user', '普通用户', TRUE),
-- ('guest', '访客', TRUE);
```

#### 5.2.2 权限表 (permissions)
```sql
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,      -- 权限代码
    name VARCHAR(100) NOT NULL,             -- 权限名称
    category VARCHAR(50) NOT NULL,          -- 分类: mail/template/rule/user/system
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 权限示例:
-- mail.send, mail.receive, mail.delete
-- template.view, template.edit, template.create
-- rule.view, rule.create, rule.edit, rule.delete
-- user.view, user.create, user.edit, user.delete
-- system.settings, system.backup
```

#### 5.2.3 角色权限关联表 (role_permissions)
```sql
CREATE TABLE role_permissions (
    role_id INT REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INT REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
```

#### 5.2.4 用户角色关联表 (user_roles)
```sql
CREATE TABLE user_roles (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    role_id INT REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by INT REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);
```

### 5.3 权限引擎架构

```
┌─────────────────────────────────────────────────────────────┐
│                    权限引擎 (PermissionEngine)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ 角色管理    │    │ 权限检查    │    │ 权限继承    │     │
│  │ RoleMgr    │    │ PermChecker │    │ Inheritance │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    权限缓存层                        │   │
│  │              (Redis / Memory Cache)                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API 中间件                        │   │
│  │              @require_permission(...)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 与阶段一、二的复用点

1. **模板权限控制** - 基于权限决定用户能否编辑模板
2. **规则权限控制** - 基于权限决定用户能否创建/编辑规则
3. **邮件发送权限** - 基于权限决定用户能否发送邮件
4. **管理功能权限** - 基于权限决定用户能否访问管理页面

### 5.5 前端设计

```
角色与权限管理
├── 角色管理
│   ├── [新建角色]
│   └── 角色列表
│       ├── 超级管理员 (系统) | 权限数: 全部 | 用户数: 1
│       ├── 管理员 (系统) | 权限数: 45 | 用户数: 3
│       ├── 普通用户 (系统) | 权限数: 20 | 用户数: 100
│       └── [自定义角色] | 权限数: 15 | 用户数: 10
│           └── [编辑] [删除] [查看用户]
├── 权限分配
│   └── 角色权限矩阵
│       ┌──────────────┬────────┬────────┬────────┐
│       │ 权限         │ 管理员 │ 用户   │ 访客   │
│       ├──────────────┼────────┼────────┼────────┤
│       │ 邮件.发送    │   ✓    │   ✓    │   ✗    │
│       │ 邮件.删除    │   ✓    │   ✓    │   ✗    │
│       │ 模板.编辑    │   ✓    │   ✗    │   ✗    │
│       │ 规则.创建    │   ✓    │   ✓    │   ✗    │
│       │ 用户.管理    │   ✓    │   ✗    │   ✗    │
│       └──────────────┴────────┴────────┴────────┘
└── 用户角色
    └── 用户角色分配
        ├── 搜索用户: [                    ]
        └── 用户列表
            ├── 张三 | admin@example.com | 角色: [管理员 ▼]
            └── 李四 | user@example.com | 角色: [普通用户 ▼]
```

---

## 六、开发计划

### 6.1 阶段一：邮件模板系统

#### 第一周：后端基础
- [ ] 创建 `template_metadata` 表迁移
- [ ] 创建 `global_variables` 表迁移
- [ ] 实现 `TemplateEngine` 类
- [ ] 重构 `MailService` 统一邮件发送
- [ ] 实现元数据 API 端点
- [ ] 初始化模板元数据和全局变量

#### 第二周：前端实现
- [ ] 重构模板列表页面（按分类分组）
- [ ] 实现富文本编辑器组件
- [ ] 实现变量插入面板
- [ ] 实现模板预览功能
- [ ] 实现测试发送功能

#### 第三周：集成测试
- [ ] 验证所有模板类型
- [ ] 测试变量渲染
- [ ] 测试邮件发送
- [ ] 修复问题

### 6.2 阶段二：自动化规则引擎

#### 第四周：后端基础
- [ ] 创建 `automation_rules` 表迁移
- [ ] 创建 `automation_logs` 表迁移
- [ ] 实现 `RuleEngine` 核心类
- [ ] 实现触发器管理器
- [ ] 实现条件匹配器
- [ ] 实现动作执行器

#### 第五周：规则 API
- [ ] 实现规则 CRUD API
- [ ] 实现规则执行 API
- [ ] 实现日志查询 API
- [ ] 集成邮件接收触发器

#### 第六周：前端实现
- [ ] 实现规则列表页面
- [ ] 实现规则编辑器
- [ ] 实现条件构建器
- [ ] 实现动作配置器
- [ ] 实现执行日志查看

### 6.3 阶段三：角色与权限系统

#### 第七周：后端基础
- [ ] 创建 `roles` 表迁移
- [ ] 创建 `permissions` 表迁移
- [ ] 创建关联表迁移
- [ ] 实现 `PermissionEngine` 核心类
- [ ] 实现权限检查中间件

#### 第八周：权限 API
- [ ] 实现角色 CRUD API
- [ ] 实现权限分配 API
- [ ] 实现用户角色 API
- [ ] 初始化系统角色和权限

#### 第九周：前端实现
- [ ] 实现角色管理页面
- [ ] 实现权限矩阵组件
- [ ] 实现用户角色分配
- [ ] 集成权限检查到现有页面

---

## 七、技术实现细节

### 7.1 模板变量语法

```
基本变量: {{variable_name}}
默认值:   {{variable_name|default:"默认值"}}
格式化:   {{date|format:"YYYY-MM-DD"}}
条件:     {{#if condition}}内容{{/if}}
循环:     {{#each items}}{{this.name}}{{/each}}
```

### 7.2 条件匹配器操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| equals | 等于 | `{"field": "from", "operator": "equals", "value": "test@example.com"}` |
| not_equals | 不等于 | `{"field": "from", "operator": "not_equals", "value": "spam@"}` |
| contains | 包含 | `{"field": "subject", "operator": "contains", "value": "发票"}` |
| not_contains | 不包含 | `{"field": "body", "operator": "not_contains", "value": "广告"}` |
| starts_with | 开头是 | `{"field": "subject", "operator": "starts_with", "value": "Re:"}` |
| ends_with | 结尾是 | `{"field": "from", "operator": "ends_with", "value": "@company.com"}` |
| regex | 正则匹配 | `{"field": "subject", "operator": "regex", "value": "订单号:\\d+"}` |
| between | 范围内 | `{"field": "received_at", "operator": "between", "value": ["09:00", "18:00"]}` |

### 7.3 动作类型定义

| 动作类型 | 说明 | 配置示例 |
|----------|------|----------|
| send_email | 发送邮件 | `{"template_code": "auto_reply", "to": "{{from}}"}` |
| forward | 转发邮件 | `{"to": "manager@company.com", "keep_original": true}` |
| add_tag | 添加标签 | `{"tag_id": 5}` |
| remove_tag | 移除标签 | `{"tag_id": 5}` |
| move_to_folder | 移动到文件夹 | `{"folder_id": 10}` |
| mark_as_read | 标记已读 | `{}` |
| mark_as_starred | 标记星标 | `{}` |
| delete | 删除邮件 | `{"permanent": false}` |
| webhook | 调用 Webhook | `{"url": "https://...", "method": "POST"}` |

### 7.4 权限代码规范

```
格式: {模块}.{操作}

模块:
- mail: 邮件相关
- template: 模板相关
- rule: 规则相关
- user: 用户相关
- role: 角色相关
- system: 系统相关

操作:
- view: 查看
- create: 创建
- edit: 编辑
- delete: 删除
- manage: 管理 (包含所有操作)

示例:
- mail.send: 发送邮件
- mail.delete: 删除邮件
- template.edit: 编辑模板
- rule.create: 创建规则
- user.manage: 管理用户
- system.settings: 系统设置
```

---

## 八、API 端点汇总

### 8.1 阶段一 API

```
# 模板元数据
GET  /api/email-templates/metadata
GET  /api/email-templates/metadata/{code}
GET  /api/email-templates/global-variables

# 模板管理 (已有)
GET    /api/email-templates/
POST   /api/email-templates/
GET    /api/email-templates/{id}
PUT    /api/email-templates/{id}
DELETE /api/email-templates/{id}
POST   /api/email-templates/{id}/preview
POST   /api/email-templates/{id}/test
```

### 8.2 阶段二 API

```
# 规则管理
GET    /api/automation-rules/
POST   /api/automation-rules/
GET    /api/automation-rules/{id}
PUT    /api/automation-rules/{id}
DELETE /api/automation-rules/{id}
POST   /api/automation-rules/{id}/toggle
POST   /api/automation-rules/{id}/test

# 规则日志
GET    /api/automation-rules/{id}/logs
GET    /api/automation-logs/
```

### 8.3 阶段三 API

```
# 角色管理
GET    /api/roles/
POST   /api/roles/
GET    /api/roles/{id}
PUT    /api/roles/{id}
DELETE /api/roles/{id}

# 权限管理
GET    /api/permissions/
GET    /api/roles/{id}/permissions
PUT    /api/roles/{id}/permissions

# 用户角色
GET    /api/users/{id}/roles
PUT    /api/users/{id}/roles
```

---

## 九、总结

本架构设计遵循以下核心原则：

1. **渐进式开发** - 三个阶段相互独立又相互关联，每个阶段都可以独立交付价值
2. **代码复用** - 阶段一的模板引擎被阶段二复用，阶段三的权限系统保护前两个阶段的功能
3. **配置驱动** - 所有业务逻辑通过数据库配置，而非硬编码
4. **可扩展性** - 每个阶段都预留了扩展点，方便未来添加新功能

通过这个架构，TalentMail 将拥有一个完整的邮件系统，支持：
- 可视化模板编辑
- 自动化邮件处理
- 细粒度权限控制
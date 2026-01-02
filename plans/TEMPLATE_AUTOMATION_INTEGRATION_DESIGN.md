# 邮件模板与自动化规则引擎集成设计

## 1. 设计目标

根据用户需求，模板系统应该支持两种使用场景：

### 场景一：Admin 后台手动发送（主要场景）
- Admin 在后台管理系统选择模板
- 填写收件人和变量
- 一键发送邮件
- 无需写代码

### 场景二：自动化触发发送
- 通过自动化规则引擎配置触发条件
- 当系统事件发生时自动执行
- 复用现有的 `AutomationRule` 表
- 不新建触发器表

---

## 2. 核心设计原则

### ✅ 复用现有架构
- **不新建 `template_triggers` 表**
- 模板触发 = 创建一条 `AutomationRule`，动作类型为 `send_template_email`
- 前端触发配置组件 = 创建/编辑自动化规则的简化界面

### ✅ 分离关注点
| 模块 | 职责 |
|------|------|
| `system_email_templates` 表 | 存储模板内容（主题、正文、变量定义） |
| `template_metadata` 表 | 存储模板元数据（变量说明、默认值） |
| `automation_rules` 表 | 存储触发规则（触发器、条件、动作） |
| `automation_logs` 表 | 存储执行日志 |

### ✅ 统一事件系统
- 创建 `EventPublisher` 事件发布器
- 在业务代码中发布事件
- 规则引擎订阅事件并执行

---

## 3. 数据模型设计

### 3.1 现有表（无需修改）

```sql
-- 模板内容表
system_email_templates:
  - id, code, name, category
  - subject, body_html, body_text
  - variables (JSON)
  - is_active

-- 模板元数据表
template_metadata:
  - id, code, name, category
  - description, trigger_description
  - variables (JSON: [{key, label, type, example, required}])
  - default_subject, default_body_html

-- 自动化规则表
automation_rules:
  - id, name, description
  - owner_id, is_system, is_active
  - trigger_type, trigger_config (JSON)
  - conditions (JSON)
  - actions (JSON: [{type, config}])
  - execution_count, last_executed_at

-- 自动化日志表
automation_logs:
  - id, rule_id, trigger_type
  - trigger_data, conditions_matched
  - actions_executed, status, error_message
```

### 3.2 动作类型扩展

在 `RuleEngine` 中添加新动作类型：

```python
class ActionType:
    # ... 现有动作
    SEND_TEMPLATE_EMAIL = "send_template_email"  # 新增：发送模板邮件
```

动作配置格式：
```json
{
  "type": "send_template_email",
  "config": {
    "template_code": "welcome_email",
    "to": "{{user_email}}",           // 支持变量
    "to_type": "trigger_user",        // trigger_user / fixed_email / admin
    "variables": {                     // 可选，覆盖默认变量
      "user_name": "{{user_name}}",
      "login_url": "https://mail.example.com"
    }
  }
}
```

---

## 4. 事件系统设计

### 4.1 EventPublisher 事件发布器

```python
# backend/core/event_publisher.py

class EventType:
    """系统事件类型"""
    # 用户事件
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGIN_NEW_DEVICE = "user.login_new_device"
    USER_PASSWORD_CHANGED = "user.password_changed"
    
    # 邮件事件
    EMAIL_RECEIVED = "email.received"
    EMAIL_SENT = "email.sent"
    
    # 文件事件
    FILE_SHARED = "drive.file_shared"
    
    # 管理事件
    INVITE_CREATED = "admin.invite_created"


class EventPublisher:
    """事件发布器 - 单例模式"""
    
    @classmethod
    async def publish(cls, event_type: str, data: dict, user: User = None, db: Session = None):
        """
        发布事件，触发相关规则
        
        Args:
            event_type: 事件类型
            data: 事件数据
            user: 相关用户
            db: 数据库会话
        """
        if not db:
            return
        
        engine = RuleEngine(db)
        await engine.trigger_user_event(event_type, user, data)
```

### 4.2 业务代码集成示例

```python
# backend/api/auth.py

@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    # ... 注册逻辑
    user = create_user(db, data)
    
    # 发布注册成功事件
    await EventPublisher.publish(
        event_type=EventType.USER_REGISTERED,
        data={
            "user_name": user.display_name or user.email.split('@')[0],
            "user_email": user.email,
            "register_time": datetime.now().isoformat(),
            "login_url": f"https://{settings.BASE_DOMAIN}/login"
        },
        user=user,
        db=db
    )
    
    return {"success": True}
```

---

## 5. API 设计

### 5.1 模板相关 API（现有）

```
GET    /api/email-templates              # 获取模板列表
GET    /api/email-templates/{id}         # 获取单个模板
POST   /api/email-templates              # 创建模板
PUT    /api/email-templates/{id}         # 更新模板
DELETE /api/email-templates/{id}         # 删除模板
POST   /api/email-templates/{id}/preview # 预览模板
POST   /api/email-templates/{id}/test    # 发送测试邮件
```

### 5.2 新增：手动发送模板邮件 API

```
POST /api/email-templates/{id}/send
```

请求体：
```json
{
  "to": "recipient@example.com",
  "cc": "cc@example.com",           // 可选
  "variables": {
    "user_name": "张三",
    "order_id": "ORD-12345"
  }
}
```

响应：
```json
{
  "success": true,
  "message": "邮件已发送",
  "message_id": "<abc123@mail.example.com>"
}
```

### 5.3 模板触发规则 API（复用自动化规则）

```
# 获取某模板关联的规则
GET /api/email-templates/{code}/rules

# 为模板创建触发规则（本质是创建自动化规则）
POST /api/email-templates/{code}/rules

# 更新规则
PUT /api/automation/rules/{id}

# 删除规则
DELETE /api/automation/rules/{id}
```

创建规则请求体（简化版）：
```json
{
  "trigger_type": "user_event",
  "trigger_event": "user.registered",
  "conditions": [],
  "send_to_type": "trigger_user",
  "send_to_email": null,
  "cooldown_hours": 0,
  "is_enabled": true
}
```

后端转换为标准 AutomationRule：
```json
{
  "name": "模板触发: welcome_email - 用户注册成功",
  "trigger_type": "user_event",
  "trigger_config": {
    "event_type": "user.registered"
  },
  "conditions": [],
  "actions": [{
    "type": "send_template_email",
    "config": {
      "template_code": "welcome_email",
      "to_type": "trigger_user"
    }
  }],
  "is_system": true,
  "is_active": true
}
```

---

## 6. 前端设计

### 6.1 触发配置弹窗（已创建）

文件：`frontend/app/components/settings/TemplateTriggerConfig.vue`

功能：
- 选择触发类型（系统事件 / 定时 / 手动）
- 选择系统事件（用户注册、登录、密码修改等）
- 配置发送目标（用户本人 / 指定邮箱 / 管理员）
- 设置冷却时间

与后端交互：
- 保存时调用 `POST /api/email-templates/{code}/rules`
- 加载时调用 `GET /api/email-templates/{code}/rules`

### 6.2 模板选择器（已创建）

文件：`frontend/app/components/email/TemplateSelector.vue`

功能：
- 在 ComposeModal 中选择模板
- 填写变量
- 应用到邮件正文

### 6.3 手动发送功能

在模板列表页添加「发送」按钮：
- 点击打开发送弹窗
- 填写收件人和变量
- 调用 `POST /api/email-templates/{id}/send`

---

## 7. 实现计划

### 第一步：增强规则引擎（后端）
1. 添加 `send_template_email` 动作类型
2. 实现动作处理器
3. 创建 `EventPublisher` 事件发布器

### 第二步：实现模板发送 API（后端）
1. 添加 `POST /api/email-templates/{id}/send` 接口
2. 添加 `GET/POST /api/email-templates/{code}/rules` 接口

### 第三步：集成事件发布（后端）
1. 在注册逻辑中发布 `user.registered` 事件
2. 在登录逻辑中发布 `user.login` 事件
3. 在其他业务逻辑中发布相应事件

### 第四步：更新前端组件
1. 更新 `TemplateTriggerConfig.vue` 调用真实 API
2. 添加手动发送弹窗
3. 完善错误处理和 loading 状态

---

## 8. 数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户操作                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │ 场景一：手动发送 │      │ 场景二：自动触发 │                   │
│  └────────┬────────┘      └────────┬────────┘                   │
│           │                        │                             │
│           ▼                        ▼                             │
│  ┌─────────────────┐      ┌─────────────────┐                   │
│  │ 选择模板        │      │ 配置触发规则    │                   │
│  │ 填写收件人      │      │ 保存为自动化规则 │                   │
│  │ 填写变量        │      └────────┬────────┘                   │
│  │ 点击发送        │               │                             │
│  └────────┬────────┘               │                             │
│           │                        │                             │
└───────────┼────────────────────────┼─────────────────────────────┘
            │                        │
            ▼                        ▼
┌───────────────────────┐   ┌───────────────────────────────────┐
│ POST /templates/send  │   │        系统事件发生               │
│                       │   │  (用户注册/登录/修改密码等)        │
└───────────┬───────────┘   └───────────────┬───────────────────┘
            │                               │
            │                               ▼
            │               ┌───────────────────────────────────┐
            │               │      EventPublisher.publish()     │
            │               │      发布事件到规则引擎            │
            │               └───────────────┬───────────────────┘
            │                               │
            │                               ▼
            │               ┌───────────────────────────────────┐
            │               │         RuleEngine                │
            │               │  1. 查找匹配的 AutomationRule     │
            │               │  2. 检查条件                      │
            │               │  3. 执行 send_template_email      │
            │               └───────────────┬───────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────────────────────────────────────────────┐
│                     TemplateEngine                            │
│                  1. 加载模板内容                               │
│                  2. 渲染变量                                   │
│                  3. 生成邮件                                   │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                      send_email()                             │
│                    SMTP 发送邮件                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 9. 优势

1. **复用现有架构** - 不新建表，复用 `AutomationRule`
2. **统一的执行引擎** - 所有自动化动作由 `RuleEngine` 执行
3. **完整的日志记录** - 复用 `AutomationLog` 表
4. **灵活的条件配置** - 复用 14 种条件操作符
5. **可扩展** - 未来可以添加更多事件类型和动作类型
6. **非开发人员友好** - 前端提供简化的配置界面

---

## 10. 示例：创建欢迎邮件触发规则

### 后台操作步骤：
1. 进入「设置 → 邮件模板」
2. 找到「欢迎邮件」模板，点击「⚙️ 触发设置」
3. 选择触发方式：系统事件
4. 选择事件：用户注册成功
5. 发送目标：用户本人
6. 点击「保存设置」

### 系统行为：
1. 创建一条 `AutomationRule` 记录
2. 当新用户注册成功时，`EventPublisher` 发布事件
3. `RuleEngine` 匹配到规则，执行 `send_template_email` 动作
4. 新用户收到欢迎邮件
5. 执行记录保存到 `AutomationLog`
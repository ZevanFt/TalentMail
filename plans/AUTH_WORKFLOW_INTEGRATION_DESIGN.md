# 认证系统与工作流集成设计 (Auth Workflow Integration Design)

## 1. 问题背景

当前系统的注册逻辑 (`auth.py`) 是硬编码的，虽然使用了邮件模板，但没有利用 `WorkflowService` 进行流程编排。同时，系统预置的 `user_registration` 工作流是一个包含"等待用户输入"的长流程，无法直接在无状态的 HTTP API 中一次性执行。

为了实现"无代码配置注册流程"的愿景，我们需要重构认证模块与工作流引擎的交互方式。

## 2. 核心架构：事件驱动与流程拆分

我们将庞大的"注册全流程"拆分为两个独立的、职责单一的工作流。

### 2.1 工作流 A: 发送验证码 (Verification Flow)

此工作流负责处理验证码的生成与发送。它由前端的 `/api/auth/send-verification-code` 接口触发。

*   **触发方式**: API 调用 (同步执行)
*   **流程定义**:
    1.  **Start**: 接收邮箱地址、用途 (register/reset_password)。
    2.  **Generate Code**: 生成 6 位数字验证码 (存入 `verification_codes` 表)。
    3.  **Send Email**: 调用邮件模板发送验证码。
        *   *配置项*: `template_code` (默认: `verification_code_register`)
    4.  **End**: 返回成功响应。

### 2.2 工作流 B: 新用户入职 (User Onboarding Flow)

此工作流负责用户注册成功后的后续操作（如欢迎邮件、通知管理员、分配初始存储空间等）。

*   **触发方式**: 内部事件 (`user.registered`)
*   **流程定义**:
    1.  **Trigger**: 监听 `user.registered` 事件 (包含 `user_id`, `email`)。
    2.  **Condition**: 检查配置 `config.send_welcome_email`。
    3.  **Action (Welcome)**: 发送欢迎邮件。
        *   *配置项*: `template_code` (默认: `welcome_email`)
    4.  **Condition**: 检查配置 `config.notify_admin`。
    5.  **Action (Admin)**: 发送管理员通知。
        *   *配置项*: `template_code` (默认: `admin_new_user_notification`)
    6.  **Action (Example)**: 为新用户创建示例数据（如我们之前讨论的自动创建"示例工作流"）。
    7.  **End**: 结束。

## 3. 详细设计

### 3.1 数据库变更

我们需要更新 `init_workflow_data.py` 中的系统工作流定义，将原来的大流程拆分为两个。

#### 新系统工作流: `auth_send_verification`
*   **Nodes**: `trigger_manual`, `data_generate_code`, `action_send_template`, `end_success`
*   **Input**: `email`, `purpose`

#### 修改系统工作流: `user_registration` (改为 `user_onboarding`)
*   **Trigger**: 改为 `trigger_user_event` (Event Type: `user.registered`)
*   **Nodes**: `condition`, `action_send_template` (Welcome), `action_send_template` (Admin), `end_success`

### 3.2 代码重构 (Auth API)

修改 `backend/api/auth.py`:

```python
# 伪代码示例

@router.post("/send-verification-code")
async def send_verification_code(request, db):
    # 旧逻辑: 直接调用 mail.send...
    
    # 新逻辑: 执行工作流
    workflow_service = WorkflowService(db)
    success, result = await workflow_service.execute_system_workflow(
        "auth_send_verification",
        trigger_data={"email": request.email, "purpose": request.purpose}
    )
    if not success:
        raise HTTPException(...)
```

修改 `backend/crud/user.py` 或 `auth.py`:

```python
# 在用户创建成功后
new_user = create_user(...)

# 触发新用户入职工作流
# 方式 1: 直接调用 WorkflowService (简单)
workflow_service.execute_system_workflow(
    "user_onboarding",
    trigger_data={"user_id": new_user.id, "email": new_user.email},
    user_id=new_user.id
)

# 方式 2: 发布事件 (解耦，推荐)
event_bus.publish("user.registered", user=new_user)
```

### 3.3 示例工作流集成

在 `user_onboarding` 工作流中，我们可以增加一个自定义节点类型 `action_create_example_data`，或者直接在代码层面处理。

鉴于目前工作流引擎的成熟度，建议由 `user_onboarding` 工作流的执行器（NodeHandler）来处理具体的业务逻辑，或者保留我们在 `auth.py` 中直接调用 `create_example_workflow` 的逻辑，作为注册成功后的固定步骤之一，而不完全依赖动态工作流（除非我们将"创建示例工作流"也做成一个工作流节点）。

**建议方案**：将"创建示例工作流"做成一个专门的 `integration` 节点 `integration_init_user_data`。

## 4. UI 交互设计 (指定模板)

用户问："发送什么邮件？不需要指定吗？"

需要在前端工作流编辑器 (`frontend/app/components/settings/AutomationRuleEditor.vue` 的对应组件) 增强体验：

1.  **节点配置面板**: 当选中 `action_send_template` 节点时。
2.  **模板选择器**:
    *   字段: `Template Code`
    *   控件: `<Select>` (下拉框)
    *   数据源: 调用 API `/api/email-templates` 获取所有可用模板。
    *   展示: 显示模板名称 (如 "注册验证码") 而不仅仅是代码 (`verification_code_register`)。
3.  **参数映射**:
    *   如果模板中有变量 `{{code}}`，配置面板应自动显示输入框让用户映射该变量的数据来源（例如映射到 `steps.generate_code.output.code`）。

## 5. 实施计划

1.  **数据层**: 更新 `init_workflow_data.py`，拆分注册工作流。
2.  **后端**:
    *   实现 API `/api/email-templates/options` 供前端下拉选择。
    *   修改 `auth.py` 对接 `auth_send_verification` 工作流。
    *   在注册成功后触发 `user_onboarding` 工作流。
    *   实现 `WorkflowService` 对异步事件触发的支持（目前先做同步调用）。
3.  **前端**:
    *   修改节点配置面板，支持从下拉框选择邮件模板。
    *   支持变量映射 UI (这比较复杂，现阶段可以先用简单的 Key-Value 输入框)。
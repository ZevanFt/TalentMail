# 统一工作流与模板系统架构设计 (Unified Workflow & Template System Design)

## 1. 核心愿景与痛点分析

当前系统存在“两张皮”现象：邮件模板系统与自动化工作流系统虽然各自独立运行尚可，但在结合部存在严重体验断层。

| 痛点 |现状 | 目标 |
|---|---|---|
| **变量映射** | 黑盒操作，靠猜变量名，无类型提示 | **强类型契约**：模板声明所需变量，工作流自动生成表单 |
| **多语言** | 依赖纯文本替换，无结构化 Locale 支持 | **原生多语言**：同一模板 Code 对应多语言版本，自动根据收件人偏好分发 |
| **编辑器** | 简陋文本框，不支持复杂排版 | **所见即所得**：集成高级可视化编辑器，支持图片拖拽、组件化 |
| **数据流** | 参数传递全靠写死 JSON | **可视化数据流**：支持从上游节点（如触发器）拖拽数据到模板变量 |

## 2. 架构层级重构

### 2.1 数据模型层 (Model Layer)

我们需要增强 `TemplateMetadata` 和 `EmailTemplate` 的职责。

#### 2.1.1 增强的模板定义 (EmailTemplate)
不再只是 title/body，增加：
*   `locale`: `zh-CN` | `en-US` (联合主键: `code` + `locale`)
*   `version`: 支持版本回滚
*   `editor_type`: `rich_text` | `markdown` | `drag_drop_builder` (为未来可视化构建器预留)

#### 2.1.2 严格的契约定义 (TemplateSchema)
模板不仅仅是 HTML，它必须包含一个 **Schema**（类似 Function Calling 定义）：
```json
{
  "code": "reset_password",
  "inputs": [
    { "key": "user_name", "type": "string", "label": "用户名称" },
    { "key": "reset_link", "type": "url", "label": "重置链接" },
    { "key": "valid_minutes", "type": "number", "label": "有效期(分)" }
  ],
  "preview_data": { ... } // 用于编辑器内实时预览的 mock 数据
}
```

### 2.2 逻辑层 (Logic Layer)

#### 2.2.1 智能模板解析器 (Smart Template Resolver)
在 `MailService` 中引入解析策略：
1.  **输入**：`template_code`, `target_user_id`, `context_data`
2.  **Locale 探测**：优先检查 `target_user.locale` -> 其次检查系统默认 Locale -> 最后回退到英文。
3.  **变量校验**：根据 Schema 校验 `context_data` 是否缺失必填项，缺失则报警。

#### 2.2.2 工作流节点运行时 (Node Runtime)
增强 `action_send_template` 节点：
*   **不仅仅是发送**：它是一个“数据转换器”。
*   **运行时逻辑**：
    1.  获取上游所有可用变量（Variable Context）。
    2.  读取配置的映射规则（Mapping Config）。
    3.  转换数据格式。
    4.  调用 MailService。

### 2.3 前端交互层 (UI Layer)

这是本次重构的**重中之重**。

#### 2.3.1 模板编辑器升级
*   集成 **Tiptap** 或 **Quill** 的高级封装版本。
*   **侧边栏变量池**：显示当前模板定义的 Schema 变量（如 `{{user_name}}`），支持点击插入，而不是手写 `{{`。
*   **实时多语言切换**：在编辑器顶部 tab 切换 `中文` / `English`，实时对比预览。

#### 2.3.2 工作流节点配置面板 (Node Configuration)
当用户在 Vue Flow 中选中“发送邮件”节点时，配置面板应如下运作：

1.  **选择模板**：下拉框选择（按分类分组），不仅仅显示 Code，显示中文名称。
2.  **自动生成表单**：选中 "重置密码" 模板后，面板下方**自动**渲染出三个输入框：
    *   `用户名称`：[ 变量选择器 ] (列出上游节点的输出，如 `trigger.user.name`)
    *   `重置链接`：[ 表达式编辑器 ] (支持拼接字符串，如 `"https://..." + trigger.code`)
    *   `有效期`：[ 静态值输入 ] (默认 15)
3.  **校验提示**：如果必填变量未映射，节点显示红色警告状态。

## 3. 实施路线图

### 阶段一：基础架构重构 (Backend)
1.  修改 `EmailTemplate` 模型，增加 `locale` 字段，调整唯一约束。
2.  完善 `TemplateMetadata` 表，正式引入 `schema` 字段存储 JSON 定义。
3.  重写 `MailService.send_template_email`，支持 locale 自动降级策略。

### 阶段二：前端组件开发 (Frontend Components)
1.  开发 `SchemaFormBuilder` 组件：根据 JSON Schema 自动生成带变量选择器的表单。
2.  开发 `VariablePicker` 组件：一个弹出的 Tree View，展示工作流上下文中的所有可用变量（Trigger Outputs, Step Outputs）。
3.  集成 `RichTextEditor`：支持变量胶囊化显示（类似 Notion 的变量引用）。

### 阶段三：集成与验证 (Integration)
1.  在工作流编辑器中集成上述组件。
2.  迁移旧的系统模板（Auth, Notification）到新的 Schema 结构。
3.  端到端测试：从“触发器接收数据” -> “节点映射变量” -> “渲染多语言邮件” -> “最终发送”。

## 4. 示例数据流

**场景**：新用户注册欢迎邮件

1.  **Trigger (user_registered)**
    *   Output: `user { id, name, email, locale='zh-CN' }`

2.  **Action Node (Send Welcome)**
    *   Config (Selected Template: `welcome_v2`)
    *   Schema Requirement: `{{name}}`, `{{login_url}}`
    *   **Mapping**:
        *   `name` <= `Trigger.user.name`
        *   `login_url` <= `Global.system_url` + `"/login"`

3.  **Execution**
    *   System detects user locale is `zh-CN`.
    *   Loads `welcome_v2` (zh-CN variant).
    *   Renders with mapped data.
    *   Sends email.

## 5. 总结

本次设计不只是修补 Bug，而是将传统的“字符串模板”升级为“**结构化、契约化、智能化**”的内容分发系统。这将彻底解决“数据传递不直观”和“多语言支持缺失”的问题。
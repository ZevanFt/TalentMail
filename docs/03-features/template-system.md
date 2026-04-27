# 模板系统文档

## 概览

TalentMail 有两套独立的模板系统：

1. **系统邮件模板** (Email Templates) — 管理员管理，用于系统通知、自动化邮件
2. **用户写信模板** (Compose Templates) — 用户自定义，用于快速插入常用邮件内容

## 系统邮件模板

### 数据模型

```python
class EmailTemplate:
    id: int
    code: str          # 唯一标识码 (如 "welcome_email")
    name: str          # 显示名称
    category: str      # 分类 (auth/notification/collaboration/finance/hr/marketing/customer/custom)
    description: str   # 描述
    subject: str       # 邮件主题 (支持变量)
    body_html: str     # HTML 正文 (支持变量)
    variables: list    # 变量列表
    is_active: bool    # 是否启用
```

### 分类

| 分类 | 标识 | 用途 |
|------|------|------|
| 认证相关 | `auth` | 注册验证、密码重置 |
| 系统通知 | `notification` | 系统公告、账户状态变更 |
| 协作分享 | `collaboration` | 文件分享、邀请 |
| 财务通知 | `finance` | 账单、订阅到期 |
| 人事通知 | `hr` | 团队管理 |
| 营销推广 | `marketing` | 产品推广 |
| 客户服务 | `customer` | 工单回复 |
| 自定义 | `custom` | 用户自定义分类 |

### 变量系统

模板支持 `{{variable_name}}` 格式的变量占位符：

```html
<h1>您好，{{user_name}}</h1>
<p>您的验证码是: <strong>{{code}}</strong></p>
<p>有效期: {{expire_minutes}} 分钟</p>
```

### 变量元数据

每个变量可定义：

```json
{
  "key": "user_name",
  "label": "用户名称",
  "type": "text",
  "example": "张三",
  "required": true
}
```

支持的类型: `text`, `number`, `email`, `url`, `textarea`

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/email-templates` | 列出所有模板 |
| `POST` | `/api/email-templates` | 创建模板 (管理员) |
| `PUT` | `/api/email-templates/{id}` | 更新模板 (管理员) |
| `DELETE` | `/api/email-templates/{id}` | 删除模板 (管理员) |
| `GET` | `/api/email-templates/{code}/metadata` | 获取模板元数据 |
| `POST` | `/api/email-templates/{id}/preview` | 预览渲染结果 |
| `POST` | `/api/email-templates/{id}/test-send` | 测试发送 |

### 在工作流中使用

工作流的「发送邮件」节点可选择模板：

```json
{
  "type": "send_email",
  "config": {
    "template_code": "welcome_email",
    "variables": {
      "user_name": "{{trigger.user.name}}",
      "activation_url": "{{trigger.activation_url}}"
    }
  }
}
```

## 用户写信模板

### 数据模型

```python
class UserTemplate:
    id: int
    user_id: int       # 所属用户
    name: str          # 模板名称
    subject: str       # 默认主题
    body_html: str     # HTML 正文
    category: str      # 用户自定义分类
    is_default: bool   # 是否默认
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/templates` | 列出用户的模板 |
| `POST` | `/api/templates` | 创建模板 |
| `PUT` | `/api/templates/{id}` | 更新模板 |
| `DELETE` | `/api/templates/{id}` | 删除模板 |

### 前端集成

在 ComposePanel 中，通过 `TemplateSelector` 组件实现：

1. 点击「使用模板」按钮打开下拉列表
2. 搜索 / 按分类浏览模板
3. 选择模板后填写变量
4. 点击「应用模板」渲染并填入编辑器

```vue
<TemplateSelector
  :compact="true"
  :toolbar="true"
  @select="handleTemplateSelect"
  @clear="handleTemplateClear"
/>
```

## 两套模板的区别

| 特性 | 系统邮件模板 | 用户写信模板 |
|------|-------------|-------------|
| 管理者 | 管理员 | 普通用户 |
| 用途 | 系统自动化邮件 | 手动写信快捷插入 |
| 变量 | 有元数据定义 | 无变量系统 |
| 预览 | 服务端渲染 | 直接使用内容 |
| 工作流 | 可在工作流中引用 | 不支持 |
| 测试发送 | 支持 | 不支持 |

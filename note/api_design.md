# API 设计文档 (V1)

本 文档定义了 TalentMail 项目的后端 API 接口。

**基础 URL**: `/talent`

---

## 零、通用设计

### 0.1 HTTP 状态码与响应结构的关系
我们采用**HTTP状态码**和**自定义响应体**协同工作的模式。
- **HTTP 状态码**: 用于表示请求的宏观状态 (成功, 客户端错误, 服务端错误)，遵循标准定义。
- **自定义响应体**: 用于提供详细的、业务相关的处理结果。

### 0.2 统一响应结构
**成功**:
```json
{
  "status": "success",
  "data": { ... } // 具体业务数据
}
```
**失败**:
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "具体的错误描述."
  }
}
```

### 0.3 响应示例 (Response Examples)
**成功示例: `GET /talent/users/me`**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "data": { "id": 1, "email": "user@example.com" }
}
```
**失败示例: `POST /talent/auth/login` (密码错误)**
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "status": "error",
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "邮箱或密码错误。"
  }
}
```

---

## 模块一: 用户认证 (Authentication)
*路径前缀: `/auth`*

### 1.1 用户注册
**Endpoint**: `POST /auth/register`
**请求体**:
```json
{
  "email": "user@example.com",
  "password": "a_strong_password",
  "display_name": "My Username",
  "phone": "18888888888",
  "redemption_code": "VIP-CODE-123"
}
```
**成功响应 (201 Created)**:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "My Username"
  }
}
```

### 1.2 用户登录
**Endpoint**: `POST /auth/login`
**请求体**:
```json
{
  "email": "user@example.com",
  "password": "a_strong_password"
}
```
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "access_token": "ey...",
    "refresh_token": "ey...",
    "token_type": "bearer"
  }
}
```

### 1.3 根据手机号查询关联账户
**Endpoint**: `POST /auth/accounts-for-phone`
**请求体**:
```json
{
  "phone": "18888888888"
}
```
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "accounts": [
      { "email": "user1@example.com", "display_name": "User One" },
      { "email": "user2@example.com", "display_name": "User Two" }
    ]
  }
}
```

### 1.4 刷新令牌
**Endpoint**: `POST /auth/refresh`
**请求体**:
```json
{
  "refresh_token": "ey..."
}
```
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "access_token": "ey...",
    "token_type": "bearer"
  }
}
```

### 1.5 获取当前用户信息
**Endpoint**: `GET /users/me`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "My Username",
    "role": "user"
  }
}
```

---

## 模块二: 邮件 (Emails)
*路径前缀: `/emails`*

### 2.1 获取邮件列表
**Endpoint**: `GET /emails`
**查询参数**: `folder_id`, `tag_id`, `is_starred`, `q`, `page`, `limit`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": 123,
        "subject": "Hello World",
        "sender": "from@example.com",
        "is_read": true,
        "is_starred": false,
        "received_at": "...",
        "has_attachments": true
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 50
  }
}
```

### 2.2 获取单封邮件详情
**Endpoint**: `GET /emails/{email_id}`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "id": 123,
    "subject": "Hello World",
    "sender": "from@example.com",
    "recipients": ["to@example.com"],
    "body_html": "...",
    "attachments": [
      { "id": 1, "filename": "invoice.pdf", "size_bytes": 12345 }
    ]
  }
}
```

### 2.3 发送/保存邮件
**Endpoint**: `POST /emails`
**请求体**:
```json
{
  "to": ["recipient@example.com"],
  "subject": "New Email",
  "body_html": "<h1>Hello</h1>",
  "action": "send"
}
```
**成功响应 (202 Accepted for send, 201 Created for draft)**

### 2.4 更新邮件状态 (批量)
**Endpoint**: `PATCH /emails`
**请求体**:
```json
{
  "email_ids": [123, 124],
  "action": { "move_to_folder": 5 }
}
```
**成功响应 (200 OK)**

---

## 模块三: 文件夹 (Folders)
*路径前缀: `/folders`*

### 3.1 获取文件夹列表
**Endpoint**: `GET /folders`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": [
    { "id": 1, "name": "Inbox", "role": "system", "unread_count": 5 },
    { "id": 2, "name": "Work", "role": "user", "unread_count": 2 }
  ]
}
```

### 3.2 创建文件夹
**Endpoint**: `POST /folders`
**请求体**:
```json
{
  "name": "Project X",
  "parent_id": 2
}
```
**成功响应 (201 Created)**

### 3.3 更新文件夹
**Endpoint**: `PUT /folders/{folder_id}`
**请求体**:
```json
{
  "name": "Project Y"
}
```
**成功响应 (200 OK)**

### 3.4 删除文件夹
**Endpoint**: `DELETE /folders/{folder_id}`
**成功响应 (204 No Content)**

---

## 模块四: 标签 (Tags)
*路径前缀: `/tags`*

### 4.1 获取标签列表
**Endpoint**: `GET /tags`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": [
    { "id": 1, "name": "Work", "color": "#4A90E2" },
    { "id": 2, "name": "Urgent", "color": "#D0021B" }
  ]
}
```

### 4.2 创建标签
**Endpoint**: `POST /tags`
**请求体**:
```json
{
  "name": "Finance",
  "color": "#F5A623"
}
```
**成功响应 (201 Created)**

### 4.3 更新标签
**Endpoint**: `PUT /tags/{tag_id}`
**请求体**:
```json
{
  "name": "Financial",
  "color": "#F8E71C"
}
```
**成功响应 (200 OK)**

### 4.4 删除标签
**Endpoint**: `DELETE /tags/{tag_id}`
**成功响应 (204 No Content)**

### 4.5 为邮件批量打标签/移除标签
**Endpoint**: `POST /emails/tags`
**描述**: 为多封邮件添加或移除一个标签。
**请求体**:
```json
{
  "email_ids": [123, 124],
  "tag_id": 2,
  "action": "add" // or "remove"
}
```
**成功响应 (200 OK)**

---

## 模块五: 设置 (Settings)

### 5.1 个人资料 (Profile)

**Endpoint**: `PUT /users/me/profile`
**描述**: 更新当前用户的个人资料。
**请求体**:
```json
{
  "display_name": "New Name",
  "avatar_url": "https://example.com/new_avatar.png"
}
```
**成功响应 (200 OK)**

### 5.2 修改密码 (Security)

**Endpoint**: `PUT /users/me/password`
**描述**: 修改当前用户的密码。
**请求体**:
```json
{
  "current_password": "old_password",
  "new_password": "a_very_strong_new_password"
}
```
**成功响应 (204 No Content)**
**失败响应**:
- `400 Bad Request`: 新密码太弱。
- `401 Unauthorized`: 当前密码错误。

### 5.3 域名管理 (Domains)
*路径前缀: `/domains`*

#### 5.3.1 获取域名列表
**Endpoint**: `GET /domains`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "domain_name": "talenting.vip",
      "is_verified": true,
      "created_at": "..."
    },
    {
      "id": 2,
      "domain_name": "example.com",
      "is_verified": false,
      "created_at": "..."
    }
  ]
}
```

#### 5.3.2 添加域名
**Endpoint**: `POST /domains`
**请求体**:
```json
{
  "domain_name": "new-domain.com"
}
```
**成功响应 (201 Created)**: 返回新创建的域名信息，包含需要设置的 DNS 记录。
```json
{
  "status": "success",
  "data": {
    "id": 3,
    "domain_name": "new-domain.com",
    "is_verified": false,
    "verification_records": {
      "dkim": {
        "type": "TXT",
        "host": "mail._domainkey",
        "value": "v=DKIM1; k=rsa; p=..."
      },
      "spf": {
        "type": "TXT",
        "host": "@",
        "value": "v=spf1 include:mail.talenting.vip ~all"
      }
    }
  }
}
```

#### 5.3.3 删除域名
**Endpoint**: `DELETE /domains/{domain_id}`
**成功响应 (204 No Content)**

#### 5.3.4 触发域名验证
**Endpoint**: `POST /domains/{domain_id}/verify`
**描述**: 请求后端去检查该域名的 DNS 记录是否已正确设置。
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "is_verified": true, // or false
    "message": "DKIM record verified. SPF record pending."
  }
}
```

### 5.4 邮箱别名管理 (Aliases)
*路径前缀: `/aliases`*

#### 5.4.1 获取别名列表
**Endpoint**: `GET /aliases`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "email": "info@talenting.vip",
      "display_name": "Info",
      "domain_id": 1,
      "is_default": true
    },
    {
      "id": 2,
      "email": "support@talenting.vip",
      "display_name": "Support Team",
      "domain_id": 1,
      "is_default": false
    }
  ]
}
```

#### 5.4.2 创建别名
**Endpoint**: `POST /aliases`
**请求体**:
```json
{
  "local_part": "ceo",
  "domain_id": 1,
  "display_name": "CEO Office"
}
```
**成功响应 (201 Created)**

#### 5.4.3 更新别名
**Endpoint**: `PUT /aliases/{alias_id}`
**请求体**:
```json
{
  "display_name": "CEO",
  "is_default": true // (可选) 设为默认发信地址
}
```
**成功响应 (200 OK)**

#### 5.4.4 删除别名
**Endpoint**: `DELETE /aliases/{alias_id}`
**成功响应 (204 No Content)**

### 5.5 邮件签名管理 (Signatures)
*路径前缀: `/signatures`*

#### 5.5.1 获取签名列表
**Endpoint**: `GET /signatures`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Work Signature",
      "content_html": "<b>John Doe</b><br>CEO, Talent Inc.",
      "is_default": true
    }
  ]
}
```

#### 5.5.2 创建签名
**Endpoint**: `POST /signatures`
**请求体**:
```json
{
  "name": "Personal Signature",
  "content_html": "Cheers,<br>John"
}
```
**成功响应 (201 Created)**

#### 5.5.3 更新签名
**Endpoint**: `PUT /signatures/{signature_id}`
**请求体**:
```json
{
  "name": "Work Sig",
  "content_html": "<b>John Doe</b><br>Chief Executive Officer, Talent Inc.",
  "is_default": true
}
```
**成功响应 (200 OK)**

#### 5.5.4 删除签名
**Endpoint**: `DELETE /signatures/{signature_id}`
**成功响应 (204 No Content)**

### 5.6 邮件过滤器管理 (Filters)
*路径前缀: `/filters`*

#### 5.6.1 获取过滤器列表
**Endpoint**: `GET /filters`
**成功响应 (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Archive Newsletters",
      "conditions": [
        { "field": "from", "operator": "contains", "value": "newsletter@" }
      ],
      "actions": [
        { "action": "move_to_folder", "value": 10 }, // 10 is Archive folder ID
        { "action": "mark_as_read", "value": true }
      ],
      "is_active": true
    }
  ]
}
```

#### 5.6.2 创建过滤器
**Endpoint**: `POST /filters`
**请求体**:
```json
{
  "name": "Urgent from Boss",
  "conditions": [
    { "field": "from", "operator": "equals", "value": "boss@talenting.vip" }
  ],
  "actions": [
    { "action": "add_tag", "value": 2 } // 2 is Urgent tag ID
  ]
}
```
**成功响应 (201 Created)**

#### 5.6.3 更新过滤器
**Endpoint**: `PUT /filters/{filter_id}`
**请求体**: (与创建时类似)

**成功响应 (200 OK)**

#### 5.6.4 删除过滤器
**Endpoint**: `DELETE /filters/{filter_id}`

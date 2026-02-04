# 代码开发规范

本文档定义了 TalentMail 项目的核心开发原则和编码规范。**所有开发者必须严格遵守这些原则。**

## 🔴 核心开发原则（必须遵守）

### 1. 零硬编码原则

**绝对禁止在代码中硬编码任何配置值。**

❌ **错误示例**：
```python
# 坚决不要这样做！
smtp_server = "maillink.talenting.test"  # 硬编码
max_file_size = 10485760  # 魔法数字
email_domain = "talenting.test"  # 硬编码域名
```

✅ **正确示例**：
```python
# 从配置文件读取
smtp_server = settings.MAIL_SERVER
max_file_size = settings.MAX_UPLOAD_SIZE
email_domain = settings.BASE_DOMAIN

# 或使用常量
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
```

**实施要点**：
- 所有配置项必须通过环境变量或配置文件管理
- 使用有意义的常量名称
- 配置项必须有默认值和文档说明
- 敏感信息必须通过环境变量传递

### 2. 完整实现原则

**功能要么不做，要做就做完整。**

❌ **禁止事项**：
```python
# 绝对不要留 TODO
def send_email():
    # TODO: 实现邮件发送
    pass

# 不要留半成品
def search_emails(query):
    # 只实现了简单搜索，复杂搜索待实现
    return simple_search(query)

# 不要写伪代码
def process_workflow():
    # 伪代码：这里应该处理工作流
    # step1: 获取节点
    # step2: 执行节点
    # step3: 保存结果
    pass
```

✅ **正确做法**：
```python
def send_email(to: str, subject: str, body: str) -> bool:
    """
    发送邮件的完整实现

    Args:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文

    Returns:
        bool: 发送成功返回 True

    Raises:
        SMTPException: SMTP 服务器错误
        ValidationError: 参数验证失败
    """
    # 1. 参数验证
    validate_email(to)
    if not subject:
        raise ValidationError("邮件主题不能为空")

    # 2. 构建邮件
    message = MIMEText(body)
    message['To'] = to
    message['Subject'] = subject

    # 3. 发送邮件
    try:
        with get_smtp_connection() as smtp:
            smtp.send_message(message)
        return True
    except SMTPException as e:
        logger.error(f"邮件发送失败: {e}")
        raise
```

**实施要求**：
- 每个函数必须有完整的实现
- 必须处理所有边缘情况
- 必须有适当的错误处理
- 必须有单元测试覆盖

### 3. 代码即法律原则

**先读懂现有代码，遵循既定模式。**

**必须做到**：
1. **先读代码再动手**
   - 理解现有架构
   - 查看相似功能的实现
   - 遵循项目约定

2. **不猜测，不臆断**
   - 不确定就查文档
   - 不清楚就看代码
   - 有疑问就测试验证

3. **基于现有架构**
   ```python
   # 如果项目使用 FastAPI 的依赖注入
   # 新功能也必须遵循相同模式
   @router.post("/emails/send")
   async def send_email(
       email_data: EmailCreate,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       # 遵循既定的服务层架构
       return await email_service.send_email(db, current_user, email_data)
   ```

4. **保持一致性**
   - 命名规范一致
   - 代码风格一致
   - 错误处理一致
   - API 设计一致

### 4. 不留烂摊子原则

**代码提交前必须确保所有功能完整可用。**

✅ **必须完成的检查清单**：

1. **所有功能都要测试**
   ```python
   # 每个新功能必须有对应的测试
   def test_password_encryption():
       # 测试加密功能
       password = "test_password"
       encrypted = encrypt_password(password)
       assert encrypted != password
       assert decrypt_password(encrypted) == password

   def test_password_encryption_with_special_chars():
       # 测试特殊字符
       password = "p@$$w0rd!#"
       encrypted = encrypt_password(password)
       assert decrypt_password(encrypted) == password
   ```

2. **所有 API 都要对接**
   - 后端 API 必须有对应的前端调用
   - 前端功能必须连接真实 API
   - 不允许存在孤立的端点

3. **所有格式都要转换**
   ```python
   # 日期格式必须统一
   def format_datetime(dt: datetime) -> str:
       """统一的日期时间格式化"""
       return dt.strftime("%Y-%m-%d %H:%M:%S")

   # 数据格式必须匹配
   def to_response(email: Email) -> EmailResponse:
       """确保响应格式符合前端要求"""
       return EmailResponse(
           id=str(email.id),  # UUID 转字符串
           created_at=format_datetime(email.created_at),
           # ... 其他字段
       )
   ```

4. **所有链路都要打通**
   - 用户操作 → 前端界面 → API 调用 → 后端处理 → 数据库操作 → 响应返回
   - 每个环节都必须测试
   - 错误处理必须完整

## 📋 开发流程检查清单

在提交代码前，必须确认：

- [ ] 没有硬编码的配置值
- [ ] 没有 TODO 注释
- [ ] 没有注释掉的代码
- [ ] 所有函数都有完整实现
- [ ] 所有函数都有文档字符串
- [ ] 遵循了项目既有的代码风格
- [ ] 编写了单元测试
- [ ] 测试覆盖率达到 80%
- [ ] API 已与前端对接
- [ ] 错误处理完整
- [ ] 日志记录适当
- [ ] 性能可接受
- [ ] 安全性已考虑

## 🛠️ 实用工具和技巧

### 1. 配置管理
```python
# backend/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """集中管理所有配置"""
    # 数据库配置
    DATABASE_URL: str

    # 邮件服务器配置
    MAIL_SERVER: str = "localhost"
    SMTP_PORT: int = 587

    # 安全配置
    SECRET_KEY: str
    ENCRYPTION_KEY: str

    class Config:
        env_file = ".env"
```

### 2. 完整性检查
```python
# 使用装饰器确保实现完整
def ensure_implemented(func):
    """确保函数已实现"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is NotImplemented:
            raise NotImplementedError(f"{func.__name__} 未实现")
        return result
    return wrapper
```

### 3. 代码一致性工具
```bash
# 使用 black 格式化 Python 代码
black backend/

# 使用 isort 整理导入
isort backend/

# 使用 prettier 格式化前端代码
npm run format

# 运行 linter
npm run lint
```

## ⚠️ 违反原则的后果

1. **代码审查不通过** - PR 将被拒绝
2. **重新实现** - 必须按原则重写
3. **技术债务** - 记录并限期改正

## 📚 相关文档

- [当前开发任务](../06-roadmap/current-tasks.md)
- [测试指南](./testing-guide.md)
- [API 设计规范](../02-architecture/api-design.md)

---

**记住：宁可不做，也不要做一半。代码质量是我们的生命线。**

最后更新：2025-02-01
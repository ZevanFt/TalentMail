# 当前开发任务

本文档记录当前正在进行的开发任务和进度，用于跟踪项目进展和指导开发工作。

> 📅 最后更新：2025-02-03
> 👤 负责人：开发团队

## 🎯 当前开发周期：2025年2月

### 本月目标
1. 完成所有安全性修复
2. 实现核心功能增强（搜索、过滤、批量操作）
3. 开始工作流引擎升级

## 📊 任务进度跟踪

### 第一阶段：安全性和稳定性（2月3日-2月10日）

#### 1. 密码加密存储 🔴
- **状态**：`已完成` ✅
- **优先级**：高
- **完成日期**：2025-02-01
- **负责人**：Assistant
- **相关文件**：
  - `backend/api/external_accounts.py:226`
  - `backend/api/external_accounts.py:254`

**已完成的任务**：
- ✅ 创建加密工具模块 `backend/core/crypto.py`
- ✅ 使用 cryptography 库的 Fernet 算法
- ✅ 实现密码加密/解密函数
- ✅ 更新外部账户创建和更新逻辑
- ✅ 编写数据迁移脚本 `backend/scripts/migrate_external_passwords.py`
- ✅ 添加单元测试 `backend/tests/test_crypto.py`
- ✅ 更新 API 文档（.env.example）
- ✅ 添加 ENCRYPTION_KEY 配置项

**实现亮点**：
1. **零硬编码**：加密密钥从环境变量读取
2. **完整实现**：包含加密、解密、密钥生成、数据迁移
3. **错误处理**：完善的异常处理和错误提示
4. **向后兼容**：迁移脚本可以安全处理已加密的数据
5. **安全考虑**：开发环境警告、密钥验证、Unicode支持

**代码质量**：
- 完整的文档字符串
- 类型注解
- 单例模式避免重复初始化
- 便捷函数提供简单接口

---

#### 2. 会话识别功能 🔴
- **状态**：`已完成` ✅
- **优先级**：高
- **完成日期**：2025-02-03
- **负责人**：Assistant
- **相关文件**：
  - `backend/api/users.py`
  - `backend/api/deps.py`
  - `backend/api/auth.py`
  - `backend/core/security.py`
  - `backend/schemas/schemas.py`

**已完成的任务**：
- ✅ 在 JWT payload 中添加 session_id
- ✅ 修改登录逻辑，在 token 中包含 session.id
- ✅ 更新 TokenData schema 添加 session_id 字段
- ✅ 创建 get_current_session_id 依赖函数
- ✅ 更新会话列表 API 支持 is_current 标识
- ✅ 测试验证通过

**实现要点**：
```python
# 在 JWT token 中添加 session_id
token_data = {
    "sub": user.id,
    "email": user.email,
    "session_id": session.id,  # 新增
    "exp": expire
}

# 判断是否当前会话
is_current = current_session_id == session.id
```

---

#### 3. 敏感配置加密 🔴
- **状态**：`已完成` ✅
- **优先级**：中
- **完成日期**：2025-02-03
- **负责人**：Assistant

**已完成的任务**：
- ✅ 设计配置加密方案
- ✅ 实现配置加密/解密模块 `scripts/config_encrypt.py`
- ✅ 支持 encrypt/decrypt 单个值
- ✅ 支持 encrypt-file/decrypt-file 整个 .env 文件
- ✅ 支持 generate-key 生成新密钥
- ✅ 支持 verify 验证配置

---

### 第二阶段：核心功能增强（2月10日-2月24日）

#### 1. 邮件全文搜索 🔴
- **状态**：`已完成` ✅
- **优先级**：高
- **完成日期**：2025-02-03
- **负责人**：Assistant
- **技术选型**：PostgreSQL 全文搜索

**已完成的任务**：
- ✅ 创建全文搜索数据库迁移 `alembic/versions/2d0614e710cb_add_email_fulltext_search.py`
- ✅ 添加 search_vector 列（tsvector 类型）
- ✅ 创建 GIN 索引加速搜索
- ✅ 创建自动更新触发器
- ✅ 初始化现有邮件的搜索向量
- ✅ 更新 Email 模型添加 search_vector 列
- ✅ 重构搜索 API 使用 plainto_tsquery
- ✅ 按相关性排序（ts_rank）
- ✅ 测试验证通过（25封邮件全部索引）

**实现亮点**：
1. **使用 'simple' 配置**：支持多语言内容（中英文）
2. **权重分配**：主题(A) > 发件人(B) > 正文(C)
3. **自动更新**：触发器确保新邮件自动索引
4. **性能优化**：GIN 索引大幅提升搜索速度

---

#### 2. 垃圾邮件过滤 🔴
- **状态**：`已完成` ✅
- **优先级**：高
- **完成日期**：2025-02-03
- **负责人**：Assistant

**已完成的任务**：
- ✅ 创建 `api/spam.py` 垃圾邮件管理 API
- ✅ 添加白名单模型 (TrustedSender)
- ✅ 添加垃圾邮件报告模型 (SpamReport)
- ✅ 实现标记垃圾/非垃圾邮件功能
- ✅ 白名单管理（增删查）
- ✅ 后台任务训练 SpamAssassin

---

#### 3. 批量操作功能 🔴
- **状态**：`已完成` ✅
- **优先级**：中
- **完成日期**：2025-02-03
- **负责人**：Assistant

**已完成的任务**：
- ✅ 批量操作 API 设计
- ✅ 实现批量标记已读/未读 `/bulk/read`
- ✅ 实现批量标记星标 `/bulk/star`
- ✅ 实现批量移动 `/bulk/move`
- ✅ 实现批量删除 `/bulk/delete`
- ✅ 实现批量归档 `/bulk/archive`
- ✅ 统一的响应格式（success_count, failed_count, failed_ids）

---

### 第三阶段：工作流引擎升级（2月24日-3月15日）

#### 1. 执行引擎重构 🔴
- **状态**：`已完成` ✅
- **优先级**：高
- **完成日期**：2025-02-03
- **负责人**：Assistant
- **相关文件**：
  - `backend/core/workflow_runtime.py`
  - `backend/core/workflow_service.py`

**已完成的任务**：
- ✅ 重构 WorkflowEngine 支持图遍历
- ✅ 新增 GraphExecutor 类处理复杂流程
- ✅ 支持条件分支（通过 source_handle 匹配）
- ✅ 支持并行执行（同一层级多节点）
- ✅ 新增 WorkflowEdge 数据结构
- ✅ 更新 WorkflowContext 支持输出端口记录
- ✅ 保持向后兼容（旧版 next_node_id）
- ✅ 更新 ConditionHandler 返回 _output_handle
- ✅ 添加邮件操作处理器（标星、标记已读、转发）
- ✅ 测试验证条件分支功能

**实现亮点**：
1. **BFS 图遍历**：使用广度优先搜索执行工作流
2. **条件分支**：通过 source_handle 匹配决定执行路径
3. **并行执行**：asyncio.gather 同时执行多个节点
4. **完全向后兼容**：旧版工作流无需修改

---

#### 2. 高级节点类型 🟡
- **状态**：`已完成` ✅
- **优先级**：中
- **完成日期**：2025-02-03
- **负责人**：Assistant
- **相关文件**：
  - `backend/core/workflow_service.py`

**已完成的节点开发**：
- ✅ DelayHandler - 延时等待节点
- ✅ LoopHandler - 循环执行节点
- ✅ ParallelHandler - 并行执行节点
- ✅ SwitchHandler - 多路分支节点（switch-case）
- ✅ WebhookHandler - Webhook 调用节点
- ✅ TransformHandler - 数据转换节点

**实现亮点**：
1. **延时节点**：支持秒/分钟延时和指定时间等待
2. **Webhook 节点**：支持 GET/POST/PUT/DELETE，自动解析 JSON
3. **数据转换**：支持 filter/map/sort/limit/count 操作

---

## 📋 开发规范要求

### ⚠️ 核心原则（必须遵守）
**详见**：[代码开发规范](../04-development/coding-standards.md)

1. **零硬编码原则** - 禁止任何硬编码配置
2. **完整实现原则** - 不留 TODO，功能必须完整
3. **代码即法律原则** - 遵循既有架构和模式
4. **不留烂摊子原则** - 所有链路必须打通

### 代码规范
1. 所有新功能必须有单元测试
2. 代码覆盖率不低于 80%
3. 使用类型注解（Python）和 TypeScript
4. 遵循项目既定的代码风格

### 文档要求
1. API 变更必须更新 OpenAPI 文档
2. 新功能需要更新用户文档
3. 复杂逻辑需要内联注释
4. 更新相应的 README 文件

### 提交规范
1. 使用语义化提交信息
2. 一个提交只做一件事
3. 提交前运行测试
4. PR 需要通过代码审查

### 提交前检查清单
- [ ] 无硬编码值
- [ ] 无 TODO 注释
- [ ] 功能实现完整
- [ ] 测试通过
- [ ] 前后端已对接
- [ ] 文档已更新

## 🔄 进度更新记录

### 2025-02-03
- ✅ 完成会话识别功能
  - JWT token 中添加 session_id
  - TokenData schema 添加 session_id 字段
  - 会话列表 API 支持 is_current 标识
- ✅ 完成邮件全文搜索功能
  - PostgreSQL 全文搜索（tsvector + GIN 索引）
  - 自动更新触发器
  - 搜索 API 按相关性排序
- ✅ 完成工作流引擎升级
  - 支持条件分支（通过 source_handle）
  - 支持并行执行
  - GraphExecutor 图遍历执行器
  - 完全向后兼容
- ✅ 完成垃圾邮件过滤功能
  - 创建 `api/spam.py` 垃圾邮件管理 API
  - 添加白名单 (TrustedSender) 和报告 (SpamReport) 模型
  - 实现标记垃圾/非垃圾邮件功能
  - 后台任务训练 SpamAssassin
- ✅ 完成批量操作功能
  - 批量标记已读/未读
  - 批量标记星标
  - 批量移动/删除/归档
- ✅ 完成敏感配置加密
  - 创建 `scripts/config_encrypt.py` 配置加密工具
  - 支持加密/解密 .env 文件中的敏感配置
- ✅ 完成高级工作流节点
  - DelayHandler - 延时等待
  - LoopHandler - 循环执行
  - ParallelHandler - 并行执行
  - SwitchHandler - 多路分支
  - WebhookHandler - Webhook 调用
  - TransformHandler - 数据转换
- ✅ 完成工作流系统底层逻辑完善
  - 补全 22 个节点处理器（TriggerHandler, DataValidateHandler, DataUpdateUserHandler, WaitHandler, EndHandler 等）
  - 添加业务代码触发点：user.registered, user.login, password.changed
  - 为 32/34 个节点类型添加 config_schema
  - 更新 init_node_types 支持 config_schema 更新
  - 绑定系统工作流 trigger_event：
    - user_registration → user.registered
    - user_login → user.login
    - password_reset → password.forgot
    - password_changed_notification → password.changed

### 2025-02-01
- ✅ 创建开发任务文档
- ✅ 制定 2月开发计划
- ✅ 记录核心开发原则
- ✅ 完成密码加密存储功能
  - 创建 `core/crypto.py` 加密工具模块
  - 更新 `external_accounts.py` 使用加密
  - 创建数据迁移脚本
  - 编写完整测试用例
  - 更新配置文档

### 待更新...
（每完成一个任务，在此处记录）

## 📝 备注

- 本文档会随着开发进展实时更新
- 每个任务完成后，请更新状态和完成日期
- 遇到阻塞问题，及时在此记录
- 下一次对话可以基于此文档继续开发

---

**相关文档**：
- [待办事项总览](./todo-list.md)
- [项目规划](./README.md)
- [开发指南](../04-development/README.md)
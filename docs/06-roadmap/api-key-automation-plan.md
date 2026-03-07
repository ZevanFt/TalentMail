# API Key 自动化能力开发计划（临时邮箱与验证码）

> 归档日期：2026-03-07  
> 状态：开发中（阶段 A、B 已完成，阶段 C 已启动）  
> 适用范围：TalentMail 自动化脚本访问后端 API（非网页登录态）

## 1. 背景与目标

当前已有临时邮箱与邮件读取能力，但自动化脚本缺少安全、可控的程序化访问入口。  
本计划目标是交付最小可用的 API Key 平台，优先满足以下刚需：

1. 创建临时邮箱
2. 获取临时邮箱邮件
3. 提取邮件中的验证码

## 2. 范围定义

### 2.1 本期范围（MVP）

1. API Key 生命周期管理（创建、列表、吊销）
2. API Key 认证（Bearer）
3. 权限范围（scope）校验
4. 自动化接口（临时邮箱/邮件/验证码）
5. 基础限流与审计
6. OpenAPI 文档与调用示例

### 2.2 非本期范围（后续迭代）

1. 第三方 OAuth 集成
2. 公共开发者门户站点
3. 全量业务 API 开放

## 3. 用户与使用场景

### 3.1 目标用户

1. 自动化脚本开发者（你自己的脚本）
2. 企业内部集成开发者（CI、机器人、业务系统）

### 3.2 典型场景

1. 脚本创建临时邮箱 -> 等待来信 -> 抓取验证码 -> 回填业务系统
2. 定时任务批量检查多个临时邮箱的最新验证码

## 4. 权限模型（最小权限）

本期仅开放自动化所需权限：

1. `temp_mailbox:create`：创建临时邮箱
2. `temp_mailbox:read`：读取临时邮箱列表与详情
3. `temp_mailbox:extend`：延长有效期
4. `temp_mailbox:restore`：恢复邮箱（在恢复窗口内）
5. `temp_email:read`：读取临时邮箱邮件
6. `temp_code:read`：读取结构化验证码结果

## 5. 技术路径

### 5.1 数据模型

基于 `api_keys` 表扩展字段：

1. `key_prefix`（展示前缀）
2. `key_hash`（仅存哈希，禁止明文存储）
3. `scopes`（JSON 或数组）
4. `expires_at`
5. `revoked_at`
6. `last_used_at`
7. `rate_limit_per_minute`
8. `description`

### 5.2 鉴权与权限校验

1. 新增 API Key 认证依赖（解析 `Authorization: Bearer`）
2. 常量时间比较校验 key 哈希
3. 统一 scope 校验装饰器/依赖
4. 认证失败、权限不足、过期、吊销返回标准错误码

### 5.3 自动化 API 命名空间

建议统一前缀：`/api/automation`

1. `POST /api/automation/temp-mailboxes`（创建）
2. `GET /api/automation/temp-mailboxes`（列表）
3. `GET /api/automation/temp-mailboxes/{id}/emails`（邮件列表）
4. `GET /api/automation/temp-mailboxes/{id}/codes/latest`（最新验证码）
5. `POST /api/automation/temp-mailboxes/{id}/extend`（延长）
6. `POST /api/automation/temp-mailboxes/{id}/restore`（恢复）

### 5.4 安全与风控

1. Key 仅在创建时返回一次明文
2. 按 key 限流（令牌桶或固定窗口）
3. 审计日志记录：key_id、user_id、path、method、status、ip、耗时
4. 支持单 key 吊销，不影响其他 key

## 6. 交付阶段与里程碑

### 阶段 A：鉴权基座（1-2 天）

1. 完成 API Key 表结构与迁移
2. 完成创建/列表/吊销接口
3. 完成哈希存储与过期/吊销校验

验收标准：
1. 可创建 key 并仅返回一次明文
2. 已吊销 key 无法调用
3. 过期 key 无法调用

### 阶段 B：自动化接口（1-2 天）

1. 完成临时邮箱创建/列表
2. 完成邮件读取与验证码提取接口
3. 对每个接口接入 scope 校验

验收标准：
1. 脚本可端到端完成“创建邮箱 -> 收取验证码”
2. 未授权 scope 调用返回 403

### 阶段 C：稳定性与文档（1 天）

1. 接入限流与审计
2. 补齐单元测试/集成测试
3. 更新 OpenAPI 与 docs 示例

验收标准：
1. 超限请求返回 429
2. 审计日志可查询调用记录
3. 文档示例可直接跑通

## 7. 测试策略

1. 单元测试：哈希校验、scope 校验、过期/吊销
2. API 测试：正常路径、无权限、无效 key、超限
3. 集成测试：完整验证码抓取链路

### 7.1 闭环联调脚本

已提供脚本：

- `scripts/test_api_key_temp_mailbox_flow.sh`

用途：

1. 登录获取 JWT
2. 创建 API Key
3. 创建临时邮箱
4. 拉取邮件与最新验证码
5. 查询 API Key 审计日志
6. （可选）通过 `Idempotency-Key` 验证创建幂等

示例：

```bash
USER_EMAIL="admin@example.vip" \
USER_PASSWORD="123456" \
BASE_URL="https://mail.example.vip" \
bash scripts/test_api_key_temp_mailbox_flow.sh

# 幂等创建示例（重复执行将复用同一临时邮箱）
USER_EMAIL="admin@example.vip" \
USER_PASSWORD="123456" \
BASE_URL="https://mail.example.vip" \
IDEMPOTENCY_KEY="test-flow-20260307-001" \
bash scripts/test_api_key_temp_mailbox_flow.sh
```

## 8. 风险与应对

1. 权限过宽风险：采用默认拒绝策略，仅白名单 scope 放行
2. Key 泄漏风险：仅显示前缀，支持快速吊销
3. 高频轮询压力：限流 + 推荐后续 webhook 模式

## 9. 实施顺序（执行建议）

1. 先完成阶段 A（认证与权限基座）
2. 再完成阶段 B（临时邮箱自动化能力）
3. 最后阶段 C（稳定性与文档闭环）

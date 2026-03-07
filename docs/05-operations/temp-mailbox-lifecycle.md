# 临时邮箱生命周期与清理策略设计

## 背景

当前临时邮箱仅有 `is_active` 与 `created_at`，缺少系统化生命周期管理，导致：

- 无固定过期时间与倒计时展示；
- 过期后无法恢复与审计；
- 清理策略不可配置、不可手动触发；
- 大量临时邮箱与邮件长期累积。

本设计引入“24 小时有效 + 10 天可恢复 + 系统级清理策略”的完整闭环。

## 生命周期模型

### 状态定义

- `active`：可正常收信、可读信。
- `expired_recoverable`：已过期，不再收信，处于可恢复窗口。
- `purged`：超过恢复窗口或被管理员/用户主动清理，不可恢复。

### 状态转换

1. 创建临时邮箱：`active`
2. 到达 `expires_at`：`active -> expired_recoverable`
3. 用户/管理员在恢复窗口内恢复：`expired_recoverable -> active`
4. 超过恢复窗口清理：`expired_recoverable -> purged`
5. 用户主动删除：直接 `-> purged`

## 时间规则

- 默认有效期：`24` 小时（创建或恢复/续期后重新计算）
- 默认恢复窗口：`10` 天（从过期时刻起算）
- 清理任务默认周期：`24` 小时执行一次（系统级可配）

## 数据结构

### temp_mailboxes 新增字段

- `status`：`active|expired_recoverable|purged`
- `expires_at`：到期时间（UTC）
- `recovery_until`：可恢复截止时间（UTC）
- `expired_at`：过期实际发生时间（UTC）
- `purged_at`：清理时间（UTC）
- `last_extended_at`：最近一次续期/恢复时间（UTC）

### 系统策略表（单例）

`temp_mailbox_policies`：

- `cleanup_enabled`：是否启用自动清理
- `ttl_hours`：有效期小时数（默认 24）
- `recoverable_days`：可恢复天数（默认 10）
- `cleanup_interval_hours`：自动清理周期（默认 24）
- `cleanup_batch_size`：单批处理数量（默认 500）
- `delete_emails_on_purge`：清理时是否删除该临时邮箱历史邮件
- `last_cleanup_at` / `last_cleanup_count`：最近执行信息

## 后端执行策略

### 懒更新 + 定时任务

1. 懒更新：在列表查询、邮箱详情、邮件读取前，对当前用户邮箱做过期状态对齐。
2. 定时任务：后台按策略执行清理流程，保证无请求时也能推进状态。

### 清理流程

1. 先将所有 `expires_at <= now` 的 `active` 邮箱置为 `expired_recoverable`。
2. 按批处理超过 `recovery_until` 的邮箱：
   - 从 mailserver 删除邮箱账户；
   - 按配置删除关联邮件；
   - 标记为 `purged`。

## API 设计

### 用户侧

- `POST /api/pool/{mailbox_id}/extend`
  - 行为：续期并恢复为 `active`（若仍在恢复窗口内）
- `POST /api/pool/{mailbox_id}/restore`
  - 行为：仅针对 `expired_recoverable`，恢复并重置过期时间

### 管理员侧

- `GET /api/pool/admin/settings`：获取系统策略
- `PATCH /api/pool/admin/settings`：修改系统策略
- `POST /api/pool/admin/cleanup/run`：立即执行一次清理（手动）

## 前端交互要求

- 临时邮箱列表展示倒计时（基于 `expires_at`）。
- 过期邮箱显示“已过期，可恢复至 yyyy-mm-dd hh:mm”。
- 管理员页面支持：
  - 启用/暂停自动清理；
  - 修改 TTL/恢复天数/执行周期/批量大小；
  - 手动立即清理。

## 安全与审计

- 管理员接口必须走管理员权限校验；
- 手动清理与策略变更写入结构化日志；
- 清理流程幂等（重复执行不破坏状态）。

## 发布与兼容

### 迁移兼容

- 为历史临时邮箱回填：
  - `status=active`
  - `expires_at=created_at + ttl_hours`
  - `recovery_until=expires_at + recoverable_days`

### 回滚策略

- 若需回滚，仅停用自动清理并保留字段；
- 不建议删除新增字段，避免历史状态丢失。


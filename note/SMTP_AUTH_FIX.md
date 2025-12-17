# TalentMail SMTP 认证与连接问题修复总结

## 1. 问题描述

用户在使用 Thunderbird 连接开发环境的邮件服务器时遇到三个主要问题：
1.  **认证失败**：无法使用数据库中的用户凭据登录。
2.  **连接超时**：主机无法连接到容器的 587 端口，提示超时。
3.  **连接断开**：连接建立后立即断开，提示 `lost connection after EHLO`。

## 2. 认证失败修复 (SMTP Auth)

### 原因分析
- 数据库存储的是 bcrypt 加密的密码。
- Postfix 默认使用 Cyrus SASL，不支持直接验证 bcrypt 哈希。
- Dovecot 虽然支持 SQL 认证，但缺少 `dovecot-pgsql` 驱动。

### 解决方案
1.  **安装驱动**：在 `config/mail/user-patches.sh` 中添加安装 `dovecot-pgsql` 的逻辑。
    - *优化*：使用阿里云镜像源解决 `apt-get update` 卡顿问题。
2.  **配置 Dovecot SQL 认证**：
    - 创建 `config/mail/dovecot-sql.conf.ext`，定义 SQL 查询语句验证 bcrypt 密码。
    - 修改 `config/mail/dovecot/10-auth.conf`，启用 `auth-sql.conf.ext`。
3.  **切换 Postfix SASL 实现**：
    - 在 `user-patches.sh` 中修改 Postfix 配置，将 `smtpd_sasl_type` 从 `cyrus` 改为 `dovecot`。
    - 配置 `smtpd_sasl_path` 指向 Dovecot 的认证 socket。

## 3. 连接超时修复 (Connection Timeout)

### 原因分析
- 在调试认证失败的过程中，可能进行了多次错误的登录尝试。
- `docker-mailserver` 内置的 `Fail2Ban` 服务检测到这些失败尝试，将 Docker 网关 IP (`172.18.0.1`) 判定为恶意攻击源并进行了封禁。
- 这导致从主机（经过 Docker 网关转发）到容器的所有连接都被防火墙拦截，表现为连接超时。

### 排查步骤
1.  `nc localhost 587` 超时，但 `docker port` 显示映射正常。
2.  进入容器内部 `ping` 网关通，但 `nc` 容器 IP 依然超时。
3.  检查 Fail2Ban 状态：`docker exec talentmail-mailserver-1 fail2ban-client status postfix`。
4.  发现 IP `172.18.0.1` 在封禁列表中。

### 解决方案
1.  **手动解封**：
    ```bash
    docker exec talentmail-mailserver-1 fail2ban-client set postfix unbanip 172.18.0.1
    docker exec talentmail-mailserver-1 fail2ban-client set dovecot unbanip 172.18.0.1
    ```
2.  **配置白名单**：
    创建 `config/mail/fail2ban-jail.local` 并挂载到容器的 `/etc/fail2ban/jail.local`，添加以下内容：
    ```ini
    [DEFAULT]
    ignoreip = 127.0.0.1/8 172.16.0.0/12 192.168.0.0/16 10.0.0.0/8
    ```

## 4. 连接断开修复 (Connection Lost)

### 原因分析
- Thunderbird 默认尝试使用 STARTTLS 加密连接。
- 开发环境使用自签名证书，或者 TLS 握手过程存在兼容性问题。
- Postfix 在 TLS 握手失败后断开连接。

### 解决方案
1.  **放宽 TLS 限制**：
    在 `config/mail/user-patches.sh` 中添加：
    ```bash
    # 允许非加密连接
    postconf -e "smtpd_tls_auth_only=no"
    postconf -e "smtpd_tls_security_level=may"
    # 强制 submission 端口 (587) 不使用 TLS (针对开发环境)
    postconf -P "submission/inet/smtpd_tls_security_level=none"
    ```
2.  **客户端设置**：
    Thunderbird 设置如下：
    - **连接安全性**: 无 (None)
    - **验证方式**: 平文密码 (Normal password)
    - **端口**: 587

## 5. 验证结果

- **内部测试**：使用 `swaks` 在容器内部测试认证，成功通过。
- **外部连接**：Thunderbird 成功连接并发送邮件。

## 6. 常用维护命令

- **查看 Fail2Ban 状态**：
  ```bash
  docker exec talentmail-mailserver-1 fail2ban-client status postfix
  docker exec talentmail-mailserver-1 fail2ban-client status dovecot
  ```
- **解封 IP**：
  ```bash
  docker exec talentmail-mailserver-1 fail2ban-client set postfix unbanip <IP_ADDRESS>
  ```
- **查看邮件日志**：
  ```bash
  docker logs -f talentmail-mailserver-1
  ```

---

## 附录：架构说明

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Thunderbird   │────▶│    Postfix      │────▶│    Dovecot      │
│  (邮件客户端)    │     │  (SMTP 服务器)   │     │  (SASL 认证)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   PostgreSQL    │
                                                │  (用户数据库)    │
                                                └─────────────────┘
```

### 相关文件

- `config/mail/user-patches.sh` - 启动时安装 dovecot-pgsql 并配置 Postfix
- `config/mail/dovecot-sql.conf.ext` - Dovecot SQL 连接配置
- `config/mail/dovecot/10-auth.conf` - Dovecot 认证配置
- `config/mail/fail2ban-jail.local` - Fail2Ban 白名单配置
- `docker-compose.dev.yml` - Docker Compose 配置
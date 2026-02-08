# 修复页面间歇性无法访问问题

## 问题诊断结果

经过系统诊断，发现以下问题导致页面间歇性无法访问：

### 1. 缺少服务健康检查
- **问题**: Backend 和 Frontend 服务没有配置健康检查
- **影响**: 容器启动后可能未完全就绪就开始接收流量
- **后果**: 导致 502/503 错误

### 2. 缺少自动重启策略
- **问题**: Backend 和 Frontend 服务没有配置 `restart` 策略
- **影响**: 服务异常退出后不会自动重启
- **后果**: 需要手动重启容器

### 3. Caddy 缺少超时和重试机制
- **问题**: 反向代理没有配置超时和失败重试
- **影响**: 后端服务短暂不可用时直接返回错误
- **后果**: 用户体验差

### 4. 服务依赖关系不完整
- **问题**: Caddy 只检查服务是否启动，未检查是否就绪
- **影响**: Caddy 可能在后端服务未就绪时就开始转发请求
- **后果**: 502 Bad Gateway 错误

## 解决方案

### 步骤 1: 添加健康检查端点

已创建 `backend/api/health.py`，需要在 `backend/main.py` 中注册：

```python
# 在 main.py 的导入部分添加
from api import health

# 在路由注册部分添加（第 135 行之后）
app.include_router(health.router, prefix="/api", tags=["Health"])
```

### 步骤 2: 更新 Docker Compose 配置

使用优化后的配置文件：

```bash
# 备份当前配置
cp docker-compose.dev.yml docker-compose.dev.yml.backup

# 使用优化配置
cp docker-compose.dev.yml.optimized docker-compose.dev.yml
```

**关键改进**:
- ✅ 添加 Backend 健康检查（检查 `/api/health` 端点）
- ✅ 添加 Frontend 健康检查（检查服务响应）
- ✅ 添加 Caddy 健康检查（检查管理接口）
- ✅ 所有服务添加 `restart: unless-stopped` 策略
- ✅ Caddy 依赖改为等待 Backend/Frontend 健康检查通过

### 步骤 3: 更新 Caddy 配置

使用优化后的 Caddy 配置：

```bash
# 备份当前配置
cp config/caddy/Caddyfile config/caddy/Caddyfile.backup

# 使用优化配置
cp config/caddy/Caddyfile.optimized config/caddy/Caddyfile
```

**关键改进**:
- ✅ 添加后端健康检查探测
- ✅ 配置连接超时（10秒）
- ✅ 配置读写超时（60秒）
- ✅ 添加失败重试机制（30秒内重试，间隔2秒）
- ✅ 自定义错误响应页面

### 步骤 4: 安装必要的工具

Backend 容器需要 curl 用于健康检查：

```bash
# 在 backend/Dockerfile 中添加
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

Frontend 容器需要 wget 用于健康检查：

```bash
# 在 frontend/Dockerfile 中添加
RUN apk add --no-cache wget
```

### 步骤 5: 重启服务

```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 重新构建并启动
docker-compose -f docker-compose.dev.yml up --build -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看健康检查状态
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 验证修复

### 1. 检查健康检查状态

```bash
# 所有服务应该显示 "healthy" 状态
docker ps --format "table {{.Names}}\t{{.Status}}"
```

预期输出：
```
NAMES                     STATUS
talentmail-backend-1      Up X minutes (healthy)
talentmail-frontend-1     Up X minutes (healthy)
talentmail-caddy-1        Up X minutes (healthy)
talentmail-db-1           Up X minutes (healthy)
talentmail-mailserver-1   Up X minutes
```

### 2. 测试健康检查端点

```bash
# 测试 Backend 健康检查
curl http://localhost:8000/api/health

# 预期输出
{"status":"healthy","service":"talentmail-backend","database":"connected"}

# 测试 Frontend
curl http://localhost:3000

# 应该返回 HTML 内容
```

### 3. 测试自动重启

```bash
# 模拟 Backend 崩溃
docker kill talentmail-backend-1

# 等待几秒，检查是否自动重启
docker ps | grep backend

# 应该看到容器自动重启
```

### 4. 监控日志

```bash
# 实时查看所有服务日志
docker-compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker logs -f talentmail-backend-1
docker logs -f talentmail-caddy-1
```

## 性能优化建议

### 1. 调整健康检查间隔

如果服务稳定，可以增加检查间隔以减少开销：

```yaml
healthcheck:
  interval: 60s  # 从 30s 增加到 60s
  timeout: 10s
  retries: 3
```

### 2. 监控资源使用

```bash
# 实时监控容器资源
docker stats

# 如果某个服务 CPU 或内存使用过高，考虑：
# - 增加容器资源限制
# - 优化应用代码
# - 使用缓存减少数据库查询
```

### 3. 配置日志轮转

防止日志文件过大：

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 常见问题

### Q: 健康检查一直失败怎么办？

A: 检查以下几点：
1. 服务是否真的启动成功（查看日志）
2. 健康检查端点是否正确
3. 容器内是否安装了 curl/wget
4. 网络连接是否正常

### Q: 服务频繁重启怎么办？

A: 可能原因：
1. 内存不足（增加容器内存限制）
2. 数据库连接失败（检查数据库配置）
3. 代码错误（查看应用日志）

### Q: Caddy 返回 502 错误？

A: 检查：
1. Backend/Frontend 是否健康
2. 网络连接是否正常
3. Caddy 配置是否正确
4. 查看 Caddy 日志获取详细错误

## 监控和告警

建议设置以下监控：

1. **容器健康状态监控**
   - 使用 Docker 健康检查 API
   - 设置告警通知

2. **服务可用性监控**
   - 使用外部监控服务（如 UptimeRobot）
   - 定期检查关键端点

3. **资源使用监控**
   - CPU、内存、磁盘使用率
   - 设置阈值告警

4. **日志监控**
   - 收集错误日志
   - 分析异常模式

## 总结

通过以上优化，系统将具备：

✅ **自动故障恢复**: 服务异常时自动重启  
✅ **健康检查**: 确保服务就绪后才接收流量  
✅ **失败重试**: 短暂故障时自动重试  
✅ **优雅降级**: 提供友好的错误提示  
✅ **可观测性**: 完善的日志和监控  

这些改进将显著提高系统的稳定性和可用性，减少间歇性访问问题。
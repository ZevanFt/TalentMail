# 修复 apt-get 下载慢导致构建卡住的问题

## 当前状态

✅ **已完成**：
- 删除了 docker-compose.dev.yml 中的 sync 服务
- 在 backend/main.py 的 startup 事件中集成了 `sync_users_to_mailserver()` 调用
- 创建了 backend/core/mailserver_sync.py 同步模块

❌ **当前问题**：
- backend 的 Dockerfile 中 `apt-get update && apt-get install -y postgresql-client` 卡住

---

## 问题描述

在 `backend/Dockerfile` 中，第 8 行的命令：
```dockerfile
RUN apt-get update && apt-get install -y postgresql-client
```
由于网络问题导致下载非常慢，使得整个构建过程卡住。

这个 `postgresql-client` 是为了给 `wait-for-postgres.sh` 脚本提供 `psql` 命令。

---

## 解决方案

**使用 docker-compose 的 healthcheck 功能** 来确保 PostgreSQL 就绪后再启动 backend，完全不需要在 Dockerfile 中安装任何额外的包。

---

## 需要修改的文件

### 1. 修改文件：`backend/Dockerfile`

**修改前：**
```dockerfile
# 使用官方 Python 镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装 postgresql-client，它包含了 psql 等工具
RUN apt-get update && apt-get install -y postgresql-client

# 复制等待脚本并赋予执行权限
COPY ./wait-for-postgres.sh /usr/local/bin/wait-for-postgres.sh
RUN chmod +x /usr/local/bin/wait-for-postgres.sh

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有后端代码到工作目录
COPY . .
```

**修改后（删除 apt-get 和 wait-for-postgres.sh 相关行）：**
```dockerfile
# 使用官方 Python 镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有后端代码到工作目录
COPY . .
```

---

### 2. 修改文件：`docker-compose.dev.yml`

需要修改两个地方：

#### 2.1 给 db 服务添加 healthcheck（约第 59-74 行）

**修改前：**
```yaml
  # --- 数据库服务 (PostgreSQL) ---
  db:
    image: postgres:15
    env_file:
      - .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

**修改后：**
```yaml
  # --- 数据库服务 (PostgreSQL) ---
  db:
    image: postgres:15
    env_file:
      - .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    # 健康检查：使用 PostgreSQL 自带的 pg_isready 命令
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
```

#### 2.2 修改 backend 服务的 depends_on 和 command（约第 29-40 行）

**修改前：**
```yaml
    depends_on:
      db:
        condition: service_started
      mailserver:
        condition: service_started
    command: >
      sh -c "wait-for-postgres.sh db -- uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

**修改后：**
```yaml
    depends_on:
      db:
        condition: service_healthy  # 改为 service_healthy，等待健康检查通过
      mailserver:
        condition: service_started
    # 直接启动 uvicorn，不需要 wait-for-postgres.sh
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 3. 可选：删除旧文件

可以删除不再需要的 `backend/wait-for-postgres.sh` 文件。

---

## 执行步骤

1. **停止当前卡住的构建**：按 `Ctrl+C`

2. **修改 `backend/Dockerfile`**：删除 apt-get 和 wait-for-postgres.sh 相关行

3. **修改 `docker-compose.dev.yml`**：
   - 给 db 服务添加 healthcheck
   - 修改 backend 的 depends_on 为 `service_healthy`
   - 简化 backend 的 command

4. **重新构建并启动**：
   ```bash
   docker compose -f docker-compose.dev.yml down
   docker compose -f docker-compose.dev.yml up --build
   ```

---

## 原理说明

- `pg_isready` 是 PostgreSQL 官方镜像自带的命令，用于检查数据库是否准备好接受连接
- `healthcheck` 会定期执行检查命令
- `condition: service_healthy` 会让 docker-compose 等待健康检查通过后才启动依赖的服务
- 这样就不需要在 backend 镜像中安装 postgresql-client 了

---

## 优点

1. **彻底解决网络慢的问题** - 不再需要 apt-get 下载任何包
2. **构建更快** - 减少了一个 RUN 层
3. **镜像更小** - 不包含 postgresql-client 包
4. **更可靠** - 使用 PostgreSQL 官方镜像自带的 `pg_isready` 命令
5. **更简洁** - 不需要额外的等待脚本
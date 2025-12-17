# TalentMail - 自托管邮件服务

这是一个使用 Nuxt.js (前端), Python FastAPI (后端), 和 PostgreSQL (数据库) 构建的、通过 Docker 容器化的自托管邮件服务项目。

---

## 推荐：基于 Docker 的本地开发环境

这是推荐的开发方式。它使用 Docker 将所有服务（前端、后端、数据库、Caddy 网关等）在隔离的容器中运行，保持您主机的清洁，并确保开发环境与生产环境高度一致。

### 第 1 步：配置本地 DNS (Hosts 文件)

**这是实现本地域名访问的关键一步，只需配置一次。**

为了让您的电脑能将 `mail.talenting.test` 这个测试域名指向本地运行的 Caddy 网关，您需要修改本机的 `hosts` 文件。

1.  找到并以**管理员权限**打开 `hosts` 文件：
    *   **Linux / macOS**: 文件位于 `/etc/hosts`。您可以在终端使用 `sudo nano /etc/hosts` 来编辑。
    *   **Windows**: 文件位于 `C:\Windows\System32\drivers\etc\hosts`。您需要以管理员身份运行记事本或其他文本编辑器来打开它。

2.  在文件末尾**另起一行**，添加以下内容并保存：
    ```
    127.0.0.1   mail.talenting.test
    ```

### 第 2 步：启动开发环境

在项目的根目录下，打开一个终端，运行以下命令：

```bash
# 构建镜像并在后台启动所有服务
docker compose -f docker-compose.dev.yml up -d --build
```
*   `up`: 创建并启动容器。
*   `-d`: 在后台（detached）模式下运行。
*   `--build`: 如果代码或 Dockerfile 有变动，则重新构建镜像。

此命令会启动 `frontend`, `backend`, `db`, `mailpit`, 和 `caddy` 共五个服务。

### 第 3 步：初始化数据库（仅首次需要）

如果您是第一次搭建项目，或者清除了数据库卷，需要执行以下命令来创建数据库表和初始数据：

```bash
# 连接到正在运行的后端容器，并执行初始化脚本
docker compose -f docker-compose.dev.yml exec backend python -m initial.initial_data
```

### 第 4 步：访问应用

所有服务启动成功后，打开您的浏览器，访问以下地址：

*   **主应用 (通过 Caddy)**: **https://mail.talenting.test** (浏览器可能会提示证书不受信任，请选择“继续前往”)
*   **Mailpit 邮件查看**: `http://localhost:8025`
*   **直接访问前端 (备用)**: `http://localhost:3000`
*   **直接访问后端 API (备用)**: `http://localhost:8000`

### 第 5 步：停止环境

当您完成工作后，使用此命令来停止并移除所有正在运行的容器：

```bash
# 停止并移除所有服务
docker compose -f docker-compose.dev.yml down
```
*您的 PostgreSQL 数据库数据会保存在 Docker 卷中，不会丢失。*

---

## 附录：常用开发命令

*   **查看正在运行的容器**:
    ```bash
    docker ps
    ```

*   **更新后端依赖**:
    如果您在后端代码中添加了新的 Python 包，可以使用 `pipreqs` 自动更新 `requirements.txt`。
    1.  在 Docker 中安装 `pipreqs` (只需一次):
        ```bash
        docker compose -f docker-compose.dev.yml exec backend pip install pipreqs
        ```
    2.  扫描代码并生成新的 `requirements.txt`:
        ```bash
        docker compose -f docker-compose.dev.yml exec backend pipreqs /app --force

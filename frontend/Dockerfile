# =============================================================================
# TalentMail Frontend 开发环境 Dockerfile
# =============================================================================
# 用于 docker-compose.dev.yml 开发环境
# =============================================================================

# 使用官方 Node.js 镜像
FROM node:20

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制所有前端代码
# 注意：开发环境下通过 volumes 挂载覆盖，这里只是确保镜像构建成功
COPY . .

# 暴露开发服务器端口
EXPOSE 3000

# 默认启动命令（会被 docker-compose.dev.yml 的 command 覆盖）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

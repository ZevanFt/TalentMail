#!/bin/bash

# 部署脚本

echo "🚀 开始部署 TalentMail..."

# 1. 停止现有服务
echo "🛑 停止现有服务..."
docker compose down

# 2. 构建镜像
echo "🏗️ 构建 Docker 镜像..."
docker compose build

# 3. 启动服务
echo "▶️ 启动服务..."
docker compose up -d

# 4. 等待数据库启动
echo "⏳ 等待数据库就绪..."
sleep 10

# 5. 运行数据库迁移
echo "🔄 运行数据库迁移..."
docker compose exec backend alembic upgrade head

echo "✅ 部署完成！"
echo "请确保您的域名 DNS 已指向此服务器，并且防火墙已开放 80, 443, 25, 143, 587, 993 端口。"
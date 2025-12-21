#!/bin/bash

# 部署脚本

echo "🚀 开始部署 TalentMail..."

# 1. 停止现有服务
echo "🛑 停止现有服务..."
docker compose down

# 2. 根据 config.json 生成生产环境配置
echo "⚙️  根据 config.json 生成域名配置文件 (.env.domains)..."
python3 scripts/generate_domains.py
if [ $? -ne 0 ]; then
    echo "🛑 错误：生成 .env.domains 文件失败，请检查错误信息。"
    exit 1
fi
echo ""

# 3. 构建镜像
echo "🏗️  构建 Docker 镜像..."
# 在构建前检查必需的 .env 变量，避免容器内进程（如 alembic/pydantic）因缺失配置而崩溃
REQUIRED_VARS=(
	DATABASE_URL_DOCKER
	REFRESH_TOKEN_EXPIRE_DAYS
	JWT_ALGORITHM
	ADMIN_EMAIL
	ADMIN_PASSWORD
	SECRET_KEY
	POSTGRES_PASSWORD
	POSTGRES_USER
	POSTGRES_DB
	DOMAIN
)

missing=()
if [ ! -f .env ]; then
	echo "❌ 未找到 .env 文件，请在项目根创建并填写必需环境变量（参见 README_DEPLOY.md）"
	exit 1
fi

for v in "${REQUIRED_VARS[@]}"; do
	if ! grep -qE "^${v}=" .env; then
		missing+=("$v")
	fi
done

if [ ${#missing[@]} -ne 0 ]; then
	echo "❌ 以下必需的环境变量在 .env 中缺失： ${missing[*]}"
	echo "请编辑 .env 并填入这些键后重试。示例见 README_DEPLOY.md 或运行 'cp .env.example .env' 并修改值。"
	exit 1
fi

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
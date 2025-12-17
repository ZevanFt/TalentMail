#!/bin/bash

# --- 配置 ---
# --- 动态配置 ---
# 从 config.json 动态读取配置，避免硬编码
CONFIG_FILE="config.json"
BASE_DOMAIN=$(jq -r '.environments.development.baseDomain' "$CONFIG_FILE")
WEB_PREFIX=$(jq -r '.environments.development.webPrefix' "$CONFIG_FILE")
BASE_URL="https://${WEB_PREFIX}.${BASE_DOMAIN}"

# 每次运行时使用一个唯一的邮箱，以避免“邮箱已注册”的错误
# 我们使用 `date +%s` 来获取当前的 Unix 时间戳
# 每次运行时使用唯一的发送者和接收者，以避免任何状态冲突
UNIQUE_ID_SENDER=$(date +%s)
UNIQUE_ID_RECIPIENT=$(($(date +%s)+1)) # 加1秒确保唯一
SENDER_EMAIL="sender_${UNIQUE_ID_SENDER}@${BASE_DOMAIN}"
RECIPIENT_EMAIL="recipient_${UNIQUE_ID_RECIPIENT}@${BASE_DOMAIN}"
TEST_PASSWORD="a_very_secure_password"

# --- 颜色代码 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- 开始端到端邮件收发闭环测试 ---${NC}"

# --- 准备工作: 在 Mailserver 中创建邮箱 ---
echo -e "\n${YELLOW}[PREP] 正在 Mailserver 中创建测试邮箱...${NC}"
docker compose -f docker-compose.dev.yml exec mailserver setup email add "${SENDER_EMAIL}" "${TEST_PASSWORD}" > /dev/null
docker compose -f docker-compose.dev.yml exec mailserver setup email add "${RECIPIENT_EMAIL}" "${TEST_PASSWORD}" > /dev/null
echo -e "${GREEN}✔ 发送者邮箱 (${SENDER_EMAIL}) 和接收者邮箱 (${RECIPIENT_EMAIL}) 已创建!${NC}"

# --- 清理函数 ---
# 使用 trap 命令确保脚本退出时（无论成功还是失败）都会执行清理操作
cleanup() {
  echo -e "\n${YELLOW}[CLEANUP] 正在从 Mailserver 中删除测试邮箱...${NC}"
  docker compose -f docker-compose.dev.yml exec mailserver setup email del "${SENDER_EMAIL}" > /dev/null
  docker compose -f docker-compose.dev.yml exec mailserver setup email del "${RECIPIENT_EMAIL}" > /dev/null
  echo -e "${GREEN}✔ 测试邮箱已清理!${NC}"
}
trap cleanup EXIT

# --- 步骤 1: 注册新用户 (发送者) ---
echo -e "\n${YELLOW}[1/3] 正在后端注册发送者用户: ${SENDER_EMAIL}...${NC}"
REGISTER_RESPONSE=$(curl -s -L -k -X POST "${BASE_URL}/api/auth/register" \
-H "Content-Type: application/json" \
-d "{\"email\": \"${SENDER_EMAIL}\", \"password\": \"${TEST_PASSWORD}\", \"redemption_code\": \"testcode\"}")

# 检查注册是否成功 (现在我们检查 status:success)
if echo "${REGISTER_RESPONSE}" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✔ 注册成功!${NC}"
    echo "  响应: ${REGISTER_RESPONSE}"
else
    echo -e "${RED}✖ 注册失败!${NC}"
    echo "  响应: ${REGISTER_RESPONSE}"
    exit 1
fi

# --- 步骤 2: 登录并提取 Token ---
echo -e "\n${YELLOW}[2/3] 正在使用新用户凭据登录...${NC}"
LOGIN_RESPONSE=$(curl -s -L -k -X POST "${BASE_URL}/api/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=${SENDER_EMAIL}&password=${TEST_PASSWORD}")

# 使用 jq 工具来安全、可靠地提取 access_token
ACCESS_TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.access_token')

if [ "${ACCESS_TOKEN}" != "null" ] && [ -n "${ACCESS_TOKEN}" ]; then
    echo -e "${GREEN}✔ 登录成功!${NC}"
    # 为了安全，只显示部分 token
    echo "  Access Token (部分): $(echo ${ACCESS_TOKEN} | cut -c 1-20)..."
else
    echo -e "${RED}✖ 登录失败!${NC}"
    echo "  响应: ${LOGIN_RESPONSE}"
    exit 1
fi

# --- 步骤 2: 发送邮件 ---
echo -e "\n${YELLOW}[3/3] 正在使用 Access Token 发送邮件至 ${RECIPIENT_EMAIL}...${NC}"
SEND_MAIL_RESPONSE=$(curl -s -L -k -X POST "${BASE_URL}/api/mail/send" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
-d @- << EOF
{
  "to": [
    {
      "name": "Test User",
      "email": "${RECIPIENT_EMAIL}"
    }
  ],
  "subject": "来自测试脚本的问候!",
  "body_html": "<h1>你好!</h1><p>这是一封通过自动化测试脚本发送的邮件。</p>"
}
EOF
)

if echo "${SEND_MAIL_RESPONSE}" | jq -e 'has("id") and has("sender")' > /dev/null; then
    echo -e "${GREEN}✔ 邮件发送请求成功!${NC}"
    echo "  响应: ${SEND_MAIL_RESPONSE}"
else
    echo -e "${RED}✖ 邮件发送请求失败!${NC}"
    echo "  响应: ${SEND_MAIL_RESPONSE}"
    exit 1
fi

echo -e "\n${GREEN}--- 所有测试已成功完成! ---${NC}"
echo "请检查邮件客户端 (如 Thunderbird)，确认收件人 ${RECIPIENT_EMAIL} 是否已成功收到邮件。"
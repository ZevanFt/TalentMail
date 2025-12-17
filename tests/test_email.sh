#!/bin/bash

# 登录信息
ADMIN_USER="admin@talenting.test"
ADMIN_PASSWORD="adminpassword"
API_BASE_URL="http://localhost/talent"

# 1. 登录并获取 Token
echo "Logging in as $ADMIN_USER..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$ADMIN_USER&password=$ADMIN_PASSWORD")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r .access_token)

if [ "$ACCESS_TOKEN" == "null" ]; then
    echo "Login failed. Response:"
    echo $LOGIN_RESPONSE
    exit 1
fi

echo "Login successful. Token received."

# 2. 发送测试邮件
echo "Sending test email..."
SEND_EMAIL_RESPONSE=$(curl -s -X POST "$API_BASE_URL/send-test-email" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
        "to_email": "test@example.com",
        "subject": "Test Email from TalentMail",
        "message": "This is a test email sent from the TalentMail API."
    }')

echo "Email send response:"
echo $SEND_EMAIL_RESPONSE

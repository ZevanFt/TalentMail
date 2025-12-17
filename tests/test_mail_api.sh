#!/bin/bash

# --- Configuration ---
# Load environment variables from .env file at the project root
set -a # automatically export all variables
source .env
set +a

# API endpoint
API_BASE_URL="https://mail.talenting.test"
LOGIN_URL="${API_BASE_URL}/api/auth/login"
SEND_MAIL_URL="${API_BASE_URL}/api/mail/send"
RESET_PASSWORD_URL="${API_BASE_URL}/api/users/reset-password-dev"

# --- Helper Functions ---
log() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# --- Dynamic Credentials ---
# Dynamically get the baseDomain from config.json to construct the admin email
log "Reading baseDomain from config.json..."
CURRENT_ENV=$(jq -r '.currentEnvironment' config.json)
BASE_DOMAIN=$(jq -r ".environments.${CURRENT_ENV}.baseDomain" config.json)

if [ -z "${BASE_DOMAIN}" ] || [ "${BASE_DOMAIN}" == "null" ]; then
    error "Could not read baseDomain from config.json for environment ${CURRENT_ENV}."
fi

ADMIN_EMAIL="admin@${BASE_DOMAIN}"
ADMIN_PASSWORD="${ADMIN_PASSWORD}" # This one correctly comes from .env
log "Admin email dynamically set to: ${ADMIN_EMAIL}"

# --- Main Script ---

# 1. Reset admin password to ensure consistency (for development)
log "Resetting password for ${ADMIN_EMAIL} to ensure test consistency..."
reset_payload=$(jq -n \
    --arg email "$ADMIN_EMAIL" \
    --arg password "$ADMIN_PASSWORD" \
    '{email: $email, new_password: $password}')

reset_response=$(curl -s -k -X POST -H "Content-Type: application/json" \
    -d "${reset_payload}" \
    "${RESET_PASSWORD_URL}")

reset_msg=$(echo "${reset_response}" | jq -r .msg)

if [ -z "${reset_msg}" ] || [ "${reset_msg}" == "null" ]; then
    error "Failed to reset password. Response: ${reset_response}"
fi
log "Password for ${ADMIN_EMAIL} has been successfully reset."


# 2. Authenticate and get JWT token
log "Attempting to login as ${ADMIN_EMAIL}..."
login_response=$(curl -s -k -X POST -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${ADMIN_EMAIL}&password=${ADMIN_PASSWORD}" \
    "${LOGIN_URL}")

access_token=$(echo "${login_response}" | jq -r .access_token)

if [ -z "${access_token}" ] || [ "${access_token}" == "null" ]; then
    error "Failed to get access token. Response: ${login_response}"
fi
log "Successfully logged in. Token received."

# 3. Prepare the email payload
# We will send an email from the admin to a test user.
# In a real scenario, you might want to create another user for testing.
# We will send an email from the admin to themselves to test the full loop.
recipient_email="testuser_1764489698@talenting.test"
recipient_name="Test User"

log "Preparing to send email to ${recipient_email}..."

# Using jq to safely construct the JSON payload
json_payload=$(jq -n \
    --arg to_email "$recipient_email" \
    --arg to_name "$recipient_name" \
    --arg subject "Hello from TalentMail API!" \
    --arg body_html "<h1>Test Email</h1><p>This is a test email sent from the <strong>TalentMail API</strong> using a test script.</p>" \
    '{
        "to": [{ "name": $to_name, "email": $to_email }],
        "cc": [],
        "bcc": [],
        "subject": $subject,
        "body_html": $body_html
    }')

# 4. Send the email
log "Sending email via API..."
send_response=$(curl -s -k -X POST "${SEND_MAIL_URL}" \
    -H "Authorization: Bearer ${access_token}" \
    -H "Content-Type: application/json" \
    -d "${json_payload}")

# 5. Display the result
log "API Response:"
echo "${send_response}" | jq .

# Check if the response contains an ID, indicating success at the API level
email_id=$(echo "${send_response}" | jq -r .id)
if [ -z "${email_id}" ] || [ "${email_id}" == "null" ]; then
    error "Failed to send email. The API did not return a valid email record."
fi

log "Email sending task was successfully submitted to the backend. DB record ID: ${email_id}"
log "Check the backend logs and your email client (Thunderbird) to verify the actual sending."
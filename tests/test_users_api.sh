#!/bin/bash

# This script tests the /api/users/me endpoint.
# It requires jq to be installed.

# --- Configuration ---
BASE_URL="http://localhost:8000"
ADMIN_USER="admin@talenting.test"
ADMIN_PASSWORD="adminpassword"

# --- Helper Functions ---
info() {
    echo "[INFO] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# --- Main Logic ---
info "Attempting to log in as '$ADMIN_USER'..."
response=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$ADMIN_USER&password=$ADMIN_PASSWORD")

access_token=$(echo "$response" | jq -r .access_token)

if [ -z "$access_token" ] || [ "$access_token" == "null" ]; then
    error "Failed to get access token. Response: $response"
fi

info "Successfully obtained access token."

info "Calling /api/users/me endpoint..."
user_info=$(curl -s -X GET "$BASE_URL/api/users/me" \
    -H "Authorization: Bearer $access_token")

info "Response from /api/users/me:"
echo "$user_info" | jq .

# --- Verification ---
user_email=$(echo "$user_info" | jq -r .email)
if [ "$user_email" == "$ADMIN_USER" ]; then
    info "SUCCESS: Endpoint returned the correct user email."
    exit 0
else
    error "FAILURE: Endpoint returned an unexpected email: '$user_email'"
fi
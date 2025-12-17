#!/bin/bash
set -e

# Define the target configuration file
CONFIG_FILE="data/mailserver/config/postfix-accounts.cf"

# Create the directory if it doesn't exist
mkdir -p "$(dirname "$CONFIG_FILE")"

# Write the user accounts to the file
cat > "$CONFIG_FILE" << EOL
# This file is used by docker-mailserver to create email accounts.
# Format: email@domain.com|{PLAIN}password
admin@talenting.test|{PLAIN}adminpassword
testuser_1764489698@talenting.test|{PLAIN}testpassword
EOL

echo "Successfully created mail server accounts in $CONFIG_FILE"
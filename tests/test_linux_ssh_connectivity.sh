#!/bin/bash
set -e
HOST=$1
USERNAME=$2
KEY="id_rsa"

# Default to ec2-user if no username provided
if [ -z "$USERNAME" ]; then
  USERNAME="ec2-user"
fi

if [ -z "$HOST" ]; then
  echo "Usage: $0 <host> [username]"
  echo "Default username: ec2-user"
  exit 1
fi

echo "Testing SSH connectivity to $HOST with username: $USERNAME"
chmod 600 $KEY
ssh -o StrictHostKeyChecking=no -i $KEY $USERNAME@$HOST "echo LINUX SSH CONNECTIVITY OK" 
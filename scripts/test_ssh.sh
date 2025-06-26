#!/bin/bash
set -e
HOST=$1
KEY="id_rsa"
USER="ubuntu"

if [ -z "$HOST" ]; then
  echo "Usage: $0 <host>"
  exit 1
fi

chmod 600 $KEY
ssh -o StrictHostKeyChecking=no -i $KEY $USER@$HOST "echo SSH OK" 
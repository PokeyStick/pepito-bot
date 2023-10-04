#!/bin/sh

if [ -f /etc/secret-volume/.env ]; then
  echo "Loading secrets from volume..."
  source /etc/secret-volume/.env
  echo "Done!"
else
  echo "Secrets file not found"
fi
echo "Launching main app..."
exec /usr/local/bin/python3 /app/pepitobot.py

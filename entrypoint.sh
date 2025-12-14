#!/bin/bash
echo "Check Redis IP..."
REDIS_IP=$(python -c "import socket; print(socket.gethostbyname('redis'))" 2>/dev/null)

if [ -n "$REDIS_IP" ]; then
    echo "Redis resolved to: $REDIS_IP"
    export REDIS_URL="redis://$REDIS_IP:6379/0"
else
    echo "Could not resolve Redis hostname."
fi

exec "$@"

#!/bin/bash

set -e

echo "Stopping compose stack..."

docker compose down

echo "Stopping Redis..."

docker stop local_redis || true

echo "Stopping Postgres..."

docker stop local_db || true

echo ""
echo "Cleanup complete."

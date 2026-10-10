#!/bin/bash

set -e

echo "Stopping compose stack..."

docker compose down

echo "Stopping Redis..."

docker stop hang-redis-local || true

echo "Stopping Postgres..."

docker stop hang-db-local || true

echo ""
echo "Cleanup complete."

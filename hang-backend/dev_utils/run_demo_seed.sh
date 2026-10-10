#!/usr/bin/env bash
set -euo pipefail

: "${NETWORK:?Set NETWORK}"
: "${DB_HOST:?Set DB_HOST}"
: "${REDIS_HOST:?Set REDIS_HOST}"

docker build -f Dockerfile.loadtest -t app-loadtest .

docker run --rm \
  --network "$NETWORK" \
  --env-file .api_env \
  -e DB_HOST="$DB_HOST" \
  -e REDIS_HOST="$REDIS_HOST" \
  -v "$(pwd)/dev_utils:/app/dev_utils" \
  app-loadtest \
  poetry run python -m dev_utils.demo_seed "$@"
#!/usr/bin/env bash
set -euo pipefail

: "${NETWORK:?Set NETWORK}"
: "${DB_HOST:?Set DB_HOST}"
: "${REDIS_HOST:?Set REDIS_HOST}"

docker build -f Dockerfile.loadtest -t app-loadtest .

docker run --rm -it \
  --network "$NETWORK" \
  --env-file .api_env \
  -e DB_HOST="$DB_HOST" \
  -e REDIS_HOST="$REDIS_HOST" \
  -v "$(pwd)/dev_utils:/app/dev_utils" \
  app-loadtest \
  sh -c '
    poetry run python -m dev_utils.load_test_seed --pairs 1000 &&
    poetry run python dev_utils/load_test_client.py \
      --url ws://hang-nginx:80/api/ws/conversations \
      --sweep "50,100,250,500,1000" \
      --messages-per-user 50 \
      --message-interval 0 \
      --drain-seconds 30
  '
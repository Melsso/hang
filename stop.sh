#!/usr/bin/env bash

# Usage: ./stop.sh            deletes the cluster, stops Postgres/Redis (data is kept)
#        ./stop.sh --purge    also removes those containers and their data

set -euo pipefail
. "$(dirname "$0")/scripts/lib.sh"

PURGE=0
if [ "${1:-}" = "--purge" ]; then PURGE=1; fi

need docker kind

log "Deleting kind cluster '$CLUSTER_NAME'"
kind delete cluster --name "$CLUSTER_NAME" >/dev/null 2>&1 || true

CONTAINERS="hang-db hang-db-prod"
for e in $ENVS; do CONTAINERS="$CONTAINERS $(env_redis_host "$e")"; done

for c in $CONTAINERS; do
  if [ "$PURGE" -eq 1 ]; then
    echo "Removing $c..."
    docker rm -fv "$c" >/dev/null 2>&1 || true
  else
    echo "Stopping $c..."
    docker stop "$c" >/dev/null 2>&1 || true
  fi
done

log "Done."
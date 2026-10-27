#!/usr/bin/env bash

# One command from a clean checkout to running environments.
# Usage: ./start.sh [env ...]     (default: dev; valid: dev qa prod)

set -euo pipefail
. "$(dirname "$0")/scripts/lib.sh"
cd "$ROOT"

TARGETS="${*:-dev}"
for e in $TARGETS; do
  case " $ENVS " in
    *" $e "*) ;;
    *) die "unknown environment '$e' (valid: $ENVS)" ;;
  esac
done

NETWORK_NAME="kind"
REDIS_IMAGE="redis:7-alpine"
PG_IMAGE="postgres:16"
BACKEND_IMAGE="hang-backend:local"
FRONTEND_IMAGE="hang-frontend:local"
INIT_SQL="infra/init.sql"

need docker kind kubectl mkcert openssl
docker info >/dev/null 2>&1 || die "Docker is not running."
[ -f "$INIT_SQL" ] || die "$INIT_SQL not found."
if grep -q 'DEV_DB_USER' "$INIT_SQL"; then
  die "$INIT_SQL still has the DEV_DB_USER owner lines. Regenerate it with: pg_dump --schema-only --no-owner --no-privileges"
fi

k() { kubectl --context "kind-$CLUSTER_NAME" "$@"; }

ensure_container() {
  local name=$1
  shift
  if docker ps -q -f name="^${name}$" | grep -q .; then
    echo "$name already running."
  elif docker ps -aq -f name="^${name}$" | grep -q .; then
    echo "Starting existing $name..."
    docker start "$name" >/dev/null
  else
    echo "Creating $name..."
    docker run -d --name "$name" --network "$NETWORK_NAME" "$@" >/dev/null
  fi
}

ensure_pg() {
  local name=$1 envfile=$2
  shift 2
  local user
  user=$(get_kv "$envfile" POSTGRES_USER)

  ensure_container "$name" --env-file "$envfile" "$PG_IMAGE" -c max_connections=200

  until docker exec "$name" pg_isready -h 127.0.0.1 -U "$user" >/dev/null 2>&1; do
    echo "Waiting for $name..."
    sleep 1
  done

  local db has
  for db in "$@"; do
    if ! docker exec "$name" psql -h 127.0.0.1 -U "$user" -d postgres -tAc \
      "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1; then
      docker exec "$name" psql -h 127.0.0.1 -U "$user" -d postgres -c "CREATE DATABASE \"$db\"" >/dev/null
    fi
    has=$(docker exec "$name" psql -h 127.0.0.1 -U "$user" -d "$db" -tAc \
      "SELECT to_regclass('public.users') IS NOT NULL")
    if [ "$has" != "t" ]; then
      echo "Initializing schema in $db..."
      docker exec -i "$name" psql -h 127.0.0.1 -U "$user" -d "$db" -v ON_ERROR_STOP=1 -q <"$INIT_SQL"
    fi
  done
}

log "Generating env files (skips anything that already exists)"
bash scripts/setup-env.sh

log "Starting Postgres and Redis on the '$NETWORK_NAME' network"
docker network inspect "$NETWORK_NAME" >/dev/null 2>&1 || docker network create "$NETWORK_NAME" >/dev/null

MAIN_DBS=""
PROD_DBS=""
for e in $TARGETS; do
  ensure_container "$(env_redis_host "$e")" "$REDIS_IMAGE" redis-server --appendonly yes
  if [ "$e" = "prod" ]; then
    PROD_DBS="$PROD_DBS $(env_db_name "$e")"
  else
    MAIN_DBS="$MAIN_DBS $(env_db_name "$e")"
  fi
done
if [ -n "$MAIN_DBS" ]; then
  ensure_pg hang-db "$(env_db_envfile dev)" $MAIN_DBS
fi
if [ -n "$PROD_DBS" ]; then
  ensure_pg hang-db-prod "$(env_db_envfile prod)" $PROD_DBS
fi

log "Building images"
docker build -f ./hang-backend/Dockerfile.hang -t "$BACKEND_IMAGE" ./hang-backend
docker build -t "$FRONTEND_IMAGE" ./hang-frontend

log "Creating the cluster, ingress and TLS (skips what exists)"
bash scripts/cluster-up.sh

log "Loading images into the cluster"
kind load docker-image "$BACKEND_IMAGE" --name "$CLUSTER_NAME"
kind load docker-image "$FRONTEND_IMAGE" --name "$CLUSTER_NAME"

for e in $TARGETS; do
  log "Deploying $e"
  existed=0
  k -n "$e" get deployment api >/dev/null 2>&1 && existed=1
  k apply -k "k8s/overlays/$e"
  if [ "$existed" -eq 1 ]; then
    k -n "$e" rollout restart deployment/api deployment/frontend
  fi
done

log "Deploying monitoring"
k apply -k k8s/monitoring

for e in $TARGETS; do
  k -n "$e" rollout status deployment/api --timeout=240s
  k -n "$e" rollout status deployment/frontend --timeout=120s
done

k -n monitoring rollout status deployment/prometheus --timeout=120s
k -n monitoring rollout status deployment/grafana --timeout=180s

log "Ready:"
echo "  https://grafana.$DOMAIN:$HTTPS_PORT"
for e in $TARGETS; do echo "  $(env_url "$e")"; done
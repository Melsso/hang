#!/usr/bin/env bash
# shellcheck disable=SC2034

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_DIR="$ROOT/.local"
mkdir -p "$LOCAL_DIR"

[ -f "$LOCAL_DIR/config.env" ] && . "$LOCAL_DIR/config.env"

: "${CLUSTER_NAME:=hang}"
: "${HTTPS_PORT:=8443}"
: "${SHARED_WORKERS:=2}"
DOMAIN="localtest.me"
ENVS="dev qa prod"

KIND_NODE_IMAGE="kindest/node:v1.35.0@sha256:452d707d4862f52530247495d180205e029056831160e22870e37e3f6c1ac31f"
INGRESS_MANIFEST="https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.3/deploy/static/provider/kind/deploy.yaml"
CERT_DIR="$LOCAL_DIR/certs"
KIND_CONFIG="$LOCAL_DIR/kind-config.yml"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

need() {
  local missing=0 c
  for c in "$@"; do
    if ! command -v "$c" >/dev/null 2>&1; then
      printf 'missing tool: %s' "$c" >&2
      case "$c" in
        kind|kubectl|mkcert) printf '   (macOS: brew install %s)' "$c" >&2 ;;
      esac
      printf '\n' >&2; missing=1
    fi
  done
  [ "$missing" -eq 0 ] || exit 1
}

env_db_host()    { case "$1" in prod) echo hang-db-prod ;; *) echo hang-db ;; esac; }
env_db_envfile() { case "$1" in prod) echo infra/.db.prod.env ;; *) echo infra/.db.dev.env ;; esac; }
env_db_name()    { echo "hang_$1"; }
env_redis_host() { echo "hang-redis-$1"; }
env_url()        { echo "https://$1.$DOMAIN:$HTTPS_PORT"; }

get_kv() { grep "^$2=" "$1" | head -1 | cut -d= -f2-; }

set_kv() {
  local tmp; tmp="$(mktemp)"
  KEY="$2" VAL="$3" awk '
    BEGIN { k = ENVIRON["KEY"]; v = ENVIRON["VAL"] }
    index($0, k "=") == 1 { print k "=" v; f = 1; next }
    { print }
    END { if (!f) print k "=" v }' "$1" > "$tmp"
  mv "$tmp" "$1"
}

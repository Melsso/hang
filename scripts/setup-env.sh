#!/usr/bin/env bash

# Generates every local, gitignored env file from the committed *.example templates.
# Usage: scripts/setup-env.sh [--force]
#   --force  regenerates the API env files (new SECRET_KEY). DB credentials are never
#            regenerated, because Postgres only reads them when its volume is first created.
# Non-interactive: export R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
#   R2_BUCKET_dev/qa/prod, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET beforehand.

set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"
need openssl

FORCE=0; [ "${1:-}" = "--force" ] && FORCE=1
PLACEHOLDER="not-configured"
PLACEHOLDER_ENDPOINT="https://storage-not-configured.invalid"

ask() {
  local var=$1 prompt=$2 def=${3:-} secret=${4:-} val
  val="${!var:-}"
  if [ -z "$val" ] && [ -t 0 ]; then
    if [ -n "$secret" ]; then read -r -s -p "$prompt: " val; echo
    else read -r -p "$prompt${def:+ [$def]}: " val; fi
  fi
  printf -v "$var" '%s' "${val:-$def}"
}

# shellcheck disable=SC2016
printf ': "${HTTPS_PORT:=%s}"\n' "$HTTPS_PORT" > "$LOCAL_DIR/config.env"

for f in infra/.db.dev.env infra/.db.prod.env; do
  if [ ! -f "$f" ]; then
    printf 'POSTGRES_USER=hang\nPOSTGRES_PASSWORD=%s\n' "$(openssl rand -hex 16)" > "$f"
    chmod 600 "$f"; log "created $f"
  fi
done

todo=""
for e in $ENVS; do
  d="k8s/overlays/$e"
  if [ "$FORCE" -eq 1 ] || [ ! -f "$d/api.env" ] || [ ! -f "$d/api.secret.env" ]; then todo="$todo $e"; fi
done
if [ -z "$todo" ]; then log "all env files exist (use --force to regenerate the API ones)"; exit 0; fi

echo
echo "Image storage: any S3-compatible bucket (Cloudflare R2, AWS S3, ...). Press Enter to skip;"
echo "the app still runs, but profile picture uploads will fail until you configure it."
ask R2_ENDPOINT "Storage endpoint URL" "$PLACEHOLDER_ENDPOINT"
ask R2_ACCESS_KEY_ID "Storage access key id" "$PLACEHOLDER"
ask R2_SECRET_ACCESS_KEY "Storage secret access key" "$PLACEHOLDER" secret
echo "Use a SEPARATE bucket per environment: image keys are users/<id>/..., so dev and prod would collide."
for e in $todo; do ask "R2_BUCKET_$e" "Bucket for $e" "hang-$e"; done
echo
echo "Google login (optional). Press Enter to skip; email/password login works without it."
ask GOOGLE_CLIENT_ID "Google OAuth client id" "$PLACEHOLDER"
ask GOOGLE_CLIENT_SECRET "Google OAuth client secret" "$PLACEHOLDER" secret

for e in $todo; do
  d="k8s/overlays/$e"
  dbenv="$(env_db_envfile "$e")"
  bucket_var="R2_BUCKET_$e"

  cp "$d/api.env.example" "$d/api.env"
  set_kv "$d/api.env" DB_HOST "$(env_db_host "$e")"
  set_kv "$d/api.env" DB_NAME "$(env_db_name "$e")"
  set_kv "$d/api.env" REDIS_HOST "$(env_redis_host "$e")"
  set_kv "$d/api.env" R2_ENDPOINT "$R2_ENDPOINT"
  set_kv "$d/api.env" R2_BUCKET_NAME "${!bucket_var}"
  set_kv "$d/api.env" GOOGLE_REDIRECT_URI "$(env_url "$e")/api/auth/login/google/callback"

  cp "$d/api.secret.env.example" "$d/api.secret.env"
  set_kv "$d/api.secret.env" DB_USER "$(get_kv "$dbenv" POSTGRES_USER)"
  set_kv "$d/api.secret.env" DB_PASSWORD "$(get_kv "$dbenv" POSTGRES_PASSWORD)"
  set_kv "$d/api.secret.env" SECRET_KEY "$(openssl rand -hex 32)"
  set_kv "$d/api.secret.env" R2_ACCESS_KEY_ID "$R2_ACCESS_KEY_ID"
  set_kv "$d/api.secret.env" R2_SECRET_ACCESS_KEY "$R2_SECRET_ACCESS_KEY"
  set_kv "$d/api.secret.env" GOOGLE_CLIENT_ID "$GOOGLE_CLIENT_ID"
  set_kv "$d/api.secret.env" GOOGLE_CLIENT_SECRET "$GOOGLE_CLIENT_SECRET"
  chmod 600 "$d/api.secret.env"
  log "generated k8s/overlays/$e/api.env and api.secret.env"
done

if [ "$GOOGLE_CLIENT_ID" != "$PLACEHOLDER" ]; then
  echo; echo "Register these redirect URIs on your Google OAuth client:"
  for e in $ENVS; do echo "  $(env_url "$e")/api/auth/login/google/callback"; done
fi

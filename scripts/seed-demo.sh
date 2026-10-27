#!/usr/bin/env bash

# Seeds demo accounts and profiles into one environment's database.
# Usage: scripts/seed-demo.sh [env] [demo_seed args]    (default env: dev)

set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"

E="${1:-dev}"
shift || true
case " $ENVS " in *" $E "*) ;; *) die "unknown environment '$E' (valid: $ENVS)" ;; esac
need docker
[ -f "k8s/overlays/$E/api.env" ] || die "env files for $E missing; run scripts/setup-env.sh"
[ -d hang-backend/dev_utils/resources ] || log "No dev_utils/resources found: profiles get the default avatar"

docker build -q -f hang-backend/Dockerfile.loadtest -t hang-loadtest:local hang-backend >/dev/null
docker run --rm --network kind \
  --env-file "k8s/overlays/$E/api.env" --env-file "k8s/overlays/$E/api.secret.env" \
  -v "$ROOT/hang-backend/dev_utils:/app/dev_utils" \
  hang-loadtest:local poetry run python -m dev_utils.demo_seed "$@"
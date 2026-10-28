#!/usr/bin/env bash

# Runs the WebSocket load test as a Job inside the cluster.
# Usage: scripts/loadtest.sh [env]    (default: prod; the cluster must be up via ./start.sh)

set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"

E="${1:-prod}"
case " $ENVS " in *" $E "*) ;; *) die "unknown environment '$E' (valid: $ENVS)" ;; esac
need docker kind kubectl
k() { kubectl --context "kind-$CLUSTER_NAME" "$@"; }

k -n "$E" get deployment api >/dev/null 2>&1 || die "'$E' is not deployed. Run ./start.sh $E first."

CM="$(k -n "$E" get configmap -o name | sed 's#configmap/##' | grep '^api-config' | head -1)"
SECRET="$(k -n "$E" get secret -o name | sed 's#secret/##' | grep '^api-secret' | head -1)"

if [ -z "$CM" ] || [ -z "$SECRET" ]; then
  die "could not find api-config / api-secret in namespace $E"
fi

INGRESS_IP="$(k -n ingress-nginx get svc ingress-nginx-controller -o jsonpath='{.spec.clusterIP}')"
[ -n "$INGRESS_IP" ] || die "ingress controller service not found"

log "Building the load test image"
docker build -f ./hang-backend/Dockerfile.loadtest -t hang-loadtest:local ./hang-backend
kind load docker-image hang-loadtest:local --name "$CLUSTER_NAME"

cleanup_users() {
  local envfile user
  envfile="$(env_db_envfile "$E")"
  user="$(get_kv "$envfile" POSTGRES_USER)"
  log "Removing load test users from $(env_db_name "$E")"
  docker exec "$(env_db_host "$E")" psql -h 127.0.0.1 -U "$user" -d "$(env_db_name "$E")" \
    -c "DELETE FROM users WHERE email LIKE 'loadtest\_%@example.com';" || true
}
trap cleanup_users EXIT

k -n "$E" delete job loadtest --ignore-not-found >/dev/null
sed -e "s#__ENV__#$E#g" -e "s#__INGRESS_IP__#$INGRESS_IP#g" \
    -e "s#__CONFIGMAP__#$CM#g" -e "s#__SECRET__#$SECRET#g" \
    k8s/loadtest/job.yml.tmpl | k apply -f -

log "Waiting for the pod to start (Grafana: https://grafana.$DOMAIN:$HTTPS_PORT, env=$E)"
k -n "$E" wait --for=condition=ready pod -l job-name=loadtest --timeout=180s

OUT="$LOCAL_DIR/loadtest-$E-$(date +%Y%m%d-%H%M%S).log"
k -n "$E" logs -f job/loadtest | tee "$OUT"
log "Saved to $OUT"

if ! k -n "$E" wait --for=condition=complete job/loadtest --timeout=120s >/dev/null 2>&1; then
  die "load test job did not complete; see the log above"
fi
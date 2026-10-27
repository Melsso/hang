#!/usr/bin/env bash

# Creates the kind cluster, installs ingress-nginx, trusts a local CA and prepares TLS.
# Safe to re-run. Node layout: 1 control-plane, 1 tainted "prod" worker, N shared workers.

set -euo pipefail
. "$(dirname "$0")/lib.sh"
need docker kind kubectl mkcert openssl
docker info >/dev/null 2>&1 || die "Docker is not running."
k() { kubectl --context "kind-$CLUSTER_NAME" "$@"; }

render_kind_config() {
  cat > "$KIND_CONFIG" <<KINDEOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: $CLUSTER_NAME
nodes:
  - role: control-plane
    image: $KIND_NODE_IMAGE
    extraPortMappings:
      - containerPort: 443
        hostPort: $HTTPS_PORT
        listenAddress: "127.0.0.1"
        protocol: TCP
  - role: worker
    image: $KIND_NODE_IMAGE
KINDEOF
  local i=0
  while [ "$i" -lt "$SHARED_WORKERS" ]; do
    printf '  - role: worker\n    image: %s\n' "$KIND_NODE_IMAGE" >> "$KIND_CONFIG"
    i=$((i + 1))
  done
}

log "Trusting the mkcert CA (may ask for your password once)"
mkcert -install
if [ ! -f "$CERT_DIR/tls.crt" ]; then
  mkdir -p "$CERT_DIR"
  mkcert -cert-file "$CERT_DIR/tls.crt" -key-file "$CERT_DIR/tls.key" "*.$DOMAIN" "$DOMAIN"
fi

docker network inspect kind >/dev/null 2>&1 || docker network create kind >/dev/null
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  log "Cluster '$CLUSTER_NAME' exists, skipping creation (recreate: kind delete cluster --name $CLUSTER_NAME)"
else
  if (exec 3<>"/dev/tcp/127.0.0.1/$HTTPS_PORT") 2>/dev/null; then
    die "Host port $HTTPS_PORT is in use. Free it, or run: HTTPS_PORT=<port> scripts/setup-env.sh (and re-register Google URIs)."
  fi
  render_kind_config
  log "Creating cluster (host port $HTTPS_PORT -> ingress)"
  kind create cluster --config "$KIND_CONFIG"
fi

k label node "$CLUSTER_NAME-control-plane" ingress-ready=true --overwrite >/dev/null
workers="$(k get nodes -l '!node-role.kubernetes.io/control-plane' -o name | sed 's#node/##' | sort)"
first=1
for n in $workers; do
  if [ "$first" -eq 1 ]; then
    k label node "$n" hang/pool=prod --overwrite >/dev/null
    k taint node "$n" hang/pool=prod:NoSchedule --overwrite >/dev/null
    first=0
  else
    k label node "$n" hang/pool=shared --overwrite >/dev/null
  fi
done

log "Installing ingress-nginx"
k apply -f "$INGRESS_MANIFEST" >/dev/null
k -n ingress-nginx rollout status deployment/ingress-nginx-controller --timeout=240s

for ns in $ENVS monitoring; do
  k create namespace "$ns" --dry-run=client -o yaml | k apply -f - >/dev/null
  k -n "$ns" create secret tls hang-tls --cert="$CERT_DIR/tls.crt" --key="$CERT_DIR/tls.key" \
    --dry-run=client -o yaml | k apply -f - >/dev/null
done

log "Cluster ready. After deploying, the environments will be at:"
for e in $ENVS; do echo "  $(env_url "$e")"; done

#!/usr/bin/env bash
# Blue/green deploy for the Arena app container.
#
# Keeps the current arena serving traffic while the new image builds and a
# standby (arena_next) becomes healthy, then flips Caddy upstream and swaps
# the primary container. Peak overlap is brief; arena_next uses less RAM and
# workers=0 so t3.medium can handle it.
#
# Usage (from repo root or deploy/):
#   ./deploy/scripts/deploy-bluegreen.sh
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${DEPLOY_DIR}"

COMPOSE=(docker compose)
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
fi

UPSTREAM_FILE="${DEPLOY_DIR}/Caddyfile.upstream"
ACTIVE_UPSTREAM="arena:8080"
NEXT_UPSTREAM="arena_next:8080"

caddy_service() {
  "${COMPOSE[@]}" ps -q caddy
}

set_upstream() {
  local target="$1"
  echo "reverse_proxy ${target}" > "${UPSTREAM_FILE}"
  echo "==> Caddy upstream -> ${target}"
  local cid
  cid="$(caddy_service || true)"
  if [[ -n "${cid}" ]]; then
    docker exec "${cid}" caddy reload --config /etc/caddy/Caddyfile
  else
    "${COMPOSE[@]}" up -d --no-deps caddy
  fi
}

wait_healthy() {
  local service="$1"
  local tries="${2:-36}"
  echo "==> Waiting for ${service} health..."
  for ((i = 1; i <= tries; i++)); do
    local cid status
    cid="$("${COMPOSE[@]}" ps -q "${service}" 2>/dev/null || true)"
    if [[ -n "${cid}" ]]; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${cid}")"
      if [[ "${status}" == "healthy" || "${status}" == "running" ]]; then
        if docker exec "${cid}" curl -fsS "http://127.0.0.1:8080/health" >/dev/null 2>&1; then
          echo "==> ${service} is ready"
          return 0
        fi
      fi
    fi
    sleep 5
  done
  echo "ERROR: ${service} did not become healthy in time" >&2
  return 1
}

cleanup_next() {
  "${COMPOSE[@]}" --profile bluegreen stop arena_next >/dev/null 2>&1 || true
  "${COMPOSE[@]}" --profile bluegreen rm -f arena_next >/dev/null 2>&1 || true
}

echo "==> Building new arena image (current container keeps serving)..."
"${COMPOSE[@]}" build arena

echo "==> Starting standby arena_next..."
cleanup_next
"${COMPOSE[@]}" --profile bluegreen up -d --no-deps arena_next
wait_healthy arena_next

echo "==> Cutting traffic to arena_next..."
set_upstream "${NEXT_UPSTREAM}"

echo "==> Recreating primary arena on new image..."
"${COMPOSE[@]}" stop arena
"${COMPOSE[@]}" up -d --no-deps --force-recreate arena
wait_healthy arena

echo "==> Cutting traffic back to arena..."
set_upstream "${ACTIVE_UPSTREAM}"

echo "==> Removing standby..."
cleanup_next

echo "==> Done."
"${COMPOSE[@]}" ps

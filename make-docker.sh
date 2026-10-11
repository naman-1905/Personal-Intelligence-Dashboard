#!/usr/bin/env bash
# make-docker.sh — rebuild & redeploy Docker services for news-dashboard.
#
# Only "built" services (web, api, scraper) are ever rebuilt. mongo/redis/ollama
# are plain images and are left untouched.
#
# Usage:
#   ./make-docker.sh                # detect changed services via git, redeploy just those
#   ./make-docker.sh web [api ...]  # redeploy specific service(s)
#   ./make-docker.sh all            # force rebuild & redeploy of web, api, scraper
#   ./make-docker.sh -n             # dry run: show what would happen, don't touch Docker
#   ./make-docker.sh -w [SECS]      # watch mode: poll git every SECS (default 5) and
#                                   # auto-redeploy whenever the set of changed files changes
#
# Change detection maps paths -> services (only runtime-affecting paths count):
#   apps/web/**         -> web
#   services/api/**     -> api
#   services/scraper/** -> scraper
#   infra/**, packages/** -> all built services (compose/env/mongo-init/shared schemas)
#   anything else       -> no-op (docs, tooling, this script; topics.txt is
#                          re-read by the scraper every cycle anyway)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT/infra/docker-compose.yml"
ENV_FILE="$ROOT/infra/.env"
BUILT_SERVICES=(web api scraper)

DRY_RUN=0
WATCH=0
POLL_SECS=5
ARGS=()

usage() {
  sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--dry-run) DRY_RUN=1; shift ;;
    -w|--watch)   WATCH=1
                 if [[ "${2:-}" =~ ^[0-9]+$ ]]; then POLL_SECS="$2"; shift; fi
                 shift ;;
    all)          ARGS+=("${BUILT_SERVICES[@]}"); shift ;;
    -h|--help)    usage; exit 0 ;;
    *)            ARGS+=("$1"); shift ;;
  esac
done

compose() { docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"; }

# Print the services that need a rebuild based on git status (one per line).
# Prints nothing when the tree is clean. Not a git repo -> all built services.
detect_services() {
  if ! git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf '%s\n' "${BUILT_SERVICES[@]}"
    return 0
  fi
  local changes line path list="" all=0 seen="" out="" s
  changes="$(git -C "$ROOT" status --porcelain || true)"
  [[ -n "$changes" ]] || return 0
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    path="${line:3}"
    case "$path" in
      apps/web*)          list+=" web" ;;
      services/api*)      list+=" api" ;;
      services/scraper*)  list+=" scraper" ;;
      infra/*|packages/*) all=1 ;;
      *)                  : ;;   # docs/tooling/topics.txt — no redeploy needed
    esac
  done <<< "$changes"
  if (( all )); then
    printf '%s\n' "${BUILT_SERVICES[@]}"
  else
    for s in $list; do
      case " $seen " in
        *" $s "*) ;;
        *) seen+=" $s"; out+="$s"$'\n' ;;
      esac
    done
    printf '%s' "$out"
  fi
}

validate_services() {
  local s t ok
  for s in "$@"; do
    ok=0
    for t in "${BUILT_SERVICES[@]}"; do [[ "$t" == "$s" ]] && ok=1; done
    if (( ! ok )); then
      echo "ERROR: unknown service '$s'. Valid services: ${BUILT_SERVICES[*]}" >&2
      exit 1
    fi
  done
}

verify() {
  local services=("$@") s need_health=0 i
  for s in "${services[@]}"; do
    if [[ "$s" == "api" || "$s" == "web" ]]; then need_health=1; fi
  done
  if (( need_health )); then
    echo "==> Waiting for API health..."
    for i in $(seq 1 30); do
      if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "    API healthy (http://localhost:8000)"
        break
      fi
      sleep 2
      if (( i == 30 )); then
        echo "    WARNING: API not healthy yet — check 'make logs'"
      fi
    done
  fi
  for s in "${services[@]}"; do
    if [[ "$s" == "web" ]]; then
      if curl -sf -o /dev/null http://localhost:3000; then
        echo "==> Web OK (http://localhost:3000)"
      else
        echo "    WARNING: web not responding yet — check 'make logs'"
      fi
    fi
  done
  compose ps
}

deploy() {
  local services=("$@")
  echo "==> Rebuilding & redeploying: ${services[*]}"
  if (( DRY_RUN )); then
    echo "    dry run: would run 'docker compose up -d --build ${services[*]}'"
    return 0
  fi
  compose up -d --build "${services[@]}"
  verify "${services[@]}"
}

# --- watch mode ---------------------------------------------------------------
if (( WATCH )); then
  echo "Watching for changes every ${POLL_SECS}s (Ctrl-C to stop)."
  trap 'echo; echo "Stopped watching."; exit 0' INT TERM
  last_state="$(git -C "$ROOT" status --porcelain || true)"
  while true; do
    sleep "$POLL_SECS"
    state="$(git -C "$ROOT" status --porcelain || true)"
    if [[ "$state" != "$last_state" ]]; then
      last_state="$state"
      echo "==> Change detected at $(date '+%Y-%m-%d %H:%M:%S')"
      services="$(detect_services)"
      if [[ -n "$services" ]]; then
        mapfile -t svc_array <<< "$services"
        deploy "${svc_array[@]}"
      else
        echo "    (changes only in no-op files, e.g. topics.txt — nothing to redeploy)"
      fi
    fi
  done
fi

# --- one-shot mode ------------------------------------------------------------
if (( ${#ARGS[@]} > 0 )); then
  validate_services "${ARGS[@]}"
  deploy "${ARGS[@]}"
else
  services="$(detect_services)"
  if [[ -z "$services" ]]; then
    echo "No changes detected (git tree is clean) — nothing to redeploy."
    echo "Tip: '$0 all' forces a full rebuild; '$0 web' targets one service."
    exit 0
  fi
  mapfile -t svc_array <<< "$services"
  deploy "${svc_array[@]}"
fi

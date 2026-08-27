#!/bin/bash
# cron wrapper - no LLM, retry once after delay
# usage: run_cron.sh <task_name> <python_script> [retry_delay_seconds]
set -u

TASK="${1:-}"
SCRIPT="${2:-}"
RETRY_DELAY="${3:-300}"

[ -z "$TASK" ] || [ -z "$SCRIPT" ] && { echo "usage: $0 <task> <script> [delay]" >&2; exit 2; }

# REPO is the current directory (set by crontab)
# cd "$REPO" || exit 1

# Token discovery: env first, then grep openclaw config
if [ -z "${TG_TOKEN:-}" ]; then
  for f in ~/.openclaw/config.yaml ~/.openclaw/config.json ~/.openclaw/config.yml ~/.openclaw/config.toml; do
    [ -f "$f" ] && TG_TOKEN=$(grep -oE '[A-Za-z0-9_-]{20,}:[A-Za-z0-9_-]{20,}' "$f" 2>/dev/null | head -1) && [ -n "$TG_TOKEN" ] && break
  done
fi
[ -z "${TG_TOKEN:-}" ] && [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && TG_TOKEN="$TELEGRAM_BOT_TOKEN"

TG_CHAT_ID="${TG_CHAT_ID:-5222823781}"
LOG_FILE="/tmp/cron_${TASK}_$(date +%Y%m%d_%H%M%S).log"
START_TIME=$(date '+%Y-%m-%d %H:%M')

notify_tg() {
  [ -z "${TG_TOKEN:-}" ] && { echo "[NO_TOKEN] $1" >&2; return; }
  curl -s -m 10 -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TG_CHAT_ID}" \
    --data-urlencode "parse_mode=HTML" \
    --data-urlencode "text=$1" >/dev/null 2>&1 || true
}

run_once() {
  local attempt="$1"
  local output rc
  output=$(python3 "$SCRIPT" 2>&1)
  rc=$?
  echo "$output" > "$LOG_FILE"
  if [ $rc -eq 0 ]; then
    notify_tg "✅ <b>${TASK}</b> ok

time: ${START_TIME}
attempt: ${attempt}
---
${output:0:3000}"
    return 0
  fi
  return $rc
}

if run_once "1/2"; then exit 0; fi
notify_tg "⏳ <b>${TASK}</b> failed, retry in ${RETRY_DELAY}s

time: ${START_TIME}
log: ${LOG_FILE}"
sleep "$RETRY_DELAY"
if run_once "2/2-retry"; then exit 0; fi
notify_tg "🚨 CRITICAL <b>${TASK}</b> still failed

time: ${START_TIME}
script: ${SCRIPT}
log: ${LOG_FILE}
---
$(tail -50 "$LOG_FILE")"
exit 1

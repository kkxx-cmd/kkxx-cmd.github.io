#!/bin/bash
# cron 任务统一包装器 — 完全脱离 LLM
# 用法: run_cron.sh <task_name> <python_script> [retry_delay_seconds]
#
# 行为:
#   1. cd 到 repo 目录
#   2. 运行 python 脚本，捕获输出
#   3. 失败则等待 delay（默认 5 分钟）重试 1 次
#   4. 无论如何，把状态发到 Telegram
#   5. 退出码: 0=成功，1=最终失败

set -u

TASK="${1:-}"
SCRIPT="${2:-}"
RETRY_DELAY="${3:-300}"

if [ -z "$TASK" ] || [ -z "$SCRIPT" ]; then
    echo "用法: $0 <task_name> <python_script> [retry_delay_seconds]"
    exit 2
fi

REPO="/home/qgg/.openclaw/workspace/repo"
cd "$REPO" || {
    notify_tg "🚨 [CRITICAL] $TASK 失败

时间: $(date '+%Y-%m-%d %H:%M')
错误: 无法 cd 到 $REPO"
    exit 1
}

LOG_FILE="/tmp/cron_${TASK}_$(date '+%Y%m%d').log"
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')

notify_tg() {
    local msg="$1"
    curl -s -m 10 -X POST "https://api.telegram.org/bot${TG_TOKEN:-}/sendMessage" \
        -d "chat_id=${TG_CHAT_ID:-5222823781}" \
        -d "parse_mode=HTML" \
        --data-urlencode "text=$msg" >/dev/null 2>&1 || true
}

run_once() {
    local attempt="$1"
    local output
    output=$(python3 "$SCRIPT" 2>&1)
    local rc=$?
    echo "$output" > "$LOG_FILE"
    if [ $rc -eq 0 ]; then
        notify_tg "✅ <b>$TASK</b> 更新成功

时间: $START_TIME
尝试: $attempt
脚本: $SCRIPT
---
$output"
        return 0
    else
        echo "$output" >&2
        return $rc
    fi
}

# 第一次
if run_once "1/2"; then
    exit 0
fi

# 失败，等 5 分钟重试
notify_tg "⏳ <b>$TASK</b> 第 1 次失败，${RETRY_DELAY}s 后重试

时间: $START_TIME
等待..."
sleep "$RETRY_DELAY"

if run_once "2/2 (重试)"; then
    exit 0
fi

# 最终失败
notify_tg "🚨 [CRITICAL] <b>$TASK</b> 重试后仍失败

时间: $START_TIME
脚本: $SCRIPT
---
日志: $LOG_FILE
$(tail -30 "$LOG_FILE")"
exit 1

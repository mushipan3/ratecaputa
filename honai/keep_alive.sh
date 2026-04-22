#!/bin/bash
# テザリング回線キープアライブ
# 1分ごとに軽量HTTPリクエストを送り続ける
# 使い方: bash keep_alive.sh &
#          kill %1  # 停止する場合

INTERVAL=60
TARGET="http://connectivitycheck.gstatic.com/generate_204"

echo "[keep_alive] 開始 (${INTERVAL}秒間隔, target=${TARGET})"

while true; do
    if curl -s --max-time 10 -o /dev/null -w "%{http_code}" "$TARGET" | grep -q "204"; then
        echo "[$(date '+%H:%M:%S')] keep_alive OK"
    else
        echo "[$(date '+%H:%M:%S')] keep_alive WARN: 応答なし"
    fi
    sleep "$INTERVAL"
done

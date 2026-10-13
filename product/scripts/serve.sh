#!/usr/bin/env bash
# Start/stop the loopback-only demo server. Usage: scripts/serve.sh start|stop|status
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
BIND="${STP_BIND:-127.0.0.1:8765}"
PIDFILE="${STP_PIDFILE:-/var/tmp/stp_d1a_server.pid}"
LOG="${STP_SERVER_LOG:-/var/tmp/stp_d1a_server.log}"
case "${1:-}" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then echo "already running pid $(cat "$PIDFILE")"; exit 0; fi
    cd "$HERE"; nohup python manage.py runserver "$BIND" --noreload >"$LOG" 2>&1 &
    echo $! >"$PIDFILE"; sleep 2
    if curl -fsS -o /dev/null "http://$BIND/"; then echo "serving http://$BIND/ (pid $(cat "$PIDFILE"))"; else echo "server failed to answer; see $LOG"; exit 1; fi;;
  stop)
    if [ -f "$PIDFILE" ]; then PID=$(cat "$PIDFILE"); if kill -0 "$PID" 2>/dev/null; then kill "$PID"; sleep 1; fi; rm -f "$PIDFILE"; echo "stopped pid $PID"; else echo "not running"; fi;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then echo "running pid $(cat "$PIDFILE") on $BIND"; else echo "not running"; fi;;
  *) echo "usage: $0 start|stop|status"; exit 2;;
esac

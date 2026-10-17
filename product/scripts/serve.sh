#!/usr/bin/env bash
# Start/stop the loopback-only demo server. Usage: scripts/serve.sh start|stop|status
#
# Safety rules (D1A-03):
# - The bind address is validated BEFORE anything is spawned: only 127.0.0.1:<1024-65535>.
#   Wildcard (0.0.0.0, ::, empty host), LAN addresses and hostnames are refused.
# - The control record (STP_PIDFILE) stores pid, kernel start time, checkout path, bind, python
#   and a per-launch token. A process is "ours" only if ALL of these match /proc/<pid>: start
#   time, cwd == this checkout, cmdline == "<python> manage.py runserver <bind> --noreload", and
#   STP_LAUNCH_TOKEN=<token> in its environment. Anything else is foreign and is never signalled.
# - The control record must be a regular file (not a symlink) owned by the current user, mode 600,
#   with exactly the six expected keys. Malformed / foreign / unverifiable records are kept and
#   the command fails without sending any signal.
# - A failed start health check stops only the process this command spawned.
# - The record is removed only after the process is confirmed gone; otherwise it is kept and the
#   command fails (exit 4/5).
# Exit codes: 0 ok, 1 start health check failed (own process stopped, record removed),
#             2 bad usage/bind, 3 foreign/malformed/stale record (nothing signalled),
#             4 stop not confirmed (record kept), 5 failed start whose cleanup could not be confirmed.
# Test hooks (stubs only): STP_PROC_ROOT, STP_KILL, STP_CURL, STP_PYTHON, STP_PRODUCT_DIR,
# STP_HEALTH_TRIES, STP_STOP_WAIT.
set -euo pipefail
HERE="${STP_PRODUCT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
HERE="$(cd "$HERE" && pwd -P)"
BIND="${STP_BIND-127.0.0.1:8765}"   # unset → default; set-but-empty → refused
PIDFILE="${STP_PIDFILE:-/var/tmp/stp_d1a_server.pid}"
LOG="${STP_SERVER_LOG:-/var/tmp/stp_d1a_server.log}"
PROC="${STP_PROC_ROOT:-/proc}"
KILL="${STP_KILL:-kill}"
CURL="${STP_CURL:-curl}"
PY="${STP_PYTHON:-python}"
TRIES="${STP_HEALTH_TRIES:-10}"
STOP_WAIT="${STP_STOP_WAIT:-10}"
WHY=

die() { echo "serve.sh: $2" >&2; exit "$1"; }

validate_bind() {
  local host port
  [[ "$BIND" =~ ^([^:]+):([0-9]{1,5})$ ]] || die 2 "refusing bind '$BIND': expected 127.0.0.1:<port>"
  host="${BASH_REMATCH[1]}"; port="${BASH_REMATCH[2]}"
  [ "$host" = "127.0.0.1" ] || die 2 "refusing bind '$BIND': only loopback 127.0.0.1 is allowed (no wildcard/LAN/hostname)"
  { [ "$port" -ge 1024 ] && [ "$port" -le 65535 ]; } || die 2 "refusing bind '$BIND': port must be 1024-65535"
}

proc_start_time() {  # field 22 of /proc/<pid>/stat (counted after the ')' that ends comm)
  local stat; stat="$(cat "$PROC/$1/stat" 2>/dev/null)" || return 1
  stat="${stat##*) }"
  # shellcheck disable=SC2086
  set -- $stat
  [ -n "${20:-}" ] || return 1
  echo "${20}"
}

proc_state() {  # field 3 of /proc/<pid>/stat
  local stat; stat="$(cat "$PROC/$1/stat" 2>/dev/null)" || return 1
  stat="${stat##*) }"; echo "${stat%% *}"
}

expected_cmdline() { printf '%s\0manage.py\0runserver\0%s\0--noreload\0' "$1" "$2"; }

# 0 = valid record loaded; 3 = no record; 4 = unusable record (message on stdout)
read_record() {
  [ -e "$PIDFILE" ] || [ -L "$PIDFILE" ] || return 3
  if [ -L "$PIDFILE" ]; then echo "control record is a symlink"; return 4; fi
  if [ ! -f "$PIDFILE" ]; then echo "control record is not a regular file"; return 4; fi
  if [ "$(stat -c %u "$PIDFILE")" != "$(id -u)" ]; then echo "control record not owned by uid $(id -u)"; return 4; fi
  if [ "$(stat -c %a "$PIDFILE")" != "600" ]; then echo "control record mode is not 600"; return 4; fi
  R_PID=; R_START=; R_CHECKOUT=; R_BIND=; R_TOKEN=; R_PY=
  local k v n=0
  while IFS='=' read -r k v; do
    case "$k" in
      pid) R_PID="$v";; start) R_START="$v";; checkout) R_CHECKOUT="$v";;
      bind) R_BIND="$v";; token) R_TOKEN="$v";; python) R_PY="$v";;
      *) echo "unknown key in control record: $k"; return 4;;
    esac
    n=$((n+1))
  done < "$PIDFILE"
  if ! [[ "$R_PID" =~ ^[1-9][0-9]{0,9}$ ]]; then echo "control record has no valid pid"; return 4; fi
  if ! { [[ "$R_START" =~ ^[0-9]+$ ]] && [[ "$R_TOKEN" =~ ^[0-9a-f]{32}$ ]] && [ -n "$R_CHECKOUT" ] && [ -n "$R_BIND" ] && [ -n "$R_PY" ]; }; then
    echo "control record is incomplete"; return 4; fi
  if [ "$n" != 6 ]; then echo "control record has unexpected line count"; return 4; fi
  return 0
}

# 0 = alive and ours; 1 = gone; 2 = alive but NOT ours (foreign / pid reused / unverifiable). Sets WHY.
identity() {
  local pid="$1" st
  WHY=
  [ -d "$PROC/$pid" ] || return 1
  # a zombie/dead entry has exited (it only awaits reaping by its parent): treat as gone
  case "$(proc_state "$pid" || true)" in Z|X|x) return 1;; esac
  st="$(proc_start_time "$pid")" || { WHY="cannot read start time"; return 2; }
  [ "$st" = "$R_START" ] || { WHY="start time differs (pid reused?)"; return 2; }
  [ "$R_CHECKOUT" = "$HERE" ] || { WHY="record belongs to another checkout"; return 2; }
  [ "$(readlink "$PROC/$pid/cwd" 2>/dev/null || true)" = "$R_CHECKOUT" ] || { WHY="cwd is not this checkout"; return 2; }
  cmp -s <(cat "$PROC/$pid/cmdline" 2>/dev/null || true) <(expected_cmdline "$R_PY" "$R_BIND") || { WHY="command line differs"; return 2; }
  { tr '\0' '\n' < "$PROC/$pid/environ" 2>/dev/null || true; } | grep -qx "STP_LAUNCH_TOKEN=$R_TOKEN" || { WHY="launch token missing"; return 2; }
  return 0
}

# Stop a verified process of ours. 0 = confirmed gone; 4 = could not signal / still alive.
stop_ours() {
  local pid="$1" i rc
  if ! "$KILL" -TERM "$pid" 2>/dev/null; then
    rc=0; identity "$pid" || rc=$?
    [ $rc -eq 1 ] && return 0
    echo "serve.sh: kill -TERM $pid failed" >&2; return 4
  fi
  for ((i=0; i<STOP_WAIT*5; i++)); do
    rc=0; identity "$pid" || rc=$?
    [ $rc -eq 1 ] && return 0
    sleep 0.2
  done
  echo "serve.sh: pid $pid still alive after ${STOP_WAIT}s" >&2; return 4
}

case "${1:-}" in
  start)
    validate_bind
    rc=0; msg="$(read_record)" || rc=$?
    if [ $rc -eq 0 ]; then
      read_record >/dev/null
      irc=0; identity "$R_PID" || irc=$?
      [ $irc -eq 0 ] && { echo "already running pid $R_PID on $R_BIND"; exit 0; }
      [ $irc -eq 2 ] && die 3 "control record points to pid $R_PID which is not ours ($WHY); refusing to overwrite $PIDFILE"
      die 3 "stale control record for pid $R_PID (process gone); run 'stop' to clear it first"
    elif [ $rc -ne 3 ]; then
      die 3 "unusable control record $PIDFILE ($msg); refusing to start"
    fi
    TOKEN="$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')"
    cd "$HERE"
    STP_LAUNCH_TOKEN="$TOKEN" nohup "$PY" manage.py runserver "$BIND" --noreload >"$LOG" 2>&1 &
    PID=$!
    sleep 0.3
    START="$(proc_start_time "$PID" || true)"
    ( umask 077; tmp="$PIDFILE.tmp.$$"
      printf 'pid=%s\nstart=%s\ncheckout=%s\nbind=%s\ntoken=%s\npython=%s\n' "$PID" "$START" "$HERE" "$BIND" "$TOKEN" "$PY" >"$tmp"
      chmod 600 "$tmp"; mv -f "$tmp" "$PIDFILE" )
    ok=0
    for ((i=0; i<TRIES; i++)); do
      if "$CURL" -fsS -o /dev/null -m 2 "http://$BIND/" 2>/dev/null; then ok=1; break; fi
      sleep 0.5
    done
    if [ $ok = 1 ]; then echo "serving http://$BIND/ (pid $PID)"; exit 0; fi
    echo "serve.sh: health check failed; stopping only the process started here (pid $PID); see $LOG" >&2
    rc=0; read_record >/dev/null || rc=$?
    [ $rc -eq 0 ] || die 5 "control record unreadable after failed start; pid $PID left untouched"
    irc=0; identity "$PID" || irc=$?
    if [ $irc -eq 1 ]; then rm -f "$PIDFILE"; exit 1; fi
    [ $irc -eq 0 ] || die 5 "spawned pid $PID failed identity check ($WHY); not signalling it; record kept"
    if stop_ours "$PID"; then rm -f "$PIDFILE"; exit 1; fi
    die 5 "could not confirm spawned pid $PID stopped; record kept at $PIDFILE"
    ;;
  stop)
    rc=0; msg="$(read_record)" || rc=$?
    [ $rc -eq 3 ] && { echo "not running"; exit 0; }
    [ $rc -eq 0 ] || die 3 "refusing to act on control record $PIDFILE ($msg); nothing was signalled"
    read_record >/dev/null
    irc=0; identity "$R_PID" || irc=$?
    if [ $irc -eq 1 ]; then rm -f "$PIDFILE"; echo "process $R_PID already gone; stale record removed"; exit 0; fi
    [ $irc -eq 0 ] || die 3 "pid $R_PID is not ours ($WHY); not signalling it; record kept"
    if stop_ours "$R_PID"; then rm -f "$PIDFILE"; echo "stopped pid $R_PID"; exit 0; fi
    die 4 "stop not confirmed for pid $R_PID; record kept at $PIDFILE"
    ;;
  status)
    rc=0; msg="$(read_record)" || rc=$?
    if [ $rc -eq 3 ]; then echo "not running"; exit 0; fi
    [ $rc -eq 0 ] || { echo "unusable control record ($msg)"; exit 3; }
    read_record >/dev/null
    irc=0; identity "$R_PID" || irc=$?
    case $irc in 0) echo "running pid $R_PID on $R_BIND";; 1) echo "not running (stale record)";; *) echo "record points to foreign pid $R_PID ($WHY)"; exit 3;; esac
    ;;
  *) echo "usage: $0 start|stop|status"; exit 2;;
esac

#!/usr/bin/env bash
# Private, local-only PostgreSQL 16 cluster for the D1-A synthetic catalog.
# Unix socket only (listen_addresses=''), trust auth on the socket, data under $STP_PG_DIR.
# Usage: scripts/pg_local.sh init|start|stop|status|createdb
set -euo pipefail
STP_PG_DIR="${STP_PG_DIR:-/var/tmp/stp_d1a_pg}"
STP_PG_PORT="${STP_PG_PORT:-54329}"
STP_PG_USER="${STP_PG_USER:-stp_d1a}"
STP_DB_NAME="${STP_DB_NAME:-stp_catalog}"
PGBIN="${PGBIN:-$(ls -d /usr/lib/postgresql/16/bin 2>/dev/null || dirname "$(command -v pg_ctl)")}"
DATA="$STP_PG_DIR/data"; SOCK="$STP_PG_DIR/sock"
run() { if [ "$(id -u)" = 0 ]; then runuser -u postgres -- "$@"; else "$@"; fi; }
case "${1:-}" in
  init)
    mkdir -p "$DATA" "$SOCK"; chmod 700 "$DATA" "$SOCK"
    if [ "$(id -u)" = 0 ]; then chown -R postgres:postgres "$STP_PG_DIR"; fi
    run "$PGBIN/initdb" -D "$DATA" -U "$STP_PG_USER" --auth-local=trust -E UTF8 --locale=C.UTF-8 >/dev/null
    echo "initdb done: $DATA (user $STP_PG_USER, socket $SOCK, port $STP_PG_PORT)";;
  start)
    run "$PGBIN/pg_ctl" -D "$DATA" -o "-c listen_addresses='' -c unix_socket_directories=$SOCK -c port=$STP_PG_PORT" -l "$STP_PG_DIR/pg.log" -w start >/dev/null
    echo "postgres started (socket only, no TCP)";;
  stop)
    run "$PGBIN/pg_ctl" -D "$DATA" -m fast -w stop >/dev/null && echo "postgres stopped";;
  status)
    run "$PGBIN/pg_ctl" -D "$DATA" status || true;;
  createdb)
    run "$PGBIN/psql" -h "$SOCK" -p "$STP_PG_PORT" -U "$STP_PG_USER" -d postgres -Atc "select 1 from pg_database where datname='$STP_DB_NAME'" | grep -q 1 \
      || run "$PGBIN/psql" -h "$SOCK" -p "$STP_PG_PORT" -U "$STP_PG_USER" -d postgres -Atc "create database $STP_DB_NAME"
    echo "database $STP_DB_NAME ready";;
  psql)
    shift; run "$PGBIN/psql" -h "$SOCK" -p "$STP_PG_PORT" -U "$STP_PG_USER" -d "$STP_DB_NAME" "$@";;
  *) echo "usage: $0 init|start|stop|status|createdb|psql"; exit 2;;
esac

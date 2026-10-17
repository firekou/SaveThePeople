#!/usr/bin/env bash
# Reproducible HTTP / DB / DB-down / lifecycle evidence run (AUTHOR_EVIDENCE, synthetic only).
# Every step's exit status is recorded; the script exits non-zero if ANY step deviates from its
# expectation, so a later success cannot hide an earlier failure.
# Prereq: venv active, postgres cluster initialised (scripts/pg_local.sh init && createdb) and migrated.
# Output: ${STP_EVIDENCE_DIR:-evidence/repair-recovery}/http_db_evidence.txt (+ 360px screenshots).
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
OUT="${STP_EVIDENCE_DIR:-evidence/repair-recovery}"; mkdir -p "$OUT"
exec > >(tee "$OUT/http_db_evidence.txt") 2>&1
B="http://${STP_BIND:-127.0.0.1:8765}"; PORT="${B##*:}"; AS="as_of=${STP_AS_OF:-2026-10-13}"
PGDIR="${STP_PG_DIR:-/var/tmp/stp_d1a_pg}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FAILS=(); N=0
# check NAME EXPECT RC : EXPECT is "zero" or "nonzero"
check() {
  N=$((N+1)); local name="$1" expect="$2" rc="$3" ok=1
  if [ "$expect" = zero ] && [ "$rc" -ne 0 ]; then ok=0; fi
  if [ "$expect" = nonzero ] && [ "$rc" -eq 0 ]; then ok=0; fi
  if [ "$ok" = 1 ]; then echo "STEP_OK   [$name] exit=$rc expected=$expect"
  else echo "STEP_FAIL [$name] exit=$rc expected=$expect"; FAILS+=("$name(exit=$rc,expected=$expect)"); fi
}
run() { local name="$1" expect="$2"; shift 2; echo; echo "## $name"; "$@"; check "$name" "$expect" $?; }
# assert NAME CONDITION-COMMAND... : a content assertion counted like a step
assert() { local name="$1"; shift; if "$@"; then check "$name" zero 0; else check "$name" zero 1; fi; }

echo "# D1-A HTTP / DB / lifecycle evidence (AUTHOR_EVIDENCE, synthetic only)"
echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) git_head=$(git rev-parse HEAD 2>/dev/null) dirty=$(git status --porcelain 2>/dev/null | wc -l)"
echo "python=$(python --version 2>&1) django=$(python -c 'import django;print(django.get_version())') psycopg=$(python -c 'import psycopg;print(psycopg.__version__)')"

run "pg start" zero scripts/pg_local.sh start
run "migrate" zero python manage.py migrate --noinput
run "migrate --check" zero python manage.py migrate --check
run "import (legal, idempotent re-run)" zero python manage.py import_synthetic_catalog
COUNTS_SQL="select 'resources',count(*) from catalog_resource union all select 'versions',count(*) from catalog_resourceversion union all select 'sources',count(*) from catalog_source union all select 'scopes',count(*) from catalog_householdscopedefinition union all select 'regions',count(*) from catalog_region union all select 'import_runs',count(*) from catalog_importrun union all select 'non_synthetic_rows',(select count(*) from catalog_resource where not is_synthetic)+(select count(*) from catalog_source where not is_synthetic);"
echo; echo "## DB counts before illegal import"; scripts/pg_local.sh psql -Atc "$COUNTS_SQL" | tee "$TMP/c1"; check "DB counts before" zero "${PIPESTATUS[0]}"
python - "$TMP" <<'PY'
import json, sys
d = json.load(open('../docs/platform/examples/synthetic_resources.json'))
a = json.loads(json.dumps(d)); a['resources'][0]['is_synthetic'] = False
json.dump(a, open(sys.argv[1] + '/bad_flag.json', 'w'))
b = json.loads(json.dumps(d)); b['sources'][0]['url_or_ref'] = 'https://example.invalid.attacker.invalid/x'
json.dump(b, open(sys.argv[1] + '/bad_url.json', 'w'))
PY
run "illegal import: per-record is_synthetic=false (non-zero expected)" nonzero python manage.py import_synthetic_catalog --path "$TMP/bad_flag.json"
run "illegal import: attacker suffix URL (non-zero expected)" nonzero python manage.py import_synthetic_catalog --path "$TMP/bad_url.json"
echo; echo "## DB counts after illegal imports (must equal before)"; scripts/pg_local.sh psql -Atc "$COUNTS_SQL" | tee "$TMP/c2"; check "DB counts after" zero "${PIPESTATUS[0]}"
assert "rollback: counts unchanged" cmp -s "$TMP/c1" "$TMP/c2"
echo; echo "## DB listen_addresses (empty => unix socket only)"; scripts/pg_local.sh psql -Atc "show listen_addresses;" | tee "$TMP/la"; check "listen_addresses query" zero "${PIPESTATUS[0]}"
assert "listen_addresses empty" test -z "$(tr -d '[:space:]' < "$TMP/la")"
run "DB CHECK negative: non-synthetic row (non-zero expected)" nonzero scripts/pg_local.sh psql -Atc "insert into catalog_resource(resource_key,canonical_name,level,categories,risk_tier,is_synthetic) values ('TW-REAL-999','x','LOCAL','[]','LOW',false);"
run "server refuses wildcard bind (non-zero expected)" nonzero env STP_BIND=0.0.0.0:8765 scripts/serve.sh start
run "server start (loopback)" zero scripts/serve.sh start
run "server status" zero scripts/serve.sh status
echo; echo "## listener check via /proc/net/tcp (expect 127.0.0.1 only)"
python - "$PORT" <<'PY' | tee "$TMP/listen"
import socket, struct, sys
port = int(sys.argv[1])
for line in open('/proc/net/tcp').read().splitlines()[1:]:
    p = line.split(); ip, pt = p[1].split(':')
    if int(pt, 16) == port and p[3] == '0A': print('LISTEN', socket.inet_ntoa(struct.pack('<I', int(ip, 16))), port)
PY
assert "listener is loopback only" bash -c "grep -q 'LISTEN 127.0.0.1' '$TMP/listen' && ! grep -v 'LISTEN 127.0.0.1' '$TMP/listen' | grep -q ."
# url expected_status expected_marker
while IFS='|' read -r u want marker; do
  echo; echo "## GET $u (expect $want)"
  code=$(curl -sS -o "$TMP/body.html" -w "%{http_code}" "$B$u"); rc=$?
  echo "http_status=$code curl_exit=$rc bytes=$(wc -c < "$TMP/body.html")"
  echo "keys: $(grep -oE 'TW-DEMO-[A-Z]+-[0-9]+' "$TMP/body.html" | sort -u | tr '\n' ' ')"
  grep -oE '共 [0-9]+ 項|尚無已查核資源|查無此(地區|類別)|歷史版本：已過期|期限未知|截止日未知|找不到這個頁面|不在公開列表|[0-9-]+ 起適用' "$TMP/body.html" | sort -u | tr '\n' ';'; echo
  check "GET $u curl" zero "$rc"
  assert "GET $u status=$want" test "$code" = "$want"
  [ -n "$marker" ] && assert "GET $u contains '$marker'" grep -q -- "$marker" "$TMP/body.html"
done <<LIST
/?$AS|200|共 5 項
/?region=DEMO-A&$AS|200|
/?region=DEMO-B&$AS|200|
/?region=DEMO-B&category=EDUCATION&$AS|200|
/?category=FOOD_GOODS&$AS|200|
/?status=EXPIRED&$AS|200|
/?region=NOWHERE|200|查無此地區
/?as_of=2026-07-01|200|
/resources/TW-DEMO-FOOD-005/?$AS|200|TW-DEMO-FOOD-005
/resources/TW-DEMO-RENT-006/?$AS|200|歷史版本：已過期
/resources/TW-DEMO-NOPE-999/|404|找不到這個頁面
LIST
echo; echo "## GET /api/public/resources"
curl -sS "$B/api/public/resources?$AS" | python -c "import sys,json; d=json.load(sys.stdin); print('count',d['count'],'is_synthetic',d['is_synthetic']); [print(' ',r['resource_key'],r['status'],r['badges'],'eff_unknown=',r['effective_unknown'],'last_src=',(r['last_source_retrieved_at'] or '')[:10]) for r in d['results']]; sys.exit(0 if d['is_synthetic'] is True and d['count']>0 else 1)"
check "API JSON" zero "${PIPESTATUS[1]}"
run "DB-down: stop postgres" zero scripts/pg_local.sh stop
echo; echo "## DB-down: GET / must be a safe 500"
code=$(curl -sS -o "$TMP/down.html" -w "%{http_code}" "$B/"); check "DB-down curl" zero $?
echo "http_status=$code"; assert "DB-down status=500" test "$code" = 500
leaks=$(grep -cE "Traceback|OperationalError|psycopg|SECRET|$PGDIR|/var/tmp" "$TMP/down.html"); echo "leak_scan=$leaks"
assert "DB-down no leak" test "$leaks" = 0
assert "DB-down friendly message" grep -q '資料暫時無法載入' "$TMP/down.html"
run "postgres restart" zero scripts/pg_local.sh start
code=$(curl -sS -o /dev/null -w "%{http_code}" "$B/?$AS"); check "recover curl" zero $?; echo "recovered http_status=$code"
assert "recovered status=200" test "$code" = 200
run "360px + keyboard UI evidence (playwright)" zero env STP_AS_OF="${STP_AS_OF:-2026-10-13}" python scripts/capture_evidence.py "$B" "$OUT"
run "server stop" zero scripts/serve.sh stop
run "server stop again (idempotent)" zero scripts/serve.sh stop
run "postgres stop" zero scripts/pg_local.sh stop
echo; echo "## cleanup check"
ps -eo pid,args | grep -E "manage.py runserver|postgres -D $PGDIR" | grep -v grep; rc=$?
check "no task processes remain (grep exit 1 expected)" nonzero "$rc"
curl -sS -o /dev/null -m 2 "$B/" 2>/dev/null; check "post-stop curl refused (non-zero expected)" nonzero $?
echo "other postgres clusters untouched: $(pg_lsclusters 2>/dev/null | tail -n +2 | tr -s ' ')"
echo; echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "SUMMARY steps=$N failures=${#FAILS[@]}"
for f in "${FAILS[@]}"; do echo "  FAILED: $f"; done
[ "${#FAILS[@]}" -eq 0 ]

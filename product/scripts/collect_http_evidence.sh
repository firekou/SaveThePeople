#!/usr/bin/env bash
# Reproducible HTTP / DB / DB-down / cleanup evidence run. Writes evidence/http_db_evidence.txt.
# Prereq: venv active, postgres cluster initialised (scripts/pg_local.sh init && createdb) and migrated.
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"; mkdir -p evidence
exec > >(tee evidence/http_db_evidence.txt) 2>&1
B="http://${STP_BIND:-127.0.0.1:8765}"; AS="as_of=${STP_AS_OF:-2026-10-13}"
echo "# D1-A HTTP / DB / lifecycle evidence (AUTHOR_EVIDENCE, synthetic only)"; echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "python=$(python --version 2>&1) django=$(python -c 'import django;print(django.get_version())') psycopg=$(python -c 'import psycopg;print(psycopg.__version__)')"
echo; echo "## pg start"; scripts/pg_local.sh start; echo "exit=$?"
echo; echo "## migrate --check"; python manage.py migrate --check; echo "exit=$?"
echo; echo "## import (idempotent re-run)"; python manage.py import_synthetic_catalog; echo "exit=$?"
echo; echo "## DB counts via psql"; scripts/pg_local.sh psql -Atc "select 'resources',count(*) from catalog_resource union all select 'versions',count(*) from catalog_resourceversion union all select 'sources',count(*) from catalog_source union all select 'scopes',count(*) from catalog_householdscopedefinition union all select 'regions',count(*) from catalog_region union all select 'import_runs',count(*) from catalog_importrun;"; echo "exit=$?"
echo; echo "## DB listen_addresses (empty => unix socket only)"; scripts/pg_local.sh psql -Atc "show listen_addresses;"; echo "exit=$?"
echo; echo "## DB CHECK constraint negative: non-synthetic row must be rejected"; scripts/pg_local.sh psql -Atc "insert into catalog_resource(resource_key,canonical_name,level,categories,risk_tier,is_synthetic) values ('TW-REAL-999','x','LOCAL','[]','LOW',false);"; echo "exit=$? (non-zero expected)"
echo; echo "## server start (loopback)"; scripts/serve.sh start; echo "exit=$?"
echo; echo "## listener check via /proc/net/tcp (expect 127.0.0.1 only)"; python - <<'PY'
import socket,struct
for line in open('/proc/net/tcp').read().splitlines()[1:]:
    p=line.split(); ip,port=p[1].split(':')
    if int(port,16)==8765 and p[3]=='0A': print('LISTEN',socket.inet_ntoa(struct.pack('<I',int(ip,16))),int(port,16))
PY
for u in "/?$AS" "/?region=DEMO-A&$AS" "/?region=DEMO-B&$AS" "/?region=DEMO-B&category=EDUCATION&$AS" "/?category=FOOD_GOODS&$AS" "/?status=EXPIRED&$AS" "/?region=NOWHERE" "/?as_of=2026-07-01" "/resources/TW-DEMO-FOOD-005/?$AS" "/resources/TW-DEMO-RENT-006/?$AS" "/resources/TW-DEMO-NOPE-999/"; do
  echo; echo "## GET $u"; curl -sS -o /tmp/stp_body.html -w "http_status=%{http_code} bytes=%{size_download} content_type=%{content_type}\n" "$B$u"; echo "exit=$?"
  echo "keys: $(grep -oE 'TW-DEMO-[A-Z]+-[0-9]+' /tmp/stp_body.html | sort -u | tr '\n' ' ')"
  grep -oE '共 [0-9]+ 項|尚無已查核資源|查無此(地區|類別)|歷史版本：已過期|期限未知|截止日未知|找不到這個頁面|不在公開列表|[0-9-]+ 起適用' /tmp/stp_body.html | sort -u | tr '\n' ';'; echo; done
echo; echo "## GET /api/public/resources"; curl -sS "$B/api/public/resources?$AS" | python -c "import sys,json; d=json.load(sys.stdin); print('count',d['count'],'is_synthetic',d['is_synthetic']); [print(' ',r['resource_key'],r['status'],r['badges'],'eff_unknown=',r['effective_unknown'],'last_src=',r['last_source_retrieved_at'][:10]) for r in d['results']]"; echo "exit=$?"
echo; echo "## DB-down negative: stop postgres, GET / must be a safe 500"; scripts/pg_local.sh stop; curl -sS -o /tmp/stp_down.html -w "http_status=%{http_code} bytes=%{size_download}\n" "$B/"; echo "curl_exit=$?"
echo "leak_scan (expect 0): $(grep -cE 'Traceback|OperationalError|stp_d1a|54329|/var/tmp|psycopg|SECRET' /tmp/stp_down.html)"; grep -o '資料暫時無法載入' /tmp/stp_down.html | head -1
echo; echo "## postgres restart, GET / recovers"; scripts/pg_local.sh start; curl -sS -o /dev/null -w "http_status=%{http_code}\n" "$B/?$AS"; echo "exit=$?"
echo; echo "## 360px UI evidence (playwright)"; STP_AS_OF="${STP_AS_OF:-2026-10-13}" python scripts/capture_evidence.py "$B" evidence; echo "exit=$?"
echo; echo "## stop server and task postgres; cleanup check"; scripts/serve.sh stop; scripts/pg_local.sh stop
echo "remaining task processes (expect none):"; ps -eo pid,args | grep -E 'manage.py runserver|postgres -D /var/tmp/stp_d1a_pg' | grep -v grep; echo "grep_exit=$? (1 = none)"
curl -sS -o /dev/null -m 2 "$B/" 2>/dev/null; echo "post-stop curl exit=$? (non-zero expected)"
echo "other postgres clusters untouched: $(pg_lsclusters 2>/dev/null | tail -n +2 | tr -s ' ')"
echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

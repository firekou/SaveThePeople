# D1 隔離環境驗證回覆（D1_ENVIRONMENT）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-D1-ENVIRONMENT｜stage：D1_ENVIRONMENT｜一次交付
工單：issuecomment-6112643046 + GPT_D1_ENVIRONMENT_PACKET_20261012.md｜claim：issuecomment-6112649232（session_01MvUGYirGBtHVdHk3mYxAkh）
source：9dd0c5d3c9c1293f6995e42f44b4607661631996（handoff edd0df68bf9323d4677251ddf9300652a73290b3 的 ancestor）｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
時間（本 session 時鐘，2026-10-11 UTC）：開始 19:11Z，DB 停止與清理完成 19:12Z；總耗時遠低於 45 分鐘（REPORTED）。
層級：隔離環境能力驗證（AUTHOR_EVIDENCE）。**不是產品、不是 Docker 驗收、不是 Django 專案或 migration**；只證明「Django 6.1 的 PostgreSQL backend 能經私人 Unix socket 連上 PostgreSQL 16、交易 rollback 有效、伺服器停止後連線失敗」。

## 1. 身分與隔離
- 本 session 為 root（uid 0）。依工單「先確認既有非 root 身分」：`getent passwd` 顯示既有非系統帳號 `ubuntu`(1000)、`postgres`(102)、`claude`(999)。以 `setpriv --reuid=999 --regid=999 --clear-groups` **降權**成既有的 `claude`（未新增 OS 使用者、未提權、未讀其家目錄；HOME 指向任務目錄）執行 venv／initdb／postgres／Django。
- 任務目錄：`/tmp/stp-d1-env`（700，屬 uid 999）。
- 為了讓非 root 身分可用 proxy 的 CA：把 proxy 環境提供的 CA 憑證（公開 CA 檔，非私鑰）複製到任務目錄並以環境變數覆寫路徑；未列印或保存任何 proxy 憑證／環境變數值。（一次嘗試以 `env | grep` 列舉 proxy 變數名稱被平台自動分類器拒絕，我未重試也未繞過，改以覆寫已知的 CA 路徑變數完成。）

## 2. 安裝（僅任務 venv；`pip --isolated`）
命令（摘要，已省略 proxy 設定）：`python3 -m venv /tmp/stp-d1-env/venv`（exit 0）→
`pip --isolated --disable-pip-version-check install --no-input Django "psycopg[binary]"`（**exit 0**；第一次因 CA 路徑在非 root 不可讀失敗 exit 1、無任何套件變更；第二次成功，共 1 次重試，皆為安全重試）。
解析結果（`pip freeze`）：Django==6.1.2、psycopg==3.3.6、psycopg-binary==3.3.6、asgiref==3.12.1、sqlparse==0.6.0；venv Python 3.13.16（`PATH=/usr/bin:/bin` 下的 python3；與本 session 另一個 PATH 下的 3.11.17 不同，本驗證只使用 venv 的 3.13.16）。
來源：標準 PyPI（經平台 proxy）；未指定鏡像、未讀 pip 帳號設定。安裝日誌顯示下載的 wheel：django-6.1.2-py3-none-any.whl（8.4 MB）、psycopg-3.3.6-py3-none-any.whl、psycopg_binary-3.3.6-cp313-manylinux2014_x86_64.whl（5.2 MB）、asgiref-3.12.1、sqlparse-0.6.0。
hash：**未取得 wheel 檔本身的 SHA256**（pip 快取為不可直接雜湊的 HTTP 快取，且不重新下載以免額外外部呼叫）；改記錄已安裝套件 `*.dist-info/RECORD` 檔的 SHA256：
- django-6.1.2: f272cca62fb90d7d03c812a9f27336e6312507aed78f82f48ded8f997b741416
- asgiref-3.12.1: d743f93b9d41e4eba88d3dec0d15e3910016670085507ba73c92914d37675006
- psycopg-3.3.6: 50ed0bd3dc95c1c22c2fa32f52cec505e04bdbd1c82d35c991d9134652e3c7fe
- psycopg_binary-3.3.6: 338ee68fe0da96b846f087bca19fef6f81bb73db6c24be251fd27c97b0af6465
- sqlparse-0.6.0: 9fda50ad78c20bb9eb8b7c207edf7fd04ed30eb3fbf8490a51ef4564f4488a9a
（缺口：下一包若要鎖定供應鏈，需另行以 `pip download --require-hashes` 流程取得 wheel hash；本工單未授權新增 lock／依賴檔。）

## 3. PostgreSQL（既存 16.15 執行檔，私人 Unix socket）
- `initdb -D /tmp/stp-d1-env/pgdata -A trust -U stp_smoke --no-sync -E UTF8 --locale=C.UTF-8`（umask 077）→ **exit 0**。
- 設定：`listen_addresses = ''`（不開 TCP）、`unix_socket_directories = /tmp/stp-d1-env/sock`、`unix_socket_permissions = 0700`、`fsync = off`（只為測試速度；非正式設定）。`-A trust` 僅因 socket 為 0700 且屬 uid 999 目錄，只有該身分（與 root）能連。
- `pg_ctl ... -w start` → **exit 0**，`pg_ctl status`：running；`psql`：PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)，`show listen_addresses` 為空，socket 目錄如上；`ss -ltnp | grep 5432` 計數 0（無 TCP 5432 監聽）。未碰任何既有 DB。

## 4. 煙霧測試（Django 6.1.2 → psycopg 3.3.6 → PostgreSQL 16.15）
腳本 `smoke.py`（合成值，內容見 §7）。實際輸出：
```
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | no_tcp_peer(unix socket): True
inside_tx=1 after_rollback=0 after_commit=1 all_synthetic=True
POSITIVE_OK
positive exit=0
```
預期與實值：交易內 1、rollback 後 **0**、另一交易 commit 後 1、全部列 `is_synthetic=true`（預期 (1,0,1,True)，實值相同）。測試表 `stp_d1_smoke` 只存在於任務 DB，測試後 `drop table`。未執行任何產品 migration／admin／使用者／家庭資料。
**負向控制（伺服器停止後）**：`pg_ctl -m fast -w stop` → exit 0，`pg_ctl status` → `no server running`，exit 3；再跑 `smoke.py down`：
```
NEGATIVE_OK OperationalError: connection is bad: connection to server on socket "/tmp/stp-d1-env/sock/.s.PGSQL.5432" failed: No such file or directory
negative exit=0
```
是 `django.db.OperationalError`（連線不可用），不是語法錯誤或 import 錯誤。

## 5. 清理
- DB 已停止（status exit 3）。停止後曾見一個 `postgres` zombie（`<defunct>`，PID 381，等 shell 回收），隨後 `ps -p 381` 已無；`pgrep -u 999 postgres` 計數 0；`ss -lnx` 對任務 socket 計數 0。
- 已刪除：`pgdata/`、`sock/`、`pg.log`、`initdb.log`。
- 保留（工單允許）：`/tmp/stp-d1-env/venv`（約 86 MB，Python 3.13.16 + 上述套件）、`.cache`（pip 快取）、`ca.crt`（公開 CA 複本）、`smoke.py`、`pip_install.log`；任務目錄總計約 100 MB，磁碟充足（`/` 約 30 GB 可用）。**注意：/tmp 為暫存位置，容器重啟後會消失，下一包需重建（命令見 §6）。**
- 未殺任何無關 process；無永久 daemon；未新增 OS 使用者、未改全域 Python／系統套件；未動 Docker。

## 6. 可重建命令（摘要；proxy 設定因環境而異，已省略）
```sh
D=/tmp/stp-d1-env; mkdir -m 700 $D; chown 999:999 $D          # root 建立，之後降權
R="setpriv --reuid=999 --regid=999 --clear-groups env HOME=$D"
$R python3 -m venv $D/venv
$R $D/venv/bin/pip --isolated --disable-pip-version-check install --no-input Django "psycopg[binary]"
$R /usr/lib/postgresql/16/bin/initdb -D $D/pgdata -A trust -U stp_smoke --no-sync -E UTF8 --locale=C.UTF-8
# postgresql.conf: listen_addresses=''；unix_socket_directories=$D/sock；unix_socket_permissions=0700
$R /usr/lib/postgresql/16/bin/pg_ctl -D $D/pgdata -l $D/pg.log -w start
$R $D/venv/bin/python $D/smoke.py $D/sock ok
$R /usr/lib/postgresql/16/bin/pg_ctl -D $D/pgdata -m fast -w stop
$R $D/venv/bin/python $D/smoke.py $D/sock down
```

## 7. smoke.py（合成，無 Secret）
```python
"""D1 環境煙霧測試（合成值；不含產品 migration／admin／使用者／家庭資料）。
Django 6.x postgresql backend 經私人 Unix socket 連線；驗證連線、交易 rollback 後筆數 0、commit 後筆數 1。"""
import sys
import django
from django.conf import settings

SOCK = sys.argv[1]
mode = sys.argv[2]  # "ok" | "down"
settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "postgres", "USER": "stp_smoke", "HOST": SOCK, "PORT": "", "CONN_MAX_AGE": 0,
                           "OPTIONS": {"connect_timeout": 3}}},
    USE_TZ=True, INSTALLED_APPS=[],
)
django.setup()
from django.db import connection, transaction, OperationalError

if mode == "down":
    try:
        with connection.cursor() as c:
            c.execute("select 1")
        print("NEGATIVE_FAIL: connected although server is stopped")
        sys.exit(3)
    except OperationalError as e:
        print("NEGATIVE_OK OperationalError:", str(e).strip().splitlines()[0][:160])
        sys.exit(0)

with connection.cursor() as c:
    c.execute("select current_setting('server_version'), inet_server_addr() is null")
    ver, unix_only = c.fetchone()
    print("server_version", ver, "| no_tcp_peer(unix socket):", unix_only)
    c.execute("drop table if exists stp_d1_smoke")
    c.execute("create table stp_d1_smoke (id serial primary key, is_synthetic boolean not null default true, note text not null)")
connection.commit() if not connection.get_autocommit() else None

def count():
    with connection.cursor() as c:
        c.execute("select count(*) from stp_d1_smoke")
        return c.fetchone()[0]

class Boom(Exception):
    pass

try:
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute("insert into stp_d1_smoke(note) values ('SYNTHETIC rollback probe')")
            inside = count()
        raise Boom()
except Boom:
    pass
after_rollback = count()
with transaction.atomic():
    with connection.cursor() as c:
        c.execute("insert into stp_d1_smoke(note) values ('SYNTHETIC commit probe')")
after_commit = count()
with connection.cursor() as c:
    c.execute("select bool_and(is_synthetic) from stp_d1_smoke")
    all_syn = c.fetchone()[0]
    c.execute("drop table stp_d1_smoke")
print(f"inside_tx={inside} after_rollback={after_rollback} after_commit={after_commit} all_synthetic={all_syn}")
ok = (inside, after_rollback, after_commit, all_syn) == (1, 0, 1, True)
print("POSITIVE_OK" if ok else "POSITIVE_FAIL")
sys.exit(0 if ok else 4)
```

## 8. 未驗證與限制
- Docker／Docker Compose：**未驗證、未宣稱通過**（daemon 仍不可用，本工單不改 daemon）；本結果只證明替代 runtime 可行，不是 `docker compose up` 驗收。
- 未建立 Django 專案、未跑 migration／`manage.py`、未驗證 HTMX、CI、`make spec-check`、HTTP、手機版面或任何 D1 功能。
- wheel 檔 hash 缺口（見 §2）；未做供應鏈鎖定（無 lock／requirements 檔）。
- 測試 DB 設定（trust、fsync off）僅供一次性隔離煙霧，不得沿用到任何正式或 staging 環境。
- 使用 Python 3.13.16 與 Django 6.1.2（依當時 PyPI 解析）；Django LTS 版本選擇（ARCHITECTURE §3 要求以官方支援表確認）**未查核**——本工單禁止新外部查核，列為 D1 實作前待確認項。
- 非 root 身分的選擇（`claude` uid 999）是我對「既有非 root 身分」的解讀；若 GPT 認為應使用其他身分，需在下一包明確指定。

## 9. 邊界聲明
外部呼叫：僅標準 PyPI 套件下載（工單授權）；支出 0；真實資料：無；Secret：未讀、未列印；部署／通知／merge：無；PR 維持 Draft；四份基線與其他 repo 檔案未改。AUTHOR_EVIDENCE，不自批。

---

# Repair 1（ENV-01～03）

task：STP-PLATFORM-PLAN-001-D1-ENVIRONMENT｜repair 1／1（已用 0→1）｜claim：issuecomment-6113208964（session_01MvUGYirGBtHVdHk3mYxAkh）
工單：issuecomment-6113201868 + GPT_D1_ENVIRONMENT_REPAIR_PACKET_20261012.md｜handoff：63345d354aa95d9f08f369b7c175ca4223adc451｜source：e8239a3c678432bea2492daeee71fa737e6b02ef｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
本段只追加；上方原 144 行未改。時間：2026-10-11 20:09～20:11Z（本 session 時鐘，REPORTED），遠低於 30 分鐘。層級：隔離 runtime 證據（AUTHOR_EVIDENCE）＋合成 mock 反例（**mock 不是 runtime**）。

## ENV-01～03 對照
| finding | 根因 | 修法 / 位置 | 反例與證據 |
|---|---|---|---|
| ENV-01 完整編排與失敗清理 | 只交 smoke 正文與摘要，設定僅為註解、無 trap | 下列 `orchestrate.sh`：umask 077、唯一 task 目錄 700、降權成既有 `claude`(uid 999)、sock 目錄 700、以實際命令寫入 `listen_addresses=''` 並用 `postgres -C` 讀回、`trap cleanup EXIT` 只停本任務 pgdata | 正常路（§A）與注入煙霧失敗路（§B）皆 `pg_ctl status` exit 3、pgdata／sock／log 清除、task postgres process 0 |
| ENV-02 嚴格負向 | 任何 OperationalError 都算通過 | `smokelib.classify_down`：先確認 socket 檔不存在，且錯誤須指名該 socket 並為 No such file／refused，認證／permission／其他拒絕；`check_positive` 要求 unix_only | 實際停止負向 NEGATIVE_OK（§A）；合成 mock 9 項（§C）含認證錯誤、permission、非 Unix、socket 仍存在，皆被拒絕 |
| ENV-03 artifact hash | 只記 RECORD hash | `pip download --no-deps` 固定 5 個版本到 wheelhouse，實算 SHA256／大小；`--no-index --find-links` 離線安裝並核對版本 | §D。**這是本次新增下載的 artifact hash，不能證明上一輪安裝時下載的檔案**（上輪僅有 RECORD hash） |

## 編排腳本與修正過程
`/tmp/stp-d1-scripts/orchestrate.sh`（root 啟動；之後所有 venv／DB／Django 動作皆為 uid 999）：
```bash
#!/bin/bash
# D1 隔離環境編排（root 啟動，立刻降權成既有非 root 帳號 claude/uid 999 執行所有 venv／DB／Django 動作）。
# 用法：orchestrate.sh prepare            建立 wheelhouse（固定 5 個 artifact）並離線安裝 venv
#       orchestrate.sh db ok|inject        啟動私人 socket 的 PostgreSQL，跑煙霧；inject 於煙霧中注入失敗；trap 一律清理
set -u
umask 077
D=/tmp/stp-d1-env-r1
S=/tmp/stp-d1-scripts
PGBIN=/usr/lib/postgresql/16/bin
UID_RUN=999
R="setpriv --reuid=$UID_RUN --regid=$UID_RUN --clear-groups env HOME=$D PATH=/usr/bin:/bin"
PINS="Django==6.1.2 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0"

setup_dir() {
  mkdir -p "$D" && chmod 700 "$D" && chown $UID_RUN:$UID_RUN "$D"
}

prepare() {
  setup_dir
  cp /root/.ccr/ca-bundle.crt "$D/ca.crt" && chown $UID_RUN:$UID_RUN "$D/ca.crt"      # 公開 CA；下載後刪除
  $R python3 -m venv "$D/dl-venv" || return 1
  attempt=1
  while :; do
    $R REQUESTS_CA_BUNDLE="$D/ca.crt" SSL_CERT_FILE="$D/ca.crt" CURL_CA_BUNDLE="$D/ca.crt" \
       "$D/dl-venv/bin/pip" --isolated --disable-pip-version-check download --no-input --no-deps -d "$D/wheelhouse" $PINS > "$D/download.log" 2>&1
    rc=$?; echo "pip download attempt=$attempt exit=$rc"
    [ $rc -eq 0 ] && break
    [ $attempt -ge 2 ] && { echo "DOWNLOAD_FAILED (partial)"; rm -f "$D/ca.crt"; return 1; }
    attempt=2; sleep 3
  done
  rm -f "$D/ca.crt" "$D/download.log"
  echo "--- wheelhouse (name, bytes, sha256) ---"
  ( cd "$D/wheelhouse" && for f in *; do printf '%s %s %s\n' "$f" "$(stat -c %s "$f")" "$(sha256sum "$f" | cut -c1-64)"; done )
  $R python3 -m venv "$D/venv" || return 1
  $R "$D/venv/bin/pip" --isolated --disable-pip-version-check install --no-input --no-index --find-links "$D/wheelhouse" --no-deps $PINS
  echo "offline install exit=$?"
  $R "$D/venv/bin/pip" --isolated --disable-pip-version-check freeze
  $R "$D/venv/bin/python" -c "import sys,django,psycopg;print('python',sys.version.split()[0],'django',django.get_version(),'psycopg',psycopg.__version__)"
  rm -rf "$D/dl-venv" "$D/.cache"
}

cleanup() {
  echo "--- cleanup ---"
  if [ -d "$D/pgdata" ]; then
    $R "$PGBIN/pg_ctl" -D "$D/pgdata" -m fast -w stop >/dev/null 2>&1       # 只停止本任務的 pgdata
    $R "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; echo "pg_ctl status exit=$? (3 = not running)"
  fi
  rm -rf "$D/pgdata" "$D/sock" "$D/pg.log" "$D/initdb.log"
  for p in pgdata sock pg.log; do [ -e "$D/$p" ] && echo "LEFTOVER $p" || echo "removed $p"; done
  echo "task postgres processes: $(pgrep -u $UID_RUN -f "$D/pgdata" | wc -l)"
}

db() {
  mode=$1
  setup_dir
  trap cleanup EXIT
  mkdir -m 700 "$D/sock" && chown $UID_RUN:$UID_RUN "$D/sock"
  $R "$PGBIN/initdb" -D "$D/pgdata" -A trust -U stp_smoke --no-sync -E UTF8 --locale=C.UTF-8 > "$D/initdb.log" 2>&1
  echo "initdb exit=$?"
  # 以實際命令寫入設定並讀回（不只是註解）
  $R sh -c "printf '%s\n' \"listen_addresses = ''\" \"unix_socket_directories = '$D/sock'\" 'unix_socket_permissions = 0700' 'fsync = off' >> '$D/pgdata/postgresql.conf'"
  echo "readback listen_addresses=[$($R "$PGBIN/postgres" -D "$D/pgdata" -C listen_addresses)] unix_socket_directories=[$($R "$PGBIN/postgres" -D "$D/pgdata" -C unix_socket_directories)] unix_socket_permissions=[$($R "$PGBIN/postgres" -D "$D/pgdata" -C unix_socket_permissions)]"
  echo "sock dir mode=$(stat -c %a "$D/sock") owner=$(stat -c %U "$D/sock")"
  $R "$PGBIN/pg_ctl" -D "$D/pgdata" -l "$D/pg.log" -w -t 30 start; echo "pg_ctl start exit=$?"
  echo "tcp 5432 listeners: $(ss -ltn 2>/dev/null | grep -c ':5432 ')"
  if [ "$mode" = inject ]; then
    $R "$D/venv/bin/python" "$S/smoke.py" "$D/sock" ok inject; echo "smoke(inject) exit=$?"
    return 7
  fi
  $R "$D/venv/bin/python" "$S/smoke.py" "$D/sock" ok; rc_pos=$?; echo "positive exit=$rc_pos"
  $R "$PGBIN/pg_ctl" -D "$D/pgdata" -m fast -w stop; echo "pg_ctl stop exit=$?"
  $R "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; echo "pg_ctl status exit=$? (3 = not running)"
  ls -a "$D/sock" | tr '\n' ' '; echo "<- sock dir contents after stop"
  $R "$D/venv/bin/python" "$S/smoke.py" "$D/sock" down; echo "negative(down) exit=$?"
  return $rc_pos
}

case "${1:-}" in
  prepare) prepare ;;
  db) db "${2:-ok}" ;;
  *) echo "usage: $0 prepare|db ok|inject"; exit 2 ;;
esac
```
`smokelib.py`：
```python
"""D1 煙霧測試的嚴格判斷（純函式，可用合成 mock 測試；不連資料庫）。"""
import os

EXPECTED_POSITIVE = (1, 0, 1, True)


def classify_down(sock_dir, exc_message):
    """伺服器停止後的負向：只接受「指定 socket 不存在／連線不可用」。回傳 (通過?, 原因)。"""
    sock_file = os.path.join(sock_dir, ".s.PGSQL.5432")
    if os.path.exists(sock_file):
        return False, "socket file still exists (server not stopped)"
    msg = exc_message or ""
    if sock_file not in msg:
        return False, "error does not name the expected socket path"
    low = msg.lower()
    if "password authentication" in low or "permission denied" in low or "authentication failed" in low:
        return False, "authentication/permission error is not connection-unavailable"
    if "no such file or directory" in low or "connection refused" in low:
        return True, "connection unavailable on expected socket"
    return False, "unrecognized error reason"


def check_positive(counts, unix_only, all_synthetic):
    """正向：(交易內, rollback 後, commit 後) == (1, 0, 1)、全合成、且為 Unix socket 連線。"""
    got = (counts[0], counts[1], counts[2], all_synthetic)
    if not unix_only:
        return False, "connection is not a unix-socket-only peer (inet_server_addr not null)"
    if got != EXPECTED_POSITIVE:
        return False, f"unexpected counts {got}"
    return True, "ok"
```
`smoke.py`：
```python
"""Django → psycopg → PostgreSQL 的合成煙霧（無產品 migration／使用者／家庭資料）。
用法：smoke.py <sock_dir> ok|down [inject]；inject=煙霧中途注入失敗（exit 7），用來驗證外層 cleanup。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smokelib
import django
from django.conf import settings

SOCK, mode = sys.argv[1], sys.argv[2]
inject = len(sys.argv) > 3 and sys.argv[3] == "inject"
settings.configure(DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "postgres", "USER": "stp_smoke", "HOST": SOCK,
                                           "PORT": "", "CONN_MAX_AGE": 0, "OPTIONS": {"connect_timeout": 3}}}, USE_TZ=True, INSTALLED_APPS=[])
django.setup()
from django.db import connection, transaction, OperationalError

if mode == "down":
    try:
        with connection.cursor() as c:
            c.execute("select 1")
        print("NEGATIVE_FAIL: connected although server is stopped"); sys.exit(3)
    except OperationalError as e:
        ok, why = smokelib.classify_down(SOCK, str(e))
        print(("NEGATIVE_OK" if ok else "NEGATIVE_REJECTED"), why, "|", str(e).strip().splitlines()[0][:150])
        sys.exit(0 if ok else 5)

with connection.cursor() as c:
    c.execute("select current_setting('server_version'), inet_server_addr() is null")
    ver, unix_only = c.fetchone()
    print("server_version", ver, "| unix_only:", unix_only)
    c.execute("drop table if exists stp_d1_smoke")
    c.execute("create table stp_d1_smoke (id serial primary key, is_synthetic boolean not null default true, note text not null)")
if inject:
    print("INJECTED_FAILURE after table creation"); sys.exit(7)

def count():
    with connection.cursor() as c:
        c.execute("select count(*) from stp_d1_smoke"); return c.fetchone()[0]

class Boom(Exception):
    pass

try:
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute("insert into stp_d1_smoke(note) values ('SYNTHETIC rollback probe')")
        inside = count()
        raise Boom()
except Boom:
    pass
after_rollback = count()
with transaction.atomic():
    with connection.cursor() as c:
        c.execute("insert into stp_d1_smoke(note) values ('SYNTHETIC commit probe')")
after_commit = count()
with connection.cursor() as c:
    c.execute("select bool_and(is_synthetic) from stp_d1_smoke"); all_syn = c.fetchone()[0]
    c.execute("drop table stp_d1_smoke")
ok, why = smokelib.check_positive((inside, after_rollback, after_commit), unix_only, all_syn)
print(f"inside_tx={inside} after_rollback={after_rollback} after_commit={after_commit} all_synthetic={all_syn} -> {'POSITIVE_OK' if ok else 'POSITIVE_REJECTED ' + why}")
sys.exit(0 if ok else 4)
```
`negtests.py`（合成 mock，不連 DB）：
```python
"""合成 mock 反例（不是 runtime、不連資料庫）：嚴格判斷必須拒絕認證錯誤、permission 錯誤、非 Unix 連線。"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smokelib
sock = tempfile.mkdtemp(prefix="stp-mock-")
sf = os.path.join(sock, ".s.PGSQL.5432")
cases = [
  ("down: expected socket missing", smokelib.classify_down(sock, f'connection to server on socket "{sf}" failed: No such file or directory'), True),
  ("down: password authentication failed", smokelib.classify_down(sock, 'password authentication failed for user "stp_smoke"'), False),
  ("down: permission denied on expected socket", smokelib.classify_down(sock, f'connection to server on socket "{sf}" failed: Permission denied'), False),
  ("down: auth failure naming the expected socket", smokelib.classify_down(sock, f'connection to server on socket "{sf}" failed: FATAL:  password authentication failed for user "stp_smoke"'), False),
  ("down: other socket path", smokelib.classify_down(sock, 'connection to server on socket "/var/run/other/.s.PGSQL.5432" failed: No such file or directory'), False),
  ("positive: TCP peer (unix_only False)", smokelib.check_positive((1, 0, 1), False, True), False),
  ("positive: wrong rollback count", smokelib.check_positive((1, 1, 2), True, True), False),
  ("positive: genuine", smokelib.check_positive((1, 0, 1), True, True), True),
]
open(sf, "w").close()
cases.append(("down: socket file still exists", smokelib.classify_down(sock, f'connection to server on socket "{sf}" failed: No such file or directory'), False))
bad = 0
for name, (ok, why), want in cases:
    verdict = "PASS" if ok == want else "FAIL"
    bad += ok != want
    print(f"{verdict} {name}: accepted={ok} expected_accept={want} ({why})")
os.remove(sf); os.rmdir(sock)
sys.exit(1 if bad else 0)
```
**過程中的失誤（如實列出）**：第一次 `prepare` 的 `pip download` 兩次都 exit 1（`No matching distribution found for Django==6.1.2`）。根因是我的編排把 `PATH` 繼承成 python 3.11，而 Django 6.x 需要 Python ≥3.12（索引有回應但無相容版本；沒有任何 artifact 下載、無外部副作用）；這不是網路暫時失敗，卻消耗了工單的「一次安全重試」額度。已將 `R` 固定 `PATH=/usr/bin:/bin`（python 3.13.16）後重跑，該次 `pip download attempt=1 exit=0`。若 GPT 認為此重試次數算超限，請在覆核中指出。

## §A 正常路（`orchestrate.sh db ok`，exit 0）
```
initdb exit=0
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-env-r1/sock] unix_socket_permissions=[448]
sock dir mode=700 owner=claude
waiting for server to start.... done
server started
pg_ctl start exit=0
tcp 5432 listeners: 0
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | unix_only: True
inside_tx=1 after_rollback=0 after_commit=1 all_synthetic=True -> POSITIVE_OK
positive exit=0
waiting for server to shut down.... done
server stopped
pg_ctl stop exit=0
pg_ctl status exit=3 (3 = not running)
. .. <- sock dir contents after stop
NEGATIVE_OK connection unavailable on expected socket | connection is bad: connection to server on socket "/tmp/stp-d1-env-r1/sock/.s.PGSQL.5432" failed: No such file or directory
negative(down) exit=0
--- cleanup ---
pg_ctl status exit=3 (3 = not running)
removed pgdata
removed sock
removed pg.log
task postgres processes: 0
script exit=0
```
備註：`unix_socket_permissions=[448]` 為 `0700` 的十進位顯示；停止後 sock 目錄為空；負向的錯誤指名指定 socket 且原因為 No such file or directory。

## §B 注入失敗路（`orchestrate.sh db inject`，煙霧 exit 7，腳本 exit 7，cleanup 仍完成）
```
initdb exit=0
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-env-r1/sock] unix_socket_permissions=[448]
sock dir mode=700 owner=claude
waiting for server to start.... done
server started
pg_ctl start exit=0
tcp 5432 listeners: 0
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | unix_only: True
INJECTED_FAILURE after table creation
smoke(inject) exit=7
--- cleanup ---
pg_ctl status exit=3 (3 = not running)
removed pgdata
removed sock
removed pg.log
task postgres processes: 0
script exit=7
```

## §C 合成 mock 反例（`negtests.py`，exit 0；mock 非 runtime）
```
PASS down: expected socket missing: accepted=True expected_accept=True (connection unavailable on expected socket)
PASS down: password authentication failed: accepted=False expected_accept=False (error does not name the expected socket path)
PASS down: permission denied on expected socket: accepted=False expected_accept=False (authentication/permission error is not connection-unavailable)
PASS down: auth failure naming the expected socket: accepted=False expected_accept=False (authentication/permission error is not connection-unavailable)
PASS down: other socket path: accepted=False expected_accept=False (error does not name the expected socket path)
PASS positive: TCP peer (unix_only False): accepted=False expected_accept=False (connection is not a unix-socket-only peer (inet_server_addr not null))
PASS positive: wrong rollback count: accepted=False expected_accept=False (unexpected counts (1, 1, 2, True))
PASS positive: genuine: accepted=True expected_accept=True (ok)
PASS down: socket file still exists: accepted=False expected_accept=False (socket file still exists (server not stopped))
negtests exit=0
```

## §D 新下載 wheelhouse（名稱、大小 bytes、SHA256）與離線安裝
來源：標準 PyPI（經平台 proxy，`pip --isolated`，未改鏡像、未讀 pip 設定、未保留 CA 複本／下載 log）。固定版本：Django==6.1.2 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0；`pip download attempt=1 exit=0`（此為成功的那次；失敗過程見上）。
```
asgiref-3.12.1-py3-none-any.whl 25478 fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094
django-6.1.2-py3-none-any.whl 8420684 141efee6ec64d1db6db90683bf734c550102450f444fb099063b0be1bd27d991
psycopg-3.3.6-py3-none-any.whl 215490 a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631
psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl 5237855 cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269
sqlparse-0.6.0-py3-none-any.whl 50070 b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f
```
離線安裝（`pip --isolated install --no-index --find-links <wheelhouse> --no-deps <5 pins>`）exit 0，`pip freeze`：asgiref==3.12.1、Django==6.1.2、psycopg==3.3.6、psycopg-binary==3.3.6、sqlparse==0.6.0；`python 3.13.16 django 6.1.2 psycopg 3.3.6`，與清單一致。
保留位置：`/tmp/stp-d1-env-r1/{venv,wheelhouse}`，合計約 99 MB（/ 磁碟可用約 30 GB）；/tmp 為暫存，容器重啟後消失，重建用 `orchestrate.sh prepare`。已刪：CA 複本、下載 log、dl-venv、pip 快取、pgdata／sock／log。repo 未新增二進位、lock 或產品檔。

## §E repo 必要檢查（於本段所在的 commit 前的樹；皆 exit 0，stderr 空）
```
python3 docs/platform/examples/check_examples.py | exit=0 | OK: 1306 checks passed | stderr=0
python3 docs/platform/tools/gen_state_machines.py --check | exit=0 | OK: 6 state machines, 86 transitions, doc in sync | stderr=0
python3 docs/platform/tools/gen_permissions.py --check | exit=0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | stderr=0
python3 docs/platform/tools/test_checks.py | exit=0 | OK: test_checks 136 counterexample checks passed | stderr=0
python3 docs/platform/tools/check_docs.py | exit=0 | OK: 2089 doc checks passed | stderr=0
```
四份原始基線 `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` 為空；本 commit 只在本檔後追加（原 144 行逐位元不變，見交付留言的 SHA256 核對）。

## 未證明／剩餘缺口
- Docker／Compose 仍未驗證；未建 Django 專案、migration、HTTP；Django LTS 版本選擇未查核（本包明確不含）。
- 上輪實際安裝的 artifact hash 無法追回（見 ENV-03 說明）。
- 測試 DB 為 trust 認證、fsync off，僅此一次性隔離，不得沿用。
- 非 root 身分選用既有 `claude`(uid 999)為我的解讀；mock 測試為純函式判斷，不能取代 runtime 的認證／permission 實際行為。
- 一次不必要的下載重試額度（見上）。
- 外部呼叫：僅 PyPI 固定 5 artifact（成功 1 次；另有 2 次索引解析失敗、無 artifact 下載）；支出 0；真實資料無；Secret 未讀；部署／merge 無。AUTHOR_EVIDENCE，不自批。

---

# Repair 2（ENV-01 fail-closed）

task：STP-PLATFORM-PLAN-001-D1-ENVIRONMENT｜repair 2／2（limit 1→2，已用 1→2）｜claim：issuecomment-6113749014（session_01MvUGYirGBtHVdHk3mYxAkh）
工單：issuecomment-6113738544 + GPT_D1_ENVIRONMENT_REPAIR2_PACKET_20261012.md｜handoff：f1b930fa75828fe667c98356a3c70570d8788d3f｜source：867ba5eccd3b1cc13542d22c471ee7413dee89fc｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
本段只追加；上方原 466 行未改。時間：2026-10-11 21:06～21:08Z（本 session 時鐘，REPORTED），遠低於 20 分鐘。**本段沒有任何外部下載或外部呼叫**（只用既存 task venv／wheelhouse／PG16）。層級：隔離 runtime（正常路與注入路）＋合成 stub 控制流程反例（**stub 不是 runtime**）。

## 偏差說明（承接 GPT 裁定）
repair1 的下載（2 次索引解析失敗＋第 3 次成功）超出原包「一次下載＋一次暫時網路安全重試」，已被 GPT 記為偏差；本輪不追認其合規、不重置 attempt、不再下載。程序改正：`verify` 的 preflight（Python 版本、既存 wheelhouse 與清單）不通過就停止，且完全不做下載。

## ENV-01 對照（根因 → 修改 → 反例 → 命令 → 結果 → 缺口）
- 根因（GPT 重現）：v1 編排只有 `set -u`，關鍵命令只印 exit 不阻斷；負向失敗被忽略（`down` exit 5 但整體 exit 0）；cleanup 不驗證停止就 `rm`（stop 1／status 0 仍刪資料）。
- 修改：新編排 `orchestrate_v2.sh`（v1 保留為 `orchestrate_v1.sh` 歷史，不再使用）：
  - `run_expect NAME WANT_RC cmd…`：每個關鍵步驟依 exit 判定，失敗記 `FAIL` 並中止後續步驟，不用最後的 cleanup 覆蓋；
  - 設定寫入後以 `postgres -C` 讀回 `listen_addresses`／`unix_socket_directories`／`unix_socket_permissions`，不符即失敗；
  - 正向、停止、`status`（必須 3）、`down` 負向都依預期值裁定；
  - `cleanup`：先 `status`；非 3 才停止（stop#1，必要時 stop#2 `-m immediate`，僅限本 task 的 pgdata，各最多一次），再核對 status 3 與 task postgres 程序為 0；**只有確定已停止才 `rm`**，否則 `CLEANUP_FAILED`、資料保留、結束碼 9（BLOCKED_CAPABILITY／partial）；
  - 結束碼：0 全成功；1 某步驟失敗；7 注入模式且一切符合預期；9 cleanup 失敗（優先於其他碼，不被掩蓋）。
- 不重寫 ENV-02 純函式（`smokelib.py`／`negtests.py`／`smoke.py` 沿用 repair1 §C，不變）與 ENV-03 清單（沿用 repair1 §D，不重下載）。

## 腳本：`orchestrate_v2.sh`
```bash
#!/bin/bash
# D1 隔離環境編排 v2（fail-closed）。不下載任何東西：只使用既存 task venv／wheelhouse／PG16。
# 用法：orchestrate_v2.sh verify            preflight＋離線安裝＋版本核對（不下載）
#       orchestrate_v2.sh db ok|inject      私人 socket PG16 煙霧；每步依 exit／預期值裁定；cleanup 失敗不刪資料
# 結束碼：0 全部成功；1 某步驟失敗（或預期值不符）；7 注入模式且一切符合預期（煙霧注入失敗 exit 7、cleanup 正常）；9 cleanup 失敗（資料保留）
set -u
umask 077
D=${STP_D:-/tmp/stp-d1-env-r1}
S=${STP_S:-/tmp/stp-d1-scripts}
PGBIN=${STP_PGBIN:-/usr/lib/postgresql/16/bin}
if [ -n "${STP_RUN_STUB:-}" ]; then                       # 合成 stub 測試用：不降權、不碰真實 PG
  RUN=(env HOME="$D" PATH="$PATH")
  CHOWN=:
else
  RUN=(setpriv --reuid=999 --regid=999 --clear-groups env HOME="$D" PATH=/usr/bin:/bin)
  CHOWN="chown 999:999"
fi
VENVPY="$D/venv/bin/python"
PIP="$D/venv/bin/pip"
PINS="Django==6.1.2 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0"
EXPECT_FREEZE=$'Django==6.1.2\nasgiref==3.12.1\npsycopg-binary==3.3.6\npsycopg==3.3.6\nsqlparse==0.6.0'

FAIL=""          # 第一個失敗原因
MAIN_RC=0
CLEAN_FAIL=0

note_fail() { [ -z "$FAIL" ] && FAIL="$1"; echo "FAIL: $1"; }

# run_expect <name> <expected_rc> <cmd...>：失敗時記錄並回傳 1，不吞錯
run_expect() {
  local name=$1 want=$2; shift 2
  "$@"; local rc=$?
  echo "$name exit=$rc (expected $want)"
  [ $rc -eq "$want" ] || { note_fail "$name exit=$rc expected=$want"; return 1; }
  return 0
}

verify_body() {
  # preflight：固定 Python／既存 artifact／清單，不通過就不往下（且不下載）
  local pyv; pyv=$("${RUN[@]}" "$VENVPY" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null); local rc=$?
  echo "preflight venv python=[$pyv] exit=$rc (need >= 3.12)"
  [ $rc -eq 0 ] || { note_fail "preflight python exit=$rc"; return 1; }
  case "$pyv" in 3.1[2-9]|3.[2-9][0-9]) ;; *) note_fail "preflight python too old: $pyv"; return 1;; esac
  [ -d "$D/wheelhouse" ] || { note_fail "preflight wheelhouse missing"; return 1; }
  if [ -f "$S/wheelhouse.sha256" ]; then
    ( cd "$D/wheelhouse" && sha256sum -c "$S/wheelhouse.sha256" ); rc=$?
    echo "wheelhouse sha256 -c exit=$rc"; [ $rc -eq 0 ] || { note_fail "wheelhouse sha256 mismatch exit=$rc"; return 1; }
  else
    note_fail "preflight wheelhouse.sha256 missing"; return 1
  fi
  run_expect offline_install 0 "${RUN[@]}" "$PIP" --isolated --disable-pip-version-check install --no-input --no-index --find-links "$D/wheelhouse" --no-deps --force-reinstall $PINS > "$D/offline_install.log" 2>&1 || return 1
  local fz; fz=$("${RUN[@]}" "$PIP" --isolated --disable-pip-version-check freeze 2>/dev/null | sort); rc=$?
  echo "pip freeze exit=$rc"; echo "$fz"
  [ $rc -eq 0 ] || { note_fail "pip freeze exit=$rc"; return 1; }
  [ "$fz" = "$(printf '%s\n' "$EXPECT_FREEZE" | sort)" ] || { note_fail "installed versions differ from pinned list"; return 1; }
  local ver; ver=$("${RUN[@]}" "$VENVPY" -c 'import django,psycopg;print(django.get_version(), psycopg.__version__)' 2>&1); rc=$?
  echo "import check exit=$rc [$ver]"
  [ $rc -eq 0 ] && [ "$ver" = "6.1.2 3.3.6" ] || { note_fail "import/version check failed: $ver"; return 1; }
  return 0
}

db_body() {
  local mode=$1
  [ -d "$D" ] || { mkdir -p "$D" && chmod 700 "$D" && $CHOWN "$D"; } || { note_fail "task dir"; return 1; }
  run_expect mkdir_sock 0 mkdir -m 700 "$D/sock" || return 1
  $CHOWN "$D/sock"
  "${RUN[@]}" "$PGBIN/initdb" -D "$D/pgdata" -A trust -U stp_smoke --no-sync -E UTF8 --locale=C.UTF-8 > "$D/initdb.log" 2>&1; local rc=$?
  echo "initdb exit=$rc (expected 0)"; [ $rc -eq 0 ] || { note_fail "initdb exit=$rc"; return 1; }
  "${RUN[@]}" sh -c 'printf "%s\n" "listen_addresses = '"''"'" "unix_socket_directories = '"'"'$1/sock'"'"'" "unix_socket_permissions = 0700" "fsync = off" >> "$1/pgdata/postgresql.conf"' _ "$D"; rc=$?
  echo "config write exit=$rc (expected 0)"; [ $rc -eq 0 ] || { note_fail "config write exit=$rc"; return 1; }
  local la sd sp
  la=$("${RUN[@]}" "$PGBIN/postgres" -D "$D/pgdata" -C listen_addresses 2>&1); rc=$?; [ $rc -eq 0 ] || { note_fail "readback listen_addresses exit=$rc"; return 1; }
  sd=$("${RUN[@]}" "$PGBIN/postgres" -D "$D/pgdata" -C unix_socket_directories 2>&1); rc=$?; [ $rc -eq 0 ] || { note_fail "readback unix_socket_directories exit=$rc"; return 1; }
  sp=$("${RUN[@]}" "$PGBIN/postgres" -D "$D/pgdata" -C unix_socket_permissions 2>&1); rc=$?; [ $rc -eq 0 ] || { note_fail "readback unix_socket_permissions exit=$rc"; return 1; }
  echo "readback listen_addresses=[$la] unix_socket_directories=[$sd] unix_socket_permissions=[$sp] (expected [] [$D/sock] [448])"
  [ -z "$la" ] && [ "$sd" = "$D/sock" ] && [ "$sp" = "448" ] || { note_fail "config readback mismatch"; return 1; }
  [ "$(stat -c %a "$D/sock")" = "700" ] || { note_fail "sock dir mode not 700"; return 1; }
  run_expect pg_start 0 "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" -l "$D/pg.log" -w -t 30 start || return 1
  local tcp; tcp=$(ss -ltn 2>/dev/null | grep -c ':5432 ')
  echo "tcp 5432 listeners: $tcp (expected 0)"; [ "$tcp" = "0" ] || { note_fail "unexpected TCP 5432 listener"; return 1; }
  if [ "$mode" = inject ]; then
    run_expect smoke_inject 7 "${RUN[@]}" "$VENVPY" "$S/smoke.py" "$D/sock" ok inject || return 1
    MAIN_RC=7
    return 0
  fi
  run_expect smoke_positive 0 "${RUN[@]}" "$VENVPY" "$S/smoke.py" "$D/sock" ok || return 1
  run_expect pg_stop 0 "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" -m fast -w stop || return 1
  run_expect pg_status_after_stop 3 "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1 || return 1
  run_expect smoke_negative_down 0 "${RUN[@]}" "$VENVPY" "$S/smoke.py" "$D/sock" down || return 1
  return 0
}

cleanup() {
  echo "--- cleanup ---"
  if [ -d "$D/pgdata" ]; then
    "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; local st=$?
    echo "cleanup status exit=$st (3 = not running)"
    if [ $st -ne 3 ]; then
      "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" -m fast -w stop >/dev/null 2>&1; echo "cleanup stop#1 exit=$?"
      "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; st=$?; echo "cleanup status exit=$st"
      if [ $st -ne 3 ]; then
        "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" -m immediate -w stop >/dev/null 2>&1; echo "cleanup stop#2 (task pgdata only) exit=$?"
        "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; st=$?; echo "cleanup status exit=$st"
      fi
    fi
    local procs; procs=$(pgrep -f "^$PGBIN/postgres -D $D/pgdata" | wc -l)
    echo "task postgres processes: $procs"
    if [ $st -ne 3 ] || [ "$procs" != "0" ]; then
      CLEAN_FAIL=1
      echo "CLEANUP_FAILED: server not confirmed stopped; data RETAINED at $D (BLOCKED_CAPABILITY/partial)"
      return
    fi
  fi
  rm -rf "$D/pgdata" "$D/sock" "$D/pg.log" "$D/initdb.log"
  for p in pgdata sock pg.log initdb.log; do
    if [ -e "$D/$p" ]; then echo "LEFTOVER $p"; CLEAN_FAIL=1; else echo "removed $p"; fi
  done
}

finish() {
  local final
  if [ "$CLEAN_FAIL" = 1 ]; then final=9
  elif [ -n "$FAIL" ]; then final=1
  else final=$MAIN_RC; fi
  echo "RESULT: first_failure=[${FAIL:-none}] cleanup_failed=$CLEAN_FAIL final_exit=$final"
  exit $final
}

case "${1:-}" in
  verify) trap 'finish' EXIT; verify_body ;;
  db) trap 'cleanup; finish' EXIT; db_body "${2:-ok}" ;;
  *) echo "usage: $0 verify|db ok|inject"; exit 2 ;;
esac
```
`wheelhouse.sha256`（與 repair1 §D 記錄的 hash 相同）：
```
fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094  asgiref-3.12.1-py3-none-any.whl
141efee6ec64d1db6db90683bf734c550102450f444fb099063b0be1bd27d991  django-6.1.2-py3-none-any.whl
a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631  psycopg-3.3.6-py3-none-any.whl
cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269  psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f  sqlparse-0.6.0-py3-none-any.whl
```

## §A 實際 PG16 runtime — 正常路與注入路（獨立於 stub）
`verify`（不下載；離線重裝並核對版本）：
```
preflight venv python=[3.13] exit=0 (need >= 3.12)
asgiref-3.12.1-py3-none-any.whl: OK
django-6.1.2-py3-none-any.whl: OK
psycopg-3.3.6-py3-none-any.whl: OK
psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl: OK
sqlparse-0.6.0-py3-none-any.whl: OK
wheelhouse sha256 -c exit=0
pip freeze exit=0
Django==6.1.2
asgiref==3.12.1
psycopg-binary==3.3.6
psycopg==3.3.6
sqlparse==0.6.0
import check exit=0 [6.1.2 3.3.6]
RESULT: first_failure=[none] cleanup_failed=0 final_exit=0
script exit=0
```
`db ok`：
```
mkdir_sock exit=0 (expected 0)
initdb exit=0 (expected 0)
config write exit=0 (expected 0)
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-env-r1/sock] unix_socket_permissions=[448] (expected [] [/tmp/stp-d1-env-r1/sock] [448])
waiting for server to start.... done
server started
pg_start exit=0 (expected 0)
tcp 5432 listeners: 0 (expected 0)
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | unix_only: True
inside_tx=1 after_rollback=0 after_commit=1 all_synthetic=True -> POSITIVE_OK
smoke_positive exit=0 (expected 0)
waiting for server to shut down.... done
server stopped
pg_stop exit=0 (expected 0)
NEGATIVE_OK connection unavailable on expected socket | connection is bad: connection to server on socket "/tmp/stp-d1-env-r1/sock/.s.PGSQL.5432" failed: No such file or directory
smoke_negative_down exit=0 (expected 0)
--- cleanup ---
cleanup status exit=3 (3 = not running)
task postgres processes: 0
removed pgdata
removed sock
removed pg.log
removed initdb.log
RESULT: first_failure=[none] cleanup_failed=0 final_exit=0
script exit=0
```
`db inject`（煙霧中注入失敗 exit 7；cleanup 仍完成；腳本 exit 7 為預期）：
```
mkdir_sock exit=0 (expected 0)
initdb exit=0 (expected 0)
config write exit=0 (expected 0)
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-env-r1/sock] unix_socket_permissions=[448] (expected [] [/tmp/stp-d1-env-r1/sock] [448])
waiting for server to start.... done
server started
pg_start exit=0 (expected 0)
tcp 5432 listeners: 0 (expected 0)
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | unix_only: True
INJECTED_FAILURE after table creation
smoke_inject exit=7 (expected 7)
--- cleanup ---
cleanup status exit=0 (3 = not running)
cleanup stop#1 exit=0
cleanup status exit=3
task postgres processes: 0
removed pgdata
removed sock
removed pg.log
removed initdb.log
RESULT: first_failure=[none] cleanup_failed=0 final_exit=7
script exit=7
```

## §B 合成 stub 控制流程反例（`stubtests.sh`；stub 明標合成，不連 DB）
覆蓋工單要求的：down5、stop1/status0（不得刪）、initdb1、config 寫入失敗、讀回不符、start1、離線安裝 1、版本不符，另加 wheel hash 被改、Python 過舊、煙霧失敗、注入退出碼錯誤、注入路 cleanup 失敗。每項為 expected／actual／原因比對。
```
PASS genuine_db_ok                      expected_exit=0  actual_exit=0  reason_match=[final_exit=0] pgdata_retained(expected/actual)=no/no
PASS genuine_db_inject                  expected_exit=7  actual_exit=7  reason_match=[final_exit=7] pgdata_retained(expected/actual)=no/no
PASS down_exit5                         expected_exit=1  actual_exit=1  reason_match=[smoke_negative_down exit=5] pgdata_retained(expected/actual)=no/no
PASS stop1_status0_no_delete            expected_exit=9  actual_exit=9  reason_match=[CLEANUP_FAILED] pgdata_retained(expected/actual)=yes/yes
PASS initdb1                            expected_exit=1  actual_exit=1  reason_match=[initdb exit=1] pgdata_retained(expected/actual)=no/no
PASS config_write_fail                  expected_exit=1  actual_exit=1  reason_match=[config write exit=] pgdata_retained(expected/actual)=no/no
PASS config_readback_mismatch           expected_exit=1  actual_exit=1  reason_match=[config readback mismatch] pgdata_retained(expected/actual)=no/no
PASS start1                             expected_exit=1  actual_exit=1  reason_match=[pg_start exit=1] pgdata_retained(expected/actual)=no/no
PASS positive_smoke_fails               expected_exit=1  actual_exit=1  reason_match=[smoke_positive exit=4] pgdata_retained(expected/actual)=no/no
PASS inject_wrong_exit                  expected_exit=1  actual_exit=1  reason_match=[smoke_inject exit=0] pgdata_retained(expected/actual)=no/no
PASS inject_cleanup_fails               expected_exit=9  actual_exit=9  reason_match=[CLEANUP_FAILED] pgdata_retained(expected/actual)=yes/yes
PASS verify_genuine                     expected_exit=0  actual_exit=0  reason_match=[final_exit=0] pgdata_retained(expected/actual)=na/no
PASS verify_offline_install1            expected_exit=1  actual_exit=1  reason_match=[offline_install exit=1] pgdata_retained(expected/actual)=na/no
PASS verify_version_mismatch            expected_exit=1  actual_exit=1  reason_match=[installed versions differ] pgdata_retained(expected/actual)=na/no
PASS verify_import_mismatch             expected_exit=1  actual_exit=1  reason_match=[import/version check failed] pgdata_retained(expected/actual)=na/no
PASS verify_python_too_old              expected_exit=1  actual_exit=1  reason_match=[preflight python too old] pgdata_retained(expected/actual)=na/no
PASS verify_wheel_hash_tamper           expected_exit=1  actual_exit=1  reason_match=[wheelhouse sha256 mismatch]
stubtests overall: ALL_PASS
```
`stubtests.sh` 原文：
```bash
#!/bin/bash
# 合成 stub 控制流程反例（不連 DB、不降權、不碰真實 PG；stub 明標合成，不是 runtime）。
# 每個情境：以 STP_RUN_STUB=1 執行真正的 orchestrate_v2.sh，stub 的 PG／python／pip 依 FAKE_* 回傳指定 exit，核對 expected/actual。
set -u
S=/tmp/stp-d1-scripts
T=$(mktemp -d /tmp/stp-stub-XXXXXX)
mk_fixture() {            # $1 = fixture dir
  local F=$1; rm -rf "$F"; mkdir -p "$F/D/venv/bin" "$F/D/wheelhouse" "$F/S" "$F/pgbin"
  echo synthetic > "$F/D/wheelhouse/pkg-1.0-py3-none-any.whl"
  ( cd "$F/D/wheelhouse" && sha256sum pkg-1.0-py3-none-any.whl ) > "$F/S/wheelhouse.sha256"
  cat > "$F/pgbin/pg_ctl" <<'X'
#!/bin/bash
ST="$STP_D/.state"; cmd=""
for a in "$@"; do case $a in start|stop|status) cmd=$a;; esac; done
case $cmd in
  start) [ "${FAKE_START_RC:-0}" = 0 ] && touch "$ST"; exit ${FAKE_START_RC:-0};;
  stop) [ "${FAKE_STOP_RC:-0}" = 0 ] && rm -f "$ST"; exit ${FAKE_STOP_RC:-0};;
  status) [ -n "${FAKE_STATUS_FIXED:-}" ] && exit $FAKE_STATUS_FIXED; [ -f "$ST" ] && exit 0 || exit 3;;
esac
X
  cat > "$F/pgbin/initdb" <<'X'
#!/bin/bash
while [ $# -gt 0 ]; do [ "$1" = -D ] && dir=$2; shift; done
rc=${FAKE_INITDB_RC:-0}
if [ $rc -eq 0 ]; then mkdir -p "$dir"; if [ -n "${FAKE_CONF_DIR:-}" ]; then mkdir -p "$dir/postgresql.conf"; else : > "$dir/postgresql.conf"; fi; fi
exit $rc
X
  cat > "$F/pgbin/postgres" <<'X'
#!/bin/bash
case "$4" in
  listen_addresses) echo "${FAKE_LISTEN:-}";;
  unix_socket_directories) echo "$STP_D/sock";;
  unix_socket_permissions) echo 448;;
esac
X
  cat > "$F/D/venv/bin/python" <<'X'
#!/bin/bash
if [ "$1" = -c ]; then
  case "$2" in *version_info*) echo "${FAKE_PYV:-3.13}";; *django*) echo "${FAKE_IMPORT:-6.1.2 3.3.6}";; esac; exit 0
fi
mode=$3; inj=${4:-}
[ "$mode" = down ] && exit ${FAKE_DOWN_RC:-0}
[ "$inj" = inject ] && exit ${FAKE_INJECT_RC:-7}
exit ${FAKE_POS_RC:-0}
X
  cat > "$F/D/venv/bin/pip" <<'X'
#!/bin/bash
for a in "$@"; do case $a in install) exit ${FAKE_PIP_RC:-0};; freeze) printf '%s\n' ${FAKE_FREEZE:-Django==6.1.2 asgiref==3.12.1 psycopg-binary==3.3.6 psycopg==3.3.6 sqlparse==0.6.0}; exit 0;; esac; done
X
  chmod 755 "$F"/pgbin/* "$F"/D/venv/bin/*
}
bad=0
# scenario <name> <subcommand...> -- <expected_exit> <expected_reason_substring> <expect_pgdata_retained:yes|no|na> [VAR=VAL ...]
scenario() {
  local name=$1; shift
  local sub=(); while [ "$1" != -- ]; do sub+=("$1"); shift; done; shift
  local want=$1 reason=$2 retained=$3; shift 3
  local F="$T/$name"; mk_fixture "$F"
  local out; out=$(env STP_RUN_STUB=1 STP_D="$F/D" STP_S="$F/S" STP_PGBIN="$F/pgbin" "$@" bash "$S/orchestrate_v2.sh" "${sub[@]}" 2>&1); local rc=$?
  local ok=1
  [ $rc -eq "$want" ] || ok=0
  echo "$out" | grep -q -- "$reason" || ok=0
  local kept=no; [ -d "$F/D/pgdata" ] && kept=yes
  { [ "$retained" = na ] || [ "$retained" = "$kept" ]; } || ok=0
  [ $ok -eq 1 ] && v=PASS || { v=FAIL; bad=1; }
  printf '%s %-34s expected_exit=%-2s actual_exit=%-2s reason_match=[%s] pgdata_retained(expected/actual)=%s/%s\n' "$v" "$name" "$want" "$rc" "$reason" "$retained" "$kept"
}
scenario genuine_db_ok            db ok       -- 0 "final_exit=0" no
scenario genuine_db_inject        db inject   -- 7 "final_exit=7" no
scenario down_exit5               db ok       -- 1 "smoke_negative_down exit=5" no   FAKE_DOWN_RC=5
scenario stop1_status0_no_delete  db ok       -- 9 "CLEANUP_FAILED" yes               FAKE_STOP_RC=1 FAKE_STATUS_FIXED=0
scenario initdb1                  db ok       -- 1 "initdb exit=1" no                 FAKE_INITDB_RC=1
scenario config_write_fail        db ok       -- 1 "config write exit=" no            FAKE_CONF_DIR=1
scenario config_readback_mismatch db ok       -- 1 "config readback mismatch" no      FAKE_LISTEN="*"
scenario start1                   db ok       -- 1 "pg_start exit=1" no               FAKE_START_RC=1
scenario positive_smoke_fails     db ok       -- 1 "smoke_positive exit=4" no         FAKE_POS_RC=4
scenario inject_wrong_exit        db inject   -- 1 "smoke_inject exit=0" no            FAKE_INJECT_RC=0
scenario inject_cleanup_fails     db inject   -- 9 "CLEANUP_FAILED" yes               FAKE_STOP_RC=1 FAKE_STATUS_FIXED=0
scenario verify_genuine           verify      -- 0 "final_exit=0" na
scenario verify_offline_install1  verify      -- 1 "offline_install exit=1" na        FAKE_PIP_RC=1
scenario verify_version_mismatch  verify      -- 1 "installed versions differ" na     FAKE_FREEZE="Django==6.0.1 asgiref==3.12.1 psycopg-binary==3.3.6 psycopg==3.3.6 sqlparse==0.6.0"
scenario verify_import_mismatch   verify      -- 1 "import/version check failed" na   FAKE_IMPORT="6.0.1 3.3.6"
scenario verify_python_too_old    verify      -- 1 "preflight python too old" na      FAKE_PYV=3.11
# wheelhouse hash 被改動：fixture 後手動竄改
F="$T/verify_hash_tamper"; mk_fixture "$F"; echo tampered > "$F/D/wheelhouse/pkg-1.0-py3-none-any.whl"
out=$(env STP_RUN_STUB=1 STP_D="$F/D" STP_S="$F/S" STP_PGBIN="$F/pgbin" bash "$S/orchestrate_v2.sh" verify 2>&1); rc=$?
if [ $rc -eq 1 ] && echo "$out" | grep -q "wheelhouse sha256 mismatch"; then v=PASS; else v=FAIL; bad=1; fi
printf '%s %-34s expected_exit=1  actual_exit=%-2s reason_match=[wheelhouse sha256 mismatch]\n' "$v" verify_wheel_hash_tamper "$rc"
rm -rf "$T"
echo "stubtests overall: $([ $bad -eq 0 ] && echo ALL_PASS || echo SOME_FAIL)"
exit $bad
```

## §C repo 必要檢查（於追加本段前的樹；皆 exit 0，stderr 空）
```
python3 docs/platform/examples/check_examples.py | exit=0 | OK: 1306 checks passed | stderr=0
python3 docs/platform/tools/gen_state_machines.py --check | exit=0 | OK: 6 state machines, 86 transitions, doc in sync | stderr=0
python3 docs/platform/tools/gen_permissions.py --check | exit=0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | stderr=0
python3 docs/platform/tools/test_checks.py | exit=0 | OK: test_checks 136 counterexample checks passed | stderr=0
python3 docs/platform/tools/check_docs.py | exit=0 | OK: 2094 doc checks passed | stderr=0
```
四份原始基線 `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- <四基線>` 為空；本 commit 只在本檔後追加（原 466 行逐位元不變）。

## 資源、保留與清理
保留：`/tmp/stp-d1-env-r1/{venv,wheelhouse}`（約 99 MB；/tmp 暫存，容器重啟即失，且本輪不再下載，重建需新的工單授權）與 `/tmp/stp-d1-scripts`（腳本與輸出）。已刪：pgdata／sock／log、offline_install.log；無 CA 複本、無下載 log、無遺留 postgres 程序。

## 未證明／剩餘缺口
- Docker／Compose、Django 專案／migration／HTTP、LTS 查核、供應鏈鎖定仍未驗證。
- stub 驗證的是**編排的控制流程**，不是 PostgreSQL／pip 的實際行為；實際故障（真的 stop 失敗）仍只以 stub 模擬，沒有在真實 PG 上製造 stop 失敗。
- cleanup 的「immediate」第二次停止僅用於本 task pgdata；若兩次仍失敗只保留與回報，未做 kill。
- 測試 DB 為 trust 認證、fsync off，僅一次性隔離。
- 外部呼叫：無；支出 0；真實資料無；Secret 未讀；部署／merge 無。AUTHOR_EVIDENCE，不自批。

---

# Repair 3（最後一次；ENV-01 剩餘：管線掩蓋上游 exit、程序／TCP 查詢失敗、停止總次數）

task：STP-PLATFORM-PLAN-001-D1-ENVIRONMENT｜repair 3／3（limit 2→3，已用 2→3）｜claim：issuecomment-6114297112（session_01MvUGYirGBtHVdHk3mYxAkh）
工單：issuecomment-6114285917 + GPT_D1_ENVIRONMENT_REPAIR3_PACKET_20261012.md｜handoff：578c6f91914a489e1066cbdbf4ef2d300a4d38fa｜source：8920a79d71eccfdac9ab9ed0cb06cefb5a4513ab｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
本段只追加；上方原 843 行未改。時間：2026-10-11 22:01～22:04Z（本 session 時鐘，REPORTED），遠低於 15 分鐘。**本段沒有任何外部下載或外部呼叫**。層級：隔離 runtime（正常路與注入路）＋合成 stub 控制流程反例（stub 不是 runtime）。無第四輪預授權：若仍未通過，不續修此編排，改交安全替代方案（見末段）。

## ENV-01 對照（根因 → 修改 → 反例 → 命令 → 結果 → 缺口）
- 根因（GPT repair2 覆核）：(1) `pip freeze | sort` 的 exit 是 sort 的，freeze 印合法清單但 exit 1 仍通過；(2) `pgrep | wc -l` 把查詢錯誤（exit 2／127）算成 0 程序後 `rm`；(3) 正常停止 1 次＋cleanup 2 次，每 task 可能呼叫 3 次 `pg_ctl stop`。
- 另一個由本輪嚴格化**自己發現**的真實缺陷：v1／v2 的 `ss -ltn 2>/dev/null | grep -c ':5432 '` 在本機根本沒有 `ss`（`command -v ss` exit 1，`ss` 回 127），錯誤被丟到 `/dev/null`、`grep -c` 印 0，所以 repair1／repair2 §A 輸出中的「tcp 5432 listeners: 0」**不是有效證據**（等同把工具缺失當成無監聽）。v3 改為讀 `/proc/net/tcp` 與 `tcp6` 的 LISTEN 狀態（本機無 `tcp6` 檔＝未設定 IPv6，明確記錄），讀取失敗即失敗。先前報告中的該行請以本段為準更正。PG 本身的 `listen_addresses=''` 讀回（有效）與 v3 的 `/proc/net/tcp` 掃描共同構成無 TCP 的證據。
- 修改（`orchestrate_v3.sh`，v1／v2 保留為歷史）：
  - freeze：先捕原命令 exit（非 0 即失敗）才 `sort` 比對；`stat` 權限、`/proc/net` 掃描同樣依實際 exit。
  - 程序查詢：`pgrep` exit 0＝找到（>0 程序→保留）、1＝確定無程序、其他（2、127…）＝查詢失敗→`CLEANUP_FAILED`、資料保留、exit 9；只有 status 3 **且**確定無程序才刪 pgdata／socket／log。
  - 停止額度：`stop_server` 以共享計數 `STOP_ATTEMPTS` 限制每 task 總共最多 2 次 `pg_ctl stop`（正常 fast 一次＋cleanup 補一次；inject 未正常停止時 cleanup 最多 fast＋immediate 共 2 次）；額度用完不再呼叫、不 kill 任何程序，仍未確認停止則保留資料、exit 9；RESULT 行輸出 `stop_attempts=N`，第一個失敗原因不被覆蓋。
- 沿用不改寫：ENV-02 純函式與 mock（repair1 §C）、ENV-03 wheelhouse 清單與離線安裝核對（repair1 §D；本輪 `verify` 仍以 `sha256sum -c` 對照同一份 hash）。

## 腳本：`orchestrate_v3.sh`
```bash
#!/bin/bash
# D1 隔離環境編排 v3（fail-closed；管線不吞上游 exit；程序／TCP 查詢失敗保留資料；停止總次數 ≤2）。不下載任何東西：只使用既存 task venv／wheelhouse／PG16。
# 用法：orchestrate_v3.sh verify            preflight＋離線安裝＋版本核對（不下載）
#       orchestrate_v3.sh db ok|inject      私人 socket PG16 煙霧；每步依 exit／預期值裁定；cleanup 失敗不刪資料
# 結束碼：0 全部成功；1 某步驟失敗（或預期值不符）；7 注入模式且一切符合預期（煙霧注入失敗 exit 7、cleanup 正常）；9 cleanup 失敗（資料保留）
set -u
umask 077
D=${STP_D:-/tmp/stp-d1-env-r1}
S=${STP_S:-/tmp/stp-d1-scripts}
PGBIN=${STP_PGBIN:-/usr/lib/postgresql/16/bin}
PGREP=${STP_PGREP:-pgrep}
PROCNET=${STP_PROCNET:-/proc/net}      # 無 ss 時以 /proc/net/tcp{,6} 證明沒有 5432 的 LISTEN
if [ -n "${STP_RUN_STUB:-}" ]; then                       # 合成 stub 測試用：不降權、不碰真實 PG
  RUN=(env HOME="$D" PATH="$PATH")
  CHOWN=:
else
  RUN=(setpriv --reuid=999 --regid=999 --clear-groups env HOME="$D" PATH=/usr/bin:/bin)
  CHOWN="chown 999:999"
fi
VENVPY="$D/venv/bin/python"
PIP="$D/venv/bin/pip"
PINS="Django==6.1.2 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0"
EXPECT_FREEZE=$'Django==6.1.2\nasgiref==3.12.1\npsycopg-binary==3.3.6\npsycopg==3.3.6\nsqlparse==0.6.0'

FAIL=""          # 第一個失敗原因
MAIN_RC=0
CLEAN_FAIL=0
STOP_ATTEMPTS=0     # 每個 task 總停止次數上限 2（正常 + cleanup 共用）

note_fail() { [ -z "$FAIL" ] && FAIL="$1"; echo "FAIL: $1"; }

# run_expect <name> <expected_rc> <cmd...>：失敗時記錄並回傳 1，不吞錯
run_expect() {
  local name=$1 want=$2; shift 2
  "$@"; local rc=$?
  echo "$name exit=$rc (expected $want)"
  [ $rc -eq "$want" ] || { note_fail "$name exit=$rc expected=$want"; return 1; }
  return 0
}

# 共享停止額度：正常停止與 cleanup 合計最多 2 次；額度用完不再呼叫 pg_ctl（回 99），不 kill 任何程序
stop_server() {
  if [ "$STOP_ATTEMPTS" -ge 2 ]; then echo "stop budget exhausted (max 2 per task)"; return 99; fi
  STOP_ATTEMPTS=$((STOP_ATTEMPTS+1))
  "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" -m "$1" -w stop; local rc=$?
  echo "pg_ctl stop#$STOP_ATTEMPTS ($1) exit=$rc"
  return $rc
}

verify_body() {
  # preflight：固定 Python／既存 artifact／清單，不通過就不往下（且不下載）
  local pyv; pyv=$("${RUN[@]}" "$VENVPY" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null); local rc=$?
  echo "preflight venv python=[$pyv] exit=$rc (need >= 3.12)"
  [ $rc -eq 0 ] || { note_fail "preflight python exit=$rc"; return 1; }
  case "$pyv" in 3.1[2-9]|3.[2-9][0-9]) ;; *) note_fail "preflight python too old: $pyv"; return 1;; esac
  [ -d "$D/wheelhouse" ] || { note_fail "preflight wheelhouse missing"; return 1; }
  if [ -f "$S/wheelhouse.sha256" ]; then
    ( cd "$D/wheelhouse" && sha256sum -c "$S/wheelhouse.sha256" ); rc=$?
    echo "wheelhouse sha256 -c exit=$rc"; [ $rc -eq 0 ] || { note_fail "wheelhouse sha256 mismatch exit=$rc"; return 1; }
  else
    note_fail "preflight wheelhouse.sha256 missing"; return 1
  fi
  run_expect offline_install 0 "${RUN[@]}" "$PIP" --isolated --disable-pip-version-check install --no-input --no-index --find-links "$D/wheelhouse" --no-deps --force-reinstall $PINS > "$D/offline_install.log" 2>&1 || return 1
  local fz_raw fz; fz_raw=$("${RUN[@]}" "$PIP" --isolated --disable-pip-version-check freeze 2>/dev/null); rc=$?   # 先捕原命令 exit，再排序
  echo "pip freeze exit=$rc"
  [ $rc -eq 0 ] || { note_fail "pip freeze exit=$rc"; return 1; }
  fz=$(printf '%s\n' "$fz_raw" | sort); echo "$fz"
  [ "$fz" = "$(printf '%s\n' "$EXPECT_FREEZE" | sort)" ] || { note_fail "installed versions differ from pinned list"; return 1; }
  local ver; ver=$("${RUN[@]}" "$VENVPY" -c 'import django,psycopg;print(django.get_version(), psycopg.__version__)' 2>&1); rc=$?
  echo "import check exit=$rc [$ver]"
  [ $rc -eq 0 ] && [ "$ver" = "6.1.2 3.3.6" ] || { note_fail "import/version check failed: $ver"; return 1; }
  return 0
}

db_body() {
  local mode=$1
  [ -d "$D" ] || { mkdir -p "$D" && chmod 700 "$D" && $CHOWN "$D"; } || { note_fail "task dir"; return 1; }
  run_expect mkdir_sock 0 mkdir -m 700 "$D/sock" || return 1
  $CHOWN "$D/sock"
  "${RUN[@]}" "$PGBIN/initdb" -D "$D/pgdata" -A trust -U stp_smoke --no-sync -E UTF8 --locale=C.UTF-8 > "$D/initdb.log" 2>&1; local rc=$?
  echo "initdb exit=$rc (expected 0)"; [ $rc -eq 0 ] || { note_fail "initdb exit=$rc"; return 1; }
  "${RUN[@]}" sh -c 'printf "%s\n" "listen_addresses = '"''"'" "unix_socket_directories = '"'"'$1/sock'"'"'" "unix_socket_permissions = 0700" "fsync = off" >> "$1/pgdata/postgresql.conf"' _ "$D"; rc=$?
  echo "config write exit=$rc (expected 0)"; [ $rc -eq 0 ] || { note_fail "config write exit=$rc"; return 1; }
  local la sd sp
  la=$("${RUN[@]}" "$PGBIN/postgres" -D "$D/pgdata" -C listen_addresses 2>&1); rc=$?; [ $rc -eq 0 ] || { note_fail "readback listen_addresses exit=$rc"; return 1; }
  sd=$("${RUN[@]}" "$PGBIN/postgres" -D "$D/pgdata" -C unix_socket_directories 2>&1); rc=$?; [ $rc -eq 0 ] || { note_fail "readback unix_socket_directories exit=$rc"; return 1; }
  sp=$("${RUN[@]}" "$PGBIN/postgres" -D "$D/pgdata" -C unix_socket_permissions 2>&1); rc=$?; [ $rc -eq 0 ] || { note_fail "readback unix_socket_permissions exit=$rc"; return 1; }
  echo "readback listen_addresses=[$la] unix_socket_directories=[$sd] unix_socket_permissions=[$sp] (expected [] [$D/sock] [448])"
  [ -z "$la" ] && [ "$sd" = "$D/sock" ] && [ "$sp" = "448" ] || { note_fail "config readback mismatch"; return 1; }
  local sm; sm=$(stat -c %a "$D/sock"); rc=$?
  echo "sock dir mode=[$sm] exit=$rc (expected 700)"
  [ $rc -eq 0 ] && [ "$sm" = "700" ] || { note_fail "sock dir mode check failed (exit=$rc mode=$sm)"; return 1; }
  run_expect pg_start 0 "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" -l "$D/pg.log" -w -t 30 start || return 1
  # TCP 監聽核對：讀 /proc/net/tcp（必須成功）與 tcp6（檔案存在則必須成功；不存在＝本機未設定 IPv6，明確記錄）。
  # 欄位 4 = 狀態 0A = LISTEN；本地埠 5432 = 十六進位 1538。讀取失敗即失敗，不把空輸出當成功。
  local tcp tcp6=0 t6files="$PROCNET/tcp"
  if [ -e "$PROCNET/tcp6" ]; then t6files="$PROCNET/tcp $PROCNET/tcp6"; else echo "tcp6 absent: IPv6 not configured on this host (recorded, not silently skipped)"; fi
  tcp=$(awk 'NR>1 && $4=="0A" { n=split($2,a,":"); if (toupper(a[n])=="1538") c++ } END { print c+0 }' $t6files); rc=$?
  echo "proc-net tcp scan exit=$rc listeners_on_5432=$tcp (expected exit 0, listeners 0)"
  [ $rc -eq 0 ] || { note_fail "proc-net scan exit=$rc (cannot prove no TCP listener)"; return 1; }
  [ "$tcp" = "0" ] || { note_fail "unexpected TCP 5432 listener"; return 1; }
  if [ "$mode" = inject ]; then
    run_expect smoke_inject 7 "${RUN[@]}" "$VENVPY" "$S/smoke.py" "$D/sock" ok inject || return 1
    MAIN_RC=7
    return 0
  fi
  run_expect smoke_positive 0 "${RUN[@]}" "$VENVPY" "$S/smoke.py" "$D/sock" ok || return 1
  run_expect pg_stop 0 stop_server fast || return 1
  run_expect pg_status_after_stop 3 "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1 || return 1
  run_expect smoke_negative_down 0 "${RUN[@]}" "$VENVPY" "$S/smoke.py" "$D/sock" down || return 1
  return 0
}

cleanup() {
  echo "--- cleanup ---"
  if [ -d "$D/pgdata" ]; then
    "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; local st=$?
    echo "cleanup status exit=$st (3 = not running)"
    local mode
    for mode in fast immediate; do                         # 受共享額度限制：總共最多 2 次停止
      [ $st -eq 3 ] && break
      stop_server $mode; local srv=$?
      echo "cleanup stop($mode) exit=$srv (attempts so far=$STOP_ATTEMPTS)"
      "${RUN[@]}" "$PGBIN/pg_ctl" -D "$D/pgdata" status >/dev/null 2>&1; st=$?
      echo "cleanup status exit=$st"
    done
    # 程序查詢：0=找到、1=未找到；其他（2、127…）=查詢失敗，一律保留資料
    local pout prc procs=unknown
    pout=$("$PGREP" -f "^$PGBIN/postgres -D $D/pgdata" 2>/dev/null); prc=$?
    case $prc in
      1) procs=0 ;;
      0) procs=$(printf '%s\n' "$pout" | grep -c .) ;;
      *) procs=unknown ;;
    esac
    echo "task process scan: pgrep exit=$prc procs=$procs (1 = none found; other non-0 = scan FAILED)"
    if [ $st -ne 3 ] || [ "$procs" != "0" ]; then
      CLEAN_FAIL=1
      echo "CLEANUP_FAILED: server not confirmed stopped (status=$st procs=$procs); data RETAINED at $D (BLOCKED_CAPABILITY/partial)"
      return
    fi
  fi
  rm -rf "$D/pgdata" "$D/sock" "$D/pg.log" "$D/initdb.log"
  for p in pgdata sock pg.log initdb.log; do
    if [ -e "$D/$p" ]; then echo "LEFTOVER $p"; CLEAN_FAIL=1; else echo "removed $p"; fi
  done
}

finish() {
  local final
  if [ "$CLEAN_FAIL" = 1 ]; then final=9
  elif [ -n "$FAIL" ]; then final=1
  else final=$MAIN_RC; fi
  echo "RESULT: first_failure=[${FAIL:-none}] cleanup_failed=$CLEAN_FAIL stop_attempts=$STOP_ATTEMPTS final_exit=$final"
  exit $final
}

case "${1:-}" in
  verify) trap 'finish' EXIT; verify_body ;;
  db) trap 'cleanup; finish' EXIT; db_body "${2:-ok}" ;;
  *) echo "usage: $0 verify|db ok|inject"; exit 2 ;;
esac
```

## §A 實際 PG16 runtime（獨立於 stub）
`verify`（不下載）— exit 0：
```
preflight venv python=[3.13] exit=0 (need >= 3.12)
asgiref-3.12.1-py3-none-any.whl: OK
django-6.1.2-py3-none-any.whl: OK
psycopg-3.3.6-py3-none-any.whl: OK
psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl: OK
sqlparse-0.6.0-py3-none-any.whl: OK
wheelhouse sha256 -c exit=0
pip freeze exit=0
Django==6.1.2
asgiref==3.12.1
psycopg-binary==3.3.6
psycopg==3.3.6
sqlparse==0.6.0
import check exit=0 [6.1.2 3.3.6]
RESULT: first_failure=[none] cleanup_failed=0 stop_attempts=0 final_exit=0
script exit=0
```
`db ok` — exit 0：
```
mkdir_sock exit=0 (expected 0)
initdb exit=0 (expected 0)
config write exit=0 (expected 0)
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-env-r1/sock] unix_socket_permissions=[448] (expected [] [/tmp/stp-d1-env-r1/sock] [448])
sock dir mode=[700] exit=0 (expected 700)
waiting for server to start.... done
server started
pg_start exit=0 (expected 0)
tcp6 absent: IPv6 not configured on this host (recorded, not silently skipped)
proc-net tcp scan exit=0 listeners_on_5432=0 (expected exit 0, listeners 0)
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | unix_only: True
inside_tx=1 after_rollback=0 after_commit=1 all_synthetic=True -> POSITIVE_OK
smoke_positive exit=0 (expected 0)
waiting for server to shut down.... done
server stopped
pg_ctl stop#1 (fast) exit=0
pg_stop exit=0 (expected 0)
NEGATIVE_OK connection unavailable on expected socket | connection is bad: connection to server on socket "/tmp/stp-d1-env-r1/sock/.s.PGSQL.5432" failed: No such file or directory
smoke_negative_down exit=0 (expected 0)
--- cleanup ---
cleanup status exit=3 (3 = not running)
task process scan: pgrep exit=1 procs=0 (1 = none found; other non-0 = scan FAILED)
removed pgdata
removed sock
removed pg.log
removed initdb.log
RESULT: first_failure=[none] cleanup_failed=0 stop_attempts=1 final_exit=0
script exit=0
```
`db inject`（煙霧注入失敗 exit 7；cleanup 完成；腳本 exit 7 為預期）：
```
mkdir_sock exit=0 (expected 0)
initdb exit=0 (expected 0)
config write exit=0 (expected 0)
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-env-r1/sock] unix_socket_permissions=[448] (expected [] [/tmp/stp-d1-env-r1/sock] [448])
sock dir mode=[700] exit=0 (expected 700)
waiting for server to start.... done
server started
pg_start exit=0 (expected 0)
tcp6 absent: IPv6 not configured on this host (recorded, not silently skipped)
proc-net tcp scan exit=0 listeners_on_5432=0 (expected exit 0, listeners 0)
server_version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) | unix_only: True
INJECTED_FAILURE after table creation
smoke_inject exit=7 (expected 7)
--- cleanup ---
cleanup status exit=0 (3 = not running)
waiting for server to shut down.... done
server stopped
pg_ctl stop#1 (fast) exit=0
cleanup stop(fast) exit=0 (attempts so far=1)
cleanup status exit=3
task process scan: pgrep exit=1 procs=0 (1 = none found; other non-0 = scan FAILED)
removed pgdata
removed sock
removed pg.log
removed initdb.log
RESULT: first_failure=[none] cleanup_failed=0 stop_attempts=1 final_exit=7
script exit=7
```

## §B 合成 stub 控制流程反例（`stubtests_v3.sh`，29 項；stub 明標合成，不連 DB，不是 runtime）
原 17 項（genuine 0／注入 7／down5 拒絕／stop 保留／initdb／config／readback／start／install／version／hash／Python 過舊）全部保留，新增 12 項：freeze 印合法清單但 exit 1；pgrep exit 1（確定無程序，正常通過）、2、127、0（有程序）；`/proc/net/tcp` 不可讀、5432 TCP 監聽、IPv6 5432 監聽、`tcp6` 不存在（記錄後通過）；持續停止失敗（正常路與注入路，總 `pg_ctl stop` 呼叫皆 ≤2，額度用完後 `cleanup stop(immediate) exit=99`、資料保留、exit 9）；注入 genuine 只停止 1 次。每項核對 expected／actual exit、原因片段、pgdata 是否保留與 stop 呼叫次數。
```
PASS genuine_db_ok                      expected_exit=0  actual_exit=0  reason_match=[final_exit=0] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS genuine_db_inject                  expected_exit=7  actual_exit=7  reason_match=[final_exit=7] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS down_exit5                         expected_exit=1  actual_exit=1  reason_match=[smoke_negative_down exit=5] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS stop1_status0_no_delete            expected_exit=9  actual_exit=9  reason_match=[CLEANUP_FAILED] pgdata_retained(expected/actual)=yes/yes stop_calls=2(max -1)
PASS initdb1                            expected_exit=1  actual_exit=1  reason_match=[initdb exit=1] pgdata_retained(expected/actual)=no/no stop_calls=0(max -1)
PASS config_write_fail                  expected_exit=1  actual_exit=1  reason_match=[config write exit=] pgdata_retained(expected/actual)=no/no stop_calls=0(max -1)
PASS config_readback_mismatch           expected_exit=1  actual_exit=1  reason_match=[config readback mismatch] pgdata_retained(expected/actual)=no/no stop_calls=0(max -1)
PASS start1                             expected_exit=1  actual_exit=1  reason_match=[pg_start exit=1] pgdata_retained(expected/actual)=no/no stop_calls=0(max -1)
PASS positive_smoke_fails               expected_exit=1  actual_exit=1  reason_match=[smoke_positive exit=4] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS inject_wrong_exit                  expected_exit=1  actual_exit=1  reason_match=[smoke_inject exit=0] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS inject_cleanup_fails               expected_exit=9  actual_exit=9  reason_match=[CLEANUP_FAILED] pgdata_retained(expected/actual)=yes/yes stop_calls=2(max -1)
PASS verify_genuine                     expected_exit=0  actual_exit=0  reason_match=[final_exit=0] pgdata_retained(expected/actual)=na/no stop_calls=0(max -1)
PASS verify_offline_install1            expected_exit=1  actual_exit=1  reason_match=[offline_install exit=1] pgdata_retained(expected/actual)=na/no stop_calls=0(max -1)
PASS verify_version_mismatch            expected_exit=1  actual_exit=1  reason_match=[installed versions differ] pgdata_retained(expected/actual)=na/no stop_calls=0(max -1)
PASS verify_import_mismatch             expected_exit=1  actual_exit=1  reason_match=[import/version check failed] pgdata_retained(expected/actual)=na/no stop_calls=0(max -1)
PASS verify_python_too_old              expected_exit=1  actual_exit=1  reason_match=[preflight python too old] pgdata_retained(expected/actual)=na/no stop_calls=0(max -1)
PASS v3_freeze_valid_list_exit1         expected_exit=1  actual_exit=1  reason_match=[pip freeze exit=1] pgdata_retained(expected/actual)=na/no stop_calls=0(max -1)
PASS v3_pgrep_rc1_genuine               expected_exit=0  actual_exit=0  reason_match=[pgrep exit=1 procs=0] pgdata_retained(expected/actual)=no/no stop_calls=1(max 1)
PASS v3_pgrep_rc2_scan_error            expected_exit=9  actual_exit=9  reason_match=[pgrep exit=2 procs=unknown] pgdata_retained(expected/actual)=yes/yes stop_calls=1(max -1)
PASS v3_pgrep_rc127_missing_tool        expected_exit=9  actual_exit=9  reason_match=[pgrep exit=127 procs=unknown] pgdata_retained(expected/actual)=yes/yes stop_calls=1(max -1)
PASS v3_pgrep_rc0_process_found         expected_exit=9  actual_exit=9  reason_match=[procs=1] pgdata_retained(expected/actual)=yes/yes stop_calls=1(max -1)
PASS v3_procnet_unreadable              expected_exit=1  actual_exit=1  reason_match=[proc-net scan exit=2] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS v3_ss_tcp_listener                 expected_exit=1  actual_exit=1  reason_match=[unexpected TCP 5432 listener] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS v3_stop_persistent_fail_ok         expected_exit=9  actual_exit=9  reason_match=[cleanup stop(immediate) exit=99] pgdata_retained(expected/actual)=yes/yes stop_calls=2(max 2)
PASS v3_stop_persistent_inject          expected_exit=9  actual_exit=9  reason_match=[attempts so far=2] pgdata_retained(expected/actual)=yes/yes stop_calls=2(max 2)
PASS v3_inject_genuine_one_stop         expected_exit=7  actual_exit=7  reason_match=[stop_attempts=1] pgdata_retained(expected/actual)=no/no stop_calls=1(max 1)
PASS v3_tcp6_absent_recorded            expected_exit=0  actual_exit=0  reason_match=[tcp6 absent: IPv6 not configured] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS v3_tcp6_listener                   expected_exit=1  actual_exit=1  reason_match=[unexpected TCP 5432 listener] pgdata_retained(expected/actual)=no/no stop_calls=1(max -1)
PASS verify_wheel_hash_tamper           expected_exit=1  actual_exit=1  reason_match=[wheelhouse sha256 mismatch]
stubtests overall: ALL_PASS
```
`stubtests_v3.sh` 原文：
```bash
#!/bin/bash
# v3：新增 freeze 上游 exit、pgrep 0/1/2/127、ss 查詢失敗與 TCP 監聽、停止總次數 ≤2。
# 合成 stub 控制流程反例（不連 DB、不降權、不碰真實 PG；stub 明標合成，不是 runtime）。
# 每個情境：以 STP_RUN_STUB=1 執行真正的 orchestrate_v3.sh，stub 的 PG／python／pip 依 FAKE_* 回傳指定 exit，核對 expected/actual。
set -u
S=/tmp/stp-d1-scripts
T=$(mktemp -d /tmp/stp-stub-XXXXXX)
mk_fixture() {            # $1 = fixture dir
  local F=$1; rm -rf "$F"; mkdir -p "$F/D/venv/bin" "$F/D/wheelhouse" "$F/S" "$F/pgbin"
  echo synthetic > "$F/D/wheelhouse/pkg-1.0-py3-none-any.whl"
  ( cd "$F/D/wheelhouse" && sha256sum pkg-1.0-py3-none-any.whl ) > "$F/S/wheelhouse.sha256"
  cat > "$F/pgbin/pg_ctl" <<'X'
#!/bin/bash
ST="$STP_D/.state"; cmd=""
for a in "$@"; do case $a in start|stop|status) cmd=$a;; esac; done
case $cmd in
  start) [ "${FAKE_START_RC:-0}" = 0 ] && touch "$ST"; exit ${FAKE_START_RC:-0};;
  stop) [ -n "${FAKE_LOG:-}" ] && echo stop >> "$FAKE_LOG"; [ "${FAKE_STOP_RC:-0}" = 0 ] && rm -f "$ST"; exit ${FAKE_STOP_RC:-0};;
  status) [ -n "${FAKE_STATUS_FIXED:-}" ] && exit $FAKE_STATUS_FIXED; [ -f "$ST" ] && exit 0 || exit 3;;
esac
X
  cat > "$F/pgbin/initdb" <<'X'
#!/bin/bash
while [ $# -gt 0 ]; do [ "$1" = -D ] && dir=$2; shift; done
rc=${FAKE_INITDB_RC:-0}
if [ $rc -eq 0 ]; then mkdir -p "$dir"; if [ -n "${FAKE_CONF_DIR:-}" ]; then mkdir -p "$dir/postgresql.conf"; else : > "$dir/postgresql.conf"; fi; fi
exit $rc
X
  cat > "$F/pgbin/postgres" <<'X'
#!/bin/bash
case "$4" in
  listen_addresses) echo "${FAKE_LISTEN:-}";;
  unix_socket_directories) echo "$STP_D/sock";;
  unix_socket_permissions) echo 448;;
esac
X
  cat > "$F/D/venv/bin/python" <<'X'
#!/bin/bash
if [ "$1" = -c ]; then
  case "$2" in *version_info*) echo "${FAKE_PYV:-3.13}";; *django*) echo "${FAKE_IMPORT:-6.1.2 3.3.6}";; esac; exit 0
fi
mode=$3; inj=${4:-}
[ "$mode" = down ] && exit ${FAKE_DOWN_RC:-0}
[ "$inj" = inject ] && exit ${FAKE_INJECT_RC:-7}
exit ${FAKE_POS_RC:-0}
X
  cat > "$F/D/venv/bin/pip" <<'X'
#!/bin/bash
for a in "$@"; do case $a in install) exit ${FAKE_PIP_RC:-0};; freeze) printf '%s\n' ${FAKE_FREEZE:-Django==6.1.2 asgiref==3.12.1 psycopg-binary==3.3.6 psycopg==3.3.6 sqlparse==0.6.0}; exit ${FAKE_FREEZE_RC:-0};; esac; done
X
  cat > "$F/pgbin/fake_pgrep" <<'X'
#!/bin/bash
rc=${FAKE_PGREP_RC:-1}; [ $rc -eq 0 ] && echo 12345; exit $rc
X
  mkdir -p "$F/procnet"; hdr="  sl  local_address rem_address   st tx_queue rx_queue"
  { echo "$hdr"; echo "   1: 0100007F:0050 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 1 1 0000000000000000 100 0 0 10 0"; } > "$F/procnet/tcp"
  echo "$hdr" > "$F/procnet/tcp6"
  chmod 755 "$F"/pgbin/* "$F"/D/venv/bin/*
}
bad=0
# scenario <name> <subcommand...> -- <expected_exit> <expected_reason_substring> <expect_pgdata_retained:yes|no|na> [VAR=VAL ...]
scenario() {
  local name=$1; shift
  local sub=(); while [ "$1" != -- ]; do sub+=("$1"); shift; done; shift
  local want=$1 reason=$2 retained=$3; shift 3
  local F="$T/$name"; mk_fixture "$F"
  local maxstops=-1 extra=() a
  for a in "$@"; do case $a in MAXSTOPS=*) maxstops=${a#MAXSTOPS=};; *) extra+=("$a");; esac; done
  for a in "${extra[@]}"; do case $a in
    FAKE_SS_TCP=*) echo "   2: 0100007F:1538 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 1 1 0000000000000000 100 0 0 10 0" >> "$F/procnet/tcp";;
    FAKE_PROC_MISSING=*) rm -f "$F/procnet/tcp";;
    FAKE_TCP6_ABSENT=*) rm -f "$F/procnet/tcp6";;
    FAKE_TCP6_LISTEN=*) echo "   2: 00000000000000000000000001000000:1538 00000000000000000000000000000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 1 1 0000000000000000 100 0 0 10 0" >> "$F/procnet/tcp6";;
  esac; done
  local out; out=$(env STP_RUN_STUB=1 STP_D="$F/D" STP_S="$F/S" STP_PGBIN="$F/pgbin" STP_PGREP="$F/pgbin/fake_pgrep" STP_PROCNET="$F/procnet" FAKE_LOG="$F/stops.log" "${extra[@]}" bash "$S/orchestrate_v3.sh" "${sub[@]}" 2>&1); local rc=$?
  local nstop=0; [ -f "$F/stops.log" ] && nstop=$(wc -l < "$F/stops.log")
  if [ "$maxstops" -ge 0 ] && [ "$nstop" -gt "$maxstops" ]; then ok_stop=0; else ok_stop=1; fi
  local ok=$ok_stop
  [ $rc -eq "$want" ] || ok=0
  echo "$out" | grep -q -- "$reason" || ok=0
  local kept=no; [ -d "$F/D/pgdata" ] && kept=yes
  { [ "$retained" = na ] || [ "$retained" = "$kept" ]; } || ok=0
  [ $ok -eq 1 ] && v=PASS || { v=FAIL; bad=1; }
  printf '%s %-34s expected_exit=%-2s actual_exit=%-2s reason_match=[%s] pgdata_retained(expected/actual)=%s/%s stop_calls=%s(max %s)\n' "$v" "$name" "$want" "$rc" "$reason" "$retained" "$kept" "$nstop" "$maxstops"
}
scenario genuine_db_ok            db ok       -- 0 "final_exit=0" no
scenario genuine_db_inject        db inject   -- 7 "final_exit=7" no
scenario down_exit5               db ok       -- 1 "smoke_negative_down exit=5" no   FAKE_DOWN_RC=5
scenario stop1_status0_no_delete  db ok       -- 9 "CLEANUP_FAILED" yes               FAKE_STOP_RC=1 FAKE_STATUS_FIXED=0
scenario initdb1                  db ok       -- 1 "initdb exit=1" no                 FAKE_INITDB_RC=1
scenario config_write_fail        db ok       -- 1 "config write exit=" no            FAKE_CONF_DIR=1
scenario config_readback_mismatch db ok       -- 1 "config readback mismatch" no      FAKE_LISTEN="*"
scenario start1                   db ok       -- 1 "pg_start exit=1" no               FAKE_START_RC=1
scenario positive_smoke_fails     db ok       -- 1 "smoke_positive exit=4" no         FAKE_POS_RC=4
scenario inject_wrong_exit        db inject   -- 1 "smoke_inject exit=0" no            FAKE_INJECT_RC=0
scenario inject_cleanup_fails     db inject   -- 9 "CLEANUP_FAILED" yes               FAKE_STOP_RC=1 FAKE_STATUS_FIXED=0
scenario verify_genuine           verify      -- 0 "final_exit=0" na
scenario verify_offline_install1  verify      -- 1 "offline_install exit=1" na        FAKE_PIP_RC=1
scenario verify_version_mismatch  verify      -- 1 "installed versions differ" na     FAKE_FREEZE="Django==6.0.1 asgiref==3.12.1 psycopg-binary==3.3.6 psycopg==3.3.6 sqlparse==0.6.0"
scenario verify_import_mismatch   verify      -- 1 "import/version check failed" na   FAKE_IMPORT="6.0.1 3.3.6"
scenario verify_python_too_old    verify      -- 1 "preflight python too old" na      FAKE_PYV=3.11
# ---- v3 新增 ----
scenario v3_freeze_valid_list_exit1  verify   -- 1 "pip freeze exit=1" na                    FAKE_FREEZE_RC=1
scenario v3_pgrep_rc1_genuine        db ok    -- 0 "pgrep exit=1 procs=0" no                 FAKE_PGREP_RC=1 MAXSTOPS=1
scenario v3_pgrep_rc2_scan_error     db ok    -- 9 "pgrep exit=2 procs=unknown" yes          FAKE_PGREP_RC=2
scenario v3_pgrep_rc127_missing_tool db ok    -- 9 "pgrep exit=127 procs=unknown" yes        FAKE_PGREP_RC=127
scenario v3_pgrep_rc0_process_found  db ok    -- 9 "procs=1" yes                              FAKE_PGREP_RC=0
scenario v3_procnet_unreadable        db ok    -- 1 "proc-net scan exit=2" no                  FAKE_PROC_MISSING=1
scenario v3_ss_tcp_listener          db ok    -- 1 "unexpected TCP 5432 listener" no          FAKE_SS_TCP=1
scenario v3_stop_persistent_fail_ok  db ok    -- 9 "cleanup stop(immediate) exit=99" yes                FAKE_STOP_RC=1 FAKE_STATUS_FIXED=0 MAXSTOPS=2
scenario v3_stop_persistent_inject   db inject -- 9 "attempts so far=2" yes                  FAKE_STOP_RC=1 FAKE_STATUS_FIXED=0 MAXSTOPS=2
scenario v3_inject_genuine_one_stop  db inject -- 7 "stop_attempts=1" no                     MAXSTOPS=1
scenario v3_tcp6_absent_recorded     db ok    -- 0 "tcp6 absent: IPv6 not configured" no     FAKE_TCP6_ABSENT=1
scenario v3_tcp6_listener            db ok    -- 1 "unexpected TCP 5432 listener" no          FAKE_TCP6_LISTEN=1
# wheelhouse hash 被改動：fixture 後手動竄改
F="$T/verify_hash_tamper"; mk_fixture "$F"; echo tampered > "$F/D/wheelhouse/pkg-1.0-py3-none-any.whl"
out=$(env STP_RUN_STUB=1 STP_D="$F/D" STP_S="$F/S" STP_PGBIN="$F/pgbin" bash "$S/orchestrate_v3.sh" verify 2>&1); rc=$?
if [ $rc -eq 1 ] && echo "$out" | grep -q "wheelhouse sha256 mismatch"; then v=PASS; else v=FAIL; bad=1; fi
printf '%s %-34s expected_exit=1  actual_exit=%-2s reason_match=[wheelhouse sha256 mismatch]\n' "$v" verify_wheel_hash_tamper "$rc"
rm -rf "$T"
echo "stubtests overall: $([ $bad -eq 0 ] && echo ALL_PASS || echo SOME_FAIL)"
exit $bad
```

## §C repo 必要檢查（於追加本段前的樹；皆 exit 0，stderr 空）
```
python3 docs/platform/examples/check_examples.py | exit=0 | OK: 1306 checks passed | stderr=0
python3 docs/platform/tools/gen_state_machines.py --check | exit=0 | OK: 6 state machines, 86 transitions, doc in sync | stderr=0
python3 docs/platform/tools/gen_permissions.py --check | exit=0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | stderr=0
python3 docs/platform/tools/test_checks.py | exit=0 | OK: test_checks 136 counterexample checks passed | stderr=0
python3 docs/platform/tools/check_docs.py | exit=0 | OK: 2096 doc checks passed | stderr=0
```
四份原始基線 `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- <四基線>` 為空；本 commit 只在本檔後追加（原 843 行逐位元不變，SHA256 見交付留言）。

## 資源、保留與清理
保留：`/tmp/stp-d1-env-r1/{venv,wheelhouse}`（約 99 MB；/tmp 暫存，重啟即失，本輪不再下載）與 `/tmp/stp-d1-scripts`。已刪 pgdata／sock／log／offline_install.log；task postgres 程序 0（pgrep exit 1）。

## 未證明／剩餘缺口與停止後的安全替代
- 未做：Docker／Compose、Django 專案／migration／HTTP、LTS 查核、供應鏈鎖定；未在真實 PG 上製造 stop 失敗或 pgrep 錯誤（僅 stub）。
- 非 root 身分、trust 認證、fsync off 的限制同前。
- 若 GPT 判定本輪仍未通過：我不再續修此 bash 編排。建議的安全替代＝把「環境驗證」縮成**只讀的 `verify`（不啟動 DB）**加上**人工在受控環境啟停 PG16**的 D1 前置 SOP，D1 實作包以 `verify` 的結果作為進場條件，DB 啟停改由 Django 測試框架在隔離 socket 內自行建立／銷毀測試資料庫（不使用本編排）。這需要 GPT／負責人決定，我不自行採用。
- 外部呼叫：無；支出 0；真實資料無；Secret 未讀；部署／merge 無。AUTHOR_EVIDENCE，不自批。

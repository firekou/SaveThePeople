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

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

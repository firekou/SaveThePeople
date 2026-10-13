# D1 LTS 版本實檔與隔離 runtime 驗證回覆（D1_LTS_RUNTIME）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-D1-LTS-RUNTIME｜stage：D1_LTS_RUNTIME｜一次交付（repair_round_limit 0）
工單：issuecomment-6115426591 + GPT_D1_LTS_RUNTIME_PACKET_20261012.md｜claim：issuecomment-6115433650（session_01MvUGYirGBtHVdHk3mYxAkh）
source：0622fbf1035c6d9fa1375f7d122ebb1c218d7e83｜handoff：380300e9abab29f76af73d4107e31cfa154d0493（source 為其 ancestor）｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
時間（本 session 時鐘，2026-10-12 UTC）：開始約 00:09Z，完成約 00:13Z。層級：隔離 runtime 版本驗證（AUTHOR_EVIDENCE，非 VERIFIED、非 APPROVED）。**這是 LTS 版本相容性驗證，不是第四輪編排修補**；v3 控制流程與安全邊界不變（見 §3 diff：僅版本字串與路徑）。
原環境回覆（1286 行）與 D1_STACK 回覆（142 行）保持原文，本檔只新增；下列「LTS venv」與原 `/tmp/stp-d1-env-r1`（Django 6.1.2）分開。

## 1. 下載 attempt 與檔案核對
- preflight（下載前，皆通過）：既存 task Python 3.13.16（`PATH=/usr/bin:/bin`，uid 999 降權）；原 wheelhouse 中 4 個依賴 wheel `sha256sum -c` OK；PostgreSQL 16.15 執行檔存在；原 venv 的 pip 存在。
- 下載：`pip --isolated --disable-pip-version-check download --no-input --no-deps --only-binary=:all: -d <dl> Django==5.2.18`（使用**原 venv 的 pip 完整路徑**，只下載、不修改該 venv；公共 CA 複本只在此步驟使用，完成後即刪；未讀 pip 設定／Secret／環境值）。**attempt 累計 = 1，exit 0**；無重試；目錄內只有 1 個檔案。
- 核對（實檔，非 metadata）：檔名 `django-5.2.18-py3-none-any.whl`；大小 **8316071** bytes（工單預期 8316071）；SHA256 `92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c`（工單預期相同）→ **實檔核對一致**。（與 D1_STACK 回覆中引用的 PyPI metadata hash 也一致；本次是實檔計算，不是 metadata 轉述。）
- 新 LTS wheelhouse：`/tmp/stp-d1-lts/wheelhouse`（5 個 wheel：Django 5.2.18 實檔＋4 個複製自原 wheelhouse且已核 hash 的依賴）；新清單 `wheelhouse.sha256`：
```
fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094  asgiref-3.12.1-py3-none-any.whl
92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c  django-5.2.18-py3-none-any.whl
a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631  psycopg-3.3.6-py3-none-any.whl
cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269  psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f  sqlparse-0.6.0-py3-none-any.whl
```

## 2. 準備腳本與輸出
`lts_prepare.sh`（正文；root 啟動，之後皆 uid 999）：
```bash
#!/bin/bash
# D1_LTS_RUNTIME 準備：新 LTS task 目錄（不覆寫原 venv）。root 啟動；venv／pip 皆以既有非 root 身分 uid 999 執行。
# 下載只允許 Django==5.2.18 的 wheel 一次（暫時網路錯誤才可同請求重試一次）；preflight 不過不下載；下載後核對檔名／大小／SHA256，不符不安裝。
set -u
umask 077
OLD=/tmp/stp-d1-env-r1
LD=/tmp/stp-d1-lts
R=(setpriv --reuid=999 --regid=999 --clear-groups env HOME="$LD" PATH=/usr/bin:/bin)
WANT_FILE=django-5.2.18-py3-none-any.whl
WANT_SIZE=8316071
WANT_SHA=92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c
fail() { echo "FAIL: $1"; exit "${2:-1}"; }

mkdir -p "$LD/wheelhouse" && chmod 700 "$LD" && chown -R 999:999 "$LD" || fail "task dir"
# preflight：既存 Python、既存 4 依賴 wheel 的 hash；不過不下載
pyv=$("${R[@]}" python3 -c 'import sys;print("%d.%d" % sys.version_info[:2])'); rc=$?
echo "preflight python=[$pyv] exit=$rc"; [ $rc -eq 0 ] || fail "preflight python"
case "$pyv" in 3.1[2-9]) ;; *) fail "preflight python too old: $pyv";; esac
( cd "$OLD/wheelhouse" && grep -v ' django-' /tmp/stp-d1-scripts/wheelhouse.sha256 | sha256sum -c - ); rc=$?
echo "preflight existing 4 dependency wheels sha256 -c exit=$rc"; [ $rc -eq 0 ] || fail "preflight dependency wheels"
[ -x "$OLD/venv/bin/pip" ] || fail "preflight existing venv pip missing"
# 複製既有 4 依賴 wheel（已核 hash）
for f in asgiref-3.12.1-py3-none-any.whl psycopg-3.3.6-py3-none-any.whl psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl sqlparse-0.6.0-py3-none-any.whl; do
  cp "$OLD/wheelhouse/$f" "$LD/wheelhouse/$f" || fail "copy $f"
done
chown -R 999:999 "$LD"
# 下載：公共 CA 複本只在本步驟使用，結束即刪
cp /root/.ccr/ca-bundle.crt "$LD/ca.crt" && chown 999:999 "$LD/ca.crt"
attempt=1
while :; do
  "${R[@]}" REQUESTS_CA_BUNDLE="$LD/ca.crt" SSL_CERT_FILE="$LD/ca.crt" CURL_CA_BUNDLE="$LD/ca.crt" \
     "$OLD/venv/bin/pip" --isolated --disable-pip-version-check download --no-input --no-deps --only-binary=:all: -d "$LD/dl" "Django==5.2.18" > "$LD/download.log" 2>&1
  rc=$?; echo "pip download attempt=$attempt exit=$rc"
  [ $rc -eq 0 ] && break
  if [ $attempt -ge 2 ] || ! grep -qiE 'timed out|temporar|connection (reset|aborted|error)|ReadTimeout|ConnectTimeout' "$LD/download.log"; then
    echo "download failed (not retrying: attempt=$attempt, not a transient network error)"; tail -3 "$LD/download.log"; rm -f "$LD/ca.crt"; fail "download exit=$rc"
  fi
  attempt=2; sleep 3
done
rm -f "$LD/ca.crt"
ls -l "$LD/dl"
[ "$(ls "$LD/dl" | wc -l)" = "1" ] && [ -f "$LD/dl/$WANT_FILE" ] || fail "downloaded file set differs from the single expected wheel"
size=$(stat -c %s "$LD/dl/$WANT_FILE"); sha=$(sha256sum "$LD/dl/$WANT_FILE" | cut -c1-64)
echo "file=$WANT_FILE size=$size (want $WANT_SIZE) sha256=$sha"
echo "want sha256=$WANT_SHA"
[ "$size" = "$WANT_SIZE" ] && [ "$sha" = "$WANT_SHA" ] || fail "size/sha256 mismatch; NOT installing"
mv "$LD/dl/$WANT_FILE" "$LD/wheelhouse/$WANT_FILE" && rmdir "$LD/dl" && rm -f "$LD/download.log"
( cd "$LD/wheelhouse" && sha256sum * ) > "$LD/wheelhouse.sha256"; cat "$LD/wheelhouse.sha256" | cut -c1-110
# 新 venv + 離線安裝 5 個 wheel
"${R[@]}" python3 -m venv "$LD/venv" || fail "venv"
"${R[@]}" "$LD/venv/bin/pip" --isolated --disable-pip-version-check install --no-input --no-index --find-links "$LD/wheelhouse" --no-deps \
   Django==5.2.18 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0 > "$LD/offline_install.log" 2>&1; rc=$?
echo "offline install exit=$rc"; tail -2 "$LD/offline_install.log"; [ $rc -eq 0 ] || fail "offline install"
fz=$("${R[@]}" "$LD/venv/bin/pip" --isolated --disable-pip-version-check freeze); rc=$?; echo "pip freeze exit=$rc"; echo "$fz"
"${R[@]}" "$LD/venv/bin/python" -c "import sys,django,psycopg;print('python',sys.version.split()[0],'django',django.get_version(),'psycopg',psycopg.__version__)"; echo "import exit=$?"
rm -rf "$LD/.cache" "$LD/offline_install.log"
echo "PREPARE_OK"
```
輸出（exit 0，`PREPARE_OK`）：
```
preflight python=[3.13] exit=0
asgiref-3.12.1-py3-none-any.whl: OK
psycopg-3.3.6-py3-none-any.whl: OK
psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl: OK
sqlparse-0.6.0-py3-none-any.whl: OK
preflight existing 4 dependency wheels sha256 -c exit=0
pip download attempt=1 exit=0
total 8124
-rw------- 1 claude systemd-journal 8316071 Oct 12 00:09 django-5.2.18-py3-none-any.whl
file=django-5.2.18-py3-none-any.whl size=8316071 (want 8316071) sha256=92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c
want sha256=92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c
fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094  asgiref-3.12.1-py3-none-any.whl
92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c  django-5.2.18-py3-none-any.whl
a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631  psycopg-3.3.6-py3-none-any.whl
cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269  psycopg_binary-3.3.6-cp313-cp313-manylinux20
b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f  sqlparse-0.6.0-py3-none-any.whl
offline install exit=0

Successfully installed Django-5.2.18 asgiref-3.12.1 psycopg-3.3.6 psycopg-binary-3.3.6 sqlparse-0.6.0
pip freeze exit=0
asgiref==3.12.1
Django==5.2.18
psycopg==3.3.6
psycopg-binary==3.3.6
sqlparse==0.6.0
python 3.13.16 django 5.2.18 psycopg 3.3.6
import exit=0
PREPARE_OK
```

## 3. 編排：v3 與 LTS 副本的完整差異（控制流程未改）
`orchestrate_v3_lts.sh` 由 `orchestrate_v3.sh` 以 sed 產生，**僅**更新路徑、PINS／EXPECT_FREEZE／import 預期值與腳本名稱，`diff` 全文（22 行）：
```
3,4c3,4
< # 用法：orchestrate_v3.sh verify            preflight＋離線安裝＋版本核對（不下載）
< #       orchestrate_v3.sh db ok|inject      私人 socket PG16 煙霧；每步依 exit／預期值裁定；cleanup 失敗不刪資料
---
> # 用法：orchestrate_v3_lts.sh verify            preflight＋離線安裝＋版本核對（不下載）
> #       orchestrate_v3_lts.sh db ok|inject      私人 socket PG16 煙霧；每步依 exit／預期值裁定；cleanup 失敗不刪資料
8,9c8,9
< D=${STP_D:-/tmp/stp-d1-env-r1}
< S=${STP_S:-/tmp/stp-d1-scripts}
---
> D=${STP_D:-/tmp/stp-d1-lts}
> S=${STP_S:-/tmp/stp-d1-scripts-lts}
22,23c22,23
< PINS="Django==6.1.2 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0"
< EXPECT_FREEZE=$'Django==6.1.2\nasgiref==3.12.1\npsycopg-binary==3.3.6\npsycopg==3.3.6\nsqlparse==0.6.0'
---
> PINS="Django==5.2.18 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0"
> EXPECT_FREEZE=$'Django==5.2.18\nasgiref==3.12.1\npsycopg-binary==3.3.6\npsycopg==3.3.6\nsqlparse==0.6.0'
71c71
<   [ $rc -eq 0 ] && [ "$ver" = "6.1.2 3.3.6" ] || { note_fail "import/version check failed: $ver"; return 1; }
---
>   [ $rc -eq 0 ] && [ "$ver" = "5.2.18 3.3.6" ] || { note_fail "import/version check failed: $ver"; return 1; }
```
沿用不變：每步 exit／預期值裁定、`pgrep` 查詢失敗保留資料（exit 9）、總 `pg_ctl stop` ≤2、空 `listen_addresses`／私人 socket 0700／非 root／`is_synthetic=true`、`/proc/net` TCP 掃描。smoke.py／smokelib.py 與先前相同（複製，未改）。

## 4. 實際 runtime（Django 5.2.18 → psycopg 3.3.6 → PostgreSQL 16.15；獨立於 mock／stub）
`orchestrate_v3_lts.sh verify`（不下載；離線重裝並核對版本）— exit 0：
```
preflight venv python=[3.13] exit=0 (need >= 3.12)
asgiref-3.12.1-py3-none-any.whl: OK
django-5.2.18-py3-none-any.whl: OK
psycopg-3.3.6-py3-none-any.whl: OK
psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl: OK
sqlparse-0.6.0-py3-none-any.whl: OK
wheelhouse sha256 -c exit=0
pip freeze exit=0
Django==5.2.18
asgiref==3.12.1
psycopg-binary==3.3.6
psycopg==3.3.6
sqlparse==0.6.0
import check exit=0 [5.2.18 3.3.6]
RESULT: first_failure=[none] cleanup_failed=0 stop_attempts=0 final_exit=0
script exit=0
```
`orchestrate_v3_lts.sh db ok` — exit 0（交易內 1／rollback 後 0／commit 後 1／全合成；停止後指定 socket 不可用負向 NEGATIVE_OK；cleanup 完成）：
```
mkdir_sock exit=0 (expected 0)
initdb exit=0 (expected 0)
config write exit=0 (expected 0)
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-lts/sock] unix_socket_permissions=[448] (expected [] [/tmp/stp-d1-lts/sock] [448])
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
NEGATIVE_OK connection unavailable on expected socket | connection is bad: connection to server on socket "/tmp/stp-d1-lts/sock/.s.PGSQL.5432" failed: No such file or directory
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
`orchestrate_v3_lts.sh db inject` — 煙霧注入失敗 exit 7、腳本 exit 7（預期）、cleanup 完成：
```
mkdir_sock exit=0 (expected 0)
initdb exit=0 (expected 0)
config write exit=0 (expected 0)
readback listen_addresses=[] unix_socket_directories=[/tmp/stp-d1-lts/sock] unix_socket_permissions=[448] (expected [] [/tmp/stp-d1-lts/sock] [448])
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
版本：venv Python 3.13.16、Django 5.2.18、psycopg 3.3.6、psycopg-binary 3.3.6、asgiref 3.12.1、sqlparse 0.6.0（`pip freeze`／`import` 在 verify 與 prepare 輸出，exit 0）。PostgreSQL 16.15。

## 5. repo 必要檢查（於追加本檔前的樹；皆 exit 0，stderr 空）
```
python3 docs/platform/examples/check_examples.py | exit=0 | OK: 1306 checks passed | stderr=0
python3 docs/platform/tools/gen_state_machines.py --check | exit=0 | OK: 6 state machines, 86 transitions, doc in sync | stderr=0
python3 docs/platform/tools/gen_permissions.py --check | exit=0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | stderr=0
python3 docs/platform/tools/test_checks.py | exit=0 | OK: test_checks 136 counterexample checks passed | stderr=0
python3 docs/platform/tools/check_docs.py | exit=0 | OK: 2130 doc checks passed | stderr=0
```
四份原始基線 `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` 為空；本 commit 只新增本檔。

## 6. 資源、保留與清理
- 保留：`/tmp/stp-d1-lts/{venv,wheelhouse,wheelhouse.sha256}`（約 98 MB；/ 磁碟可用約 30 GB）與腳本 `/tmp/stp-d1-scripts-lts`；/tmp 為暫存，容器重啟即消失（重建需下載授權，現行授權僅此一次）。原 `/tmp/stp-d1-env-r1`（Django 6.1.2）未被修改，仍保留。
- 已刪：CA 複本、下載 log、offline_install.log、pip 快取、pgdata／sock／log；task postgres 程序 0（pgrep exit 1）。

## 7. 未證明／邊界
- 未證明：Django 5.2 LTS 官方標示與 PostgreSQL 支援期間（GPT 以其合法官方查詢補齊，見其覆核；本人出口政策被拒，**不自行重述為已驗證**）；Docker／Compose；Django 專案、migration、HTTP、360px；任何產品行為；供應鏈鎖定（本次僅單一 wheel 的實檔 hash，4 個依賴 wheel 沿用先前下載且已核 hash）。
- 外部呼叫：僅 PyPI 標準來源下載 1 個指定 wheel（attempt 1，成功）；無其他套件／版本；支出 0；真實資料無；Secret 未讀；全域安裝／OS 新 user／提權／Docker／部署／通知／merge 無；PR 維持 Draft。D1-A 仍 PREPARED，不因本驗證生效。AUTHOR_EVIDENCE，不自批。

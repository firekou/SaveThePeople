# D1 LTS 可重建交付包回覆（D1_LTS_REPLAY）

work_id：STP-PLATFORM-PLAN-001｜task：STP-PLATFORM-PLAN-001-D1-LTS-REPLAY｜stage：D1_LTS_REPLAY｜一次交付（repair_round_limit 0）
工單：issuecomment-6115934263 + GPT_D1_LTS_REPLAY_PACKET_20261012.md｜claim：issuecomment-6115941942（session_01MvUGYirGBtHVdHk3mYxAkh）
source：6c87bebebe4473358c18867cd232734d5fd8bb76｜handoff：333b6da7782cee5883dfb65a131bc485cb578bc6（source 為其 ancestor）｜base/main：9a7bd1295e20837786acc45bdab7fb94f5a1b012
本檔只整理**既有**交付，使完整 LTS 驗證腳本不再只存在於 /tmp；**沒有下載、安裝、啟動 DB／HTTP、查外部、讀 Secret／CA**，也不改控制流程。層級：回放說明＋提取／語法／hash 完整性（AUTHOR_EVIDENCE）。DB 與 artifact 實檔仍是先前交付的 AUTHOR_EVIDENCE；本檔**沒有重跑 DB**，不把回放說明當成已再次執行 runtime。

## 1. OBSERVED／RECONSTRUCTED 分開
- **OBSERVED（直接讀自 /tmp/stp-d1-scripts-lts 的實檔，逐檔 SHA256 如 §3 標題）**：orchestrate_v3_lts.sh、smoke.py、smokelib.py、wheelhouse.sha256、lts_prepare.sh。smoke.py／smokelib.py 另以 `cmp` 確認與舊目錄 /tmp/stp-d1-scripts 內同名檔逐位元相同。
- **RECONSTRUCTED（獨立路徑）**：從固定歷史 `D1_ENVIRONMENT_RESPONSE_20261012.md` 內 repair3 的 `orchestrate_v3.sh` 原文（取其最後一個「## 腳本：`orchestrate_v3.sh`」fence）＋ §4 的 sed 重建 LTS 版。比對結果：fence 原文與舊目錄 `orchestrate_v3.sh` 實檔 `==` 相同；重建出的 LTS 腳本 SHA256 = `bd6d85fd587797df2f5ab417f24833bdf621afac7928144515918cbd440b20c6`，與 OBSERVED 實檔 `cmp` 相同（RECONSTRUCTED_EQUALS_OBSERVED）。

## 2. 目錄清單、helper 引用與隱含依賴
回放用的腳本目錄（建議 `/tmp/stp-d1-scripts-lts`，或任何路徑並以 `STP_S` 指定）必須含以下 4 個提取檔：
| 檔案 | 被誰引用 | 來源 |
|---|---|---|
| orchestrate_v3_lts.sh | 入口（`verify`／`db ok`／`db inject`） | §3 FILE 區塊 |
| smoke.py | orchestrate 以 `$S/smoke.py` 呼叫 | §3 FILE 區塊（`import smokelib`，同目錄） |
| smokelib.py | smoke.py 同目錄 import | §3 FILE 區塊 |
| wheelhouse.sha256 | orchestrate `verify` 以 `sha256sum -c "$S/wheelhouse.sha256"` 核對 `$D/wheelhouse` | §3 FILE 區塊 |

task 目錄 `$D`（預設 `/tmp/stp-d1-lts`，或以 `STP_D` 指定）須含：`venv/`（Python 3.13，已離線安裝下列 5 個 wheel）與 `wheelhouse/`（5 個 wheel 檔）。**orchestrate_v3_lts.sh 不引用舊 /tmp/stp-d1-scripts 的任何檔案**（已 grep：該腳本內只有 `$D`／`$S` 路徑）。
**隱含舊路徑依賴只在 `lts_prepare.sh`**：它讀 `/tmp/stp-d1-env-r1/wheelhouse`（舊 Django 6.1.2 的 wheelhouse，取其 4 個依賴 wheel）與 `/tmp/stp-d1-scripts/wheelhouse.sha256`（舊清單），並含 Django 5.2.18 的下載步驟——因此 **lts_prepare.sh 不可作為乾淨回放的步驟，只作歷史參考**；乾淨回放用 §5 的 verify 流程。
五個 wheel（檔名／平台標籤／SHA256 以 `wheelhouse.sha256` 為準；cp313＝CPython 3.13，manylinux x86_64）：
```
fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094  asgiref-3.12.1-py3-none-any.whl
92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c  django-5.2.18-py3-none-any.whl
a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631  psycopg-3.3.6-py3-none-any.whl
cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269  psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f  sqlparse-0.6.0-py3-none-any.whl
```
**取得這些 wheel 需要下載授權：本包 NOT_AUTHORIZED_IN_THIS_PACKET**；不可假設 /tmp 快取永存（容器重啟即失）。前置：Python ≥3.12（觀察到 3.13.16，`PATH=/usr/bin:/bin`）、PostgreSQL 16 執行檔在 `/usr/lib/postgresql/16/bin`、系統有既存非 root 身分 uid 999（`claude`）、啟動者為 root（用 `setpriv` 降權）；不建立 OS 使用者、不使用 Docker／SQLite。

## 3. 完整可提取原文（逐位元；每個 FILE 標題的 SHA256 即該檔實檔 SHA256）
提取規則（§5）：以 `### FILE <name> sha256=<hex>` 標題＋緊接的 5 個反引號 fence 為界，內容逐字（含結尾換行）寫出並核 hash；hash 不符、缺區塊、語法檢查失敗皆非 0。

OBSERVED（本任務新寫的提取器，非舊 /tmp 檔）
### FILE extract_lts_replay.py sha256=3ab741011b23c5a231e94d97865dd4ba8570d4cad547e3a142cf7b5856c788b6
`````python
#!/usr/bin/env python3
"""從 D1_LTS_REPLAY_RESPONSE 的 `### FILE <name> sha256=<hex>` 區塊逐字提取檔案，核對 SHA256，並做語法檢查（bash -n／Python compile，不執行）。
用法：python3 extract_lts_replay.py <response.md> <output_dir>
只用標準函式庫；不連網、不讀環境值或 Secret、不執行被提取的腳本（只做 bash -n／compile）。
任何 SHA256 不符、區塊缺失或語法檢查失敗皆回傳非 0。"""
import hashlib, os, re, subprocess, sys

HEAD = re.compile(r"^### FILE (\S+) sha256=([0-9a-f]{64})$")
EXPECT = {"extract_lts_replay.py", "orchestrate_v3_lts.sh", "smoke.py", "smokelib.py", "wheelhouse.sha256", "lts_prepare.sh"}


def main(md, out):
    lines = open(md, encoding="utf-8").read().split("\n")
    os.makedirs(out, exist_ok=True)
    found, bad = {}, 0
    i = 0
    while i < len(lines):
        m = HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        name, want = m.group(1), m.group(2)
        i += 1
        if i >= len(lines) or not lines[i].startswith("````"):
            print(f"FAIL {name}: no fence after heading"); bad += 1; continue
        fence = re.match(r"`+", lines[i]).group(0)
        i += 1
        body = []
        while i < len(lines) and lines[i] != fence:
            body.append(lines[i]); i += 1
        i += 1                                   # skip closing fence
        data = ("\n".join(body) + "\n").encode("utf-8")
        got = hashlib.sha256(data).hexdigest()
        path = os.path.join(out, name)
        with open(path, "wb") as f:
            f.write(data)
        ok = got == want
        syn = "n/a"
        if ok and name.endswith(".sh"):
            syn = "bash -n exit %d" % subprocess.run(["bash", "-n", path]).returncode
            ok = syn.endswith("0")
        elif ok and name.endswith(".py"):
            try:
                compile(data.decode("utf-8"), path, "exec"); syn = "python syntax ok"      # 只編譯，不執行、不寫 .pyc
            except SyntaxError as e:
                syn = "python syntax FAILED: %s" % e; ok = False
        print(("OK  " if ok else "FAIL"), name, "sha256", got[:16] + "…", "expected", want[:16] + "…", "|", syn)
        bad += 0 if ok else 1
        found[name] = ok
    missing = EXPECT - set(found)
    if missing:
        print("FAIL missing blocks:", sorted(missing)); bad += 1
    print("RESULT:", "ALL_OK" if bad == 0 else "FAILED(%d)" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
`````

OBSERVED（讀自 /tmp/stp-d1-scripts-lts；另有 RECONSTRUCTED 對照，見 §1、§4）
### FILE orchestrate_v3_lts.sh sha256=bd6d85fd587797df2f5ab417f24833bdf621afac7928144515918cbd440b20c6
`````bash
#!/bin/bash
# D1 隔離環境編排 v3（fail-closed；管線不吞上游 exit；程序／TCP 查詢失敗保留資料；停止總次數 ≤2）。不下載任何東西：只使用既存 task venv／wheelhouse／PG16。
# 用法：orchestrate_v3_lts.sh verify            preflight＋離線安裝＋版本核對（不下載）
#       orchestrate_v3_lts.sh db ok|inject      私人 socket PG16 煙霧；每步依 exit／預期值裁定；cleanup 失敗不刪資料
# 結束碼：0 全部成功；1 某步驟失敗（或預期值不符）；7 注入模式且一切符合預期（煙霧注入失敗 exit 7、cleanup 正常）；9 cleanup 失敗（資料保留）
set -u
umask 077
D=${STP_D:-/tmp/stp-d1-lts}
S=${STP_S:-/tmp/stp-d1-scripts-lts}
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
PINS="Django==5.2.18 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0"
EXPECT_FREEZE=$'Django==5.2.18\nasgiref==3.12.1\npsycopg-binary==3.3.6\npsycopg==3.3.6\nsqlparse==0.6.0'

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
  [ $rc -eq 0 ] && [ "$ver" = "5.2.18 3.3.6" ] || { note_fail "import/version check failed: $ver"; return 1; }
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
`````

OBSERVED
### FILE smoke.py sha256=57743e2f523b7c99749b42a7a3cacec7eea1fc4f9f63cbc46fabf8ddce18f66b
`````python
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
`````

OBSERVED
### FILE smokelib.py sha256=4fec4db99867bd24429d1932eebdaeb56b480c6a8c9522e07ee91288c17fda0f
`````python
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
`````

OBSERVED
### FILE wheelhouse.sha256 sha256=86c8759e41fce785f5cea7f73c64844154ba5bbf3e07365101422906dad663dd
`````text
fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094  asgiref-3.12.1-py3-none-any.whl
92ed81d500be6408ecd704d7bd1366c534f30427bffcc63c5fefb129561aec7c  django-5.2.18-py3-none-any.whl
a1db9f7148b06a28606767efaca51fa6f9398c5c0a3810519be69d7000bdb631  psycopg-3.3.6-py3-none-any.whl
cec5ea900390897d0b46130f60bc2883bf19c314f9044235217c8be88b0ef269  psycopg_binary-3.3.6-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
b861c0288ce2fa56209a9a6412d2e066ac664b3873b89c26c9d8415e8e32996f  sqlparse-0.6.0-py3-none-any.whl
`````

OBSERVED（僅供歷史參考：含下載，本包 NOT_AUTHORIZED；另有隱含舊路徑依賴，見 §2）
### FILE lts_prepare.sh sha256=f605d1788f5821418bd8accb39907e82bc597577c7220f0bcce9f65087db78a4
`````bash
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
`````

## 4. 重建 LTS 腳本的 sed 與完整 diff（RECONSTRUCTED 路徑）
```bash
sed -e 's|/tmp/stp-d1-env-r1|/tmp/stp-d1-lts|; s|/tmp/stp-d1-scripts}|/tmp/stp-d1-scripts-lts}|; s|Django==6.1.2 psycopg==3.3.6|Django==5.2.18 psycopg==3.3.6|; s|\$'"'"'Django==6.1.2\\nasgiref|$'"'"'Django==5.2.18\\nasgiref|; s|"6.1.2 3.3.6"|"5.2.18 3.3.6"|; s|orchestrate_v3.sh|orchestrate_v3_lts.sh|g' orchestrate_v3.sh > orchestrate_v3_lts.sh
```
`diff orchestrate_v3.sh orchestrate_v3_lts.sh`（22 行；僅路徑、PINS／EXPECT_FREEZE／import 預期值、腳本名稱；diff 檔 SHA256 `c7144313fa7454d2230c913b4429055bf9eea49a29b16a5372ef77157d9556ad`）：
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
控制流程、exit 碼、安全邊界（pgrep 查詢失敗保留、總 `pg_ctl stop` ≤2、空 `listen_addresses`、socket 0700、非 root 降權、`/proc/net` TCP 掃描、`is_synthetic=true` 煙霧）皆在 `orchestrate_v3_lts.sh` 原文內，**本包未手改任何一行**。

## 5. 乾淨 checkout 的提取、核 hash、離線重建順序
以下為**說明**；步驟 1～2（提取與語法檢查）本任務已實際執行（結果見 §6）；步驟 3～6 需要既存 wheel 與 PG16，**本任務未執行**（NOT_RUN）。
1. 取得本檔（固定 result SHA 的 checkout），提取提取器並用它提取全部檔案：
```bash
D1=docs/platform/revisions/D1_LTS_REPLAY_RESPONSE_20261012.md
awk '/^### FILE extract_lts_replay.py /{f=1;next} f&&/^`````/{c++; if(c==2)exit; next} f&&c==1{print}' "$D1" > /tmp/extract_lts_replay.py
python3 /tmp/extract_lts_replay.py "$D1" /tmp/stp-d1-scripts-lts   # 逐檔核 SHA256＋bash -n／py_compile；任何不符非 0
```
2. `sha256sum /tmp/stp-d1-scripts-lts/*` 應與 §3 FILE 標題一致（提取器已核）。
3. （需要授權）把 5 個 wheel 放進 `$D/wheelhouse`（`D=/tmp/stp-d1-lts`），`( cd $D/wheelhouse && sha256sum -c /tmp/stp-d1-scripts-lts/wheelhouse.sha256 )` 必須全 OK。
4. 建 venv（root 啟動，降權成既有 uid 999）：`mkdir -p $D && chmod 700 $D && chown 999:999 $D`；`setpriv --reuid=999 --regid=999 --clear-groups env HOME=$D PATH=/usr/bin:/bin python3 -m venv $D/venv`。
5. 離線安裝（無網路）：`setpriv --reuid=999 --regid=999 --clear-groups env HOME=$D PATH=/usr/bin:/bin $D/venv/bin/pip --isolated --disable-pip-version-check install --no-input --no-index --find-links $D/wheelhouse --no-deps Django==5.2.18 psycopg==3.3.6 psycopg-binary==3.3.6 asgiref==3.12.1 sqlparse==0.6.0`。
6. `bash /tmp/stp-d1-scripts-lts/orchestrate_v3_lts.sh verify`（exit 0）→ `db ok`（exit 0）→ `db inject`（exit 7 為預期）。DB 只在 `$D/pgdata`、私人 socket `$D/sock`（0700，`listen_addresses=''`，無 TCP）；失敗時資料保留、結束碼 9；總停止次數 ≤2；全部命令不讀帳號設定或 Secret。
保留與失效：/tmp/stp-d1-lts（約 98 MB）與 /tmp/stp-d1-env-r1（Django 6.1.2，約 99 MB）皆為暫存，容器重啟後消失；本檔的原文與 hash 是重建的唯一依據。恢復界線：wheel 缺失時 `verify` 在 preflight 失敗（缺檔或 `wheelhouse sha256 mismatch`）並**不下載**，須由 GPT 另行授權取得 wheel。

## 6. 本任務實際執行的完整性檢查（只在 /tmp 隔離副本；未下載、未跑 DB／HTTP、未執行被提取的腳本）
以下為提交前、於本檔草稿（§1～§5 內容與最終版相同）上的結果；固定 result SHA 的乾淨 checkout 重跑結果見交付留言（OBSERVED）。
**(a) 提取器 bootstrap 與提取（exit 0）**：`awk` 取出的提取器與 §3 的 FILE 區塊逐位元相同（`cmp`）；`python3 extract_lts_replay.py <本檔> <out>`：
```
OK   extract_lts_replay.py sha256 3ab741011b23c5a2… expected 3ab741011b23c5a2… | python syntax ok
OK   orchestrate_v3_lts.sh sha256 bd6d85fd587797df… expected bd6d85fd587797df… | bash -n exit 0
OK   smoke.py sha256 57743e2f523b7c99… expected 57743e2f523b7c99… | python syntax ok
OK   smokelib.py sha256 4fec4db99867bd24… expected 4fec4db99867bd24… | python syntax ok
OK   wheelhouse.sha256 sha256 86c8759e41fce785… expected 86c8759e41fce785… | n/a
OK   lts_prepare.sh sha256 f605d1788f582141… expected f605d1788f582141… | bash -n exit 0
RESULT: ALL_OK
extract exit=0
```
**(b) 與 OBSERVED 原檔 `cmp`**：orchestrate_v3_lts.sh、smoke.py、smokelib.py、wheelhouse.sha256、lts_prepare.sh 對 /tmp/stp-d1-scripts-lts 內實檔皆 `cmp` 相同（無輸出差異）。
**(c) 提取器負向控制**（皆預期非 0；此為本任務新寫提取器的自我測試，AUTHOR_EVIDENCE）：
| 情境 | 實際 |
|---|---|
| 竄改 orchestrate 區塊 1 字元（hash 不符） | `FAIL orchestrate_v3_lts.sh sha256 … expected bd6d85fd…`，`RESULT: FAILED(1)`，exit 1 |
| 刪除 smokelib.py 區塊 | `FAIL missing blocks: ['smokelib.py']`，exit 1 |
| 區塊 hash 與內容相符但 Python 語法錯（`def (:`） | `FAIL smoke.py … python syntax FAILED: invalid syntax`，exit 1 |
**(d) RECONSTRUCTED 對照（§1）**：歷史 fence 原文 == 舊目錄實檔；sed 重建的 LTS 腳本 SHA256 = `bd6d85fd587797df2f5ab417f24833bdf621afac7928144515918cbd440b20c6` == OBSERVED（`RECONSTRUCTED_EQUALS_OBSERVED`）。
**(e) repo 必要檢查（追加本檔前的樹；皆 exit 0，stderr 空）**：
```
python3 docs/platform/examples/check_examples.py | exit=0 | OK: 1306 checks passed | stderr=0
python3 docs/platform/tools/gen_state_machines.py --check | exit=0 | OK: 6 state machines, 86 transitions, doc in sync | stderr=0
python3 docs/platform/tools/gen_permissions.py --check | exit=0 | OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync | stderr=0
python3 docs/platform/tools/test_checks.py | exit=0 | OK: test_checks 136 counterexample checks passed | stderr=0
python3 docs/platform/tools/check_docs.py | exit=0 | OK: 2133 doc checks passed | stderr=0
```
四份原始基線 `git diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 HEAD -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md` 為空；本 commit 只新增本檔。

## 7. 資源、保留與未證明
- 保留（皆 /tmp 暫存、容器重啟即失）：`/tmp/stp-d1-lts`（venv＋wheelhouse，約 98 MB）、`/tmp/stp-d1-env-r1`（Django 6.1.2，約 99 MB）、`/tmp/stp-d1-scripts`、`/tmp/stp-d1-scripts-lts`、`/tmp/stp-d1-replay`。本檔使重建不再依賴這些目錄的存續，但 **wheel 檔本身不在 repo 內**（不提交二進位）。
- 未做／未證明：未重跑 DB runtime（先前 LTS runtime 證據仍 AUTHOR_EVIDENCE，GPT 無 PG16／Django／psycopg，DB NOT_RUN）；wheel 下載 NOT_AUTHORIZED；Docker；Django 專案／migration／HTTP／360px；`lts_prepare.sh` 的下載步驟不屬回放。
- 外部呼叫：無；支出 0；真實資料無；Secret／CA 未讀；安裝／下載／部署／通知／merge 無；PR 維持 Draft。D1-A 仍 PREPARED，本包不是產品開工。AUTHOR_EVIDENCE，不自批。

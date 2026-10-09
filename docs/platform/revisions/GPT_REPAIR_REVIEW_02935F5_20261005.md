# R2 修補獨立覆核｜STP-PLATFORM-PLAN-001

日期：2026-10-05｜Reviewer：GPT／Codex｜裁定：**APPROVED（僅本次修補差異的 A/B 文件與參考邏輯層）**。
task_id：STP-PLATFORM-PLAN-001-R2-GPT-REPAIR-20261005；stage：R2_REPAIR_REVIEW。

## 固定版本與角色

| 欄位 | 值 |
|---|---|
| repo | firekou/SaveThePeople，公開 |
| 可信 base／origin/main | 9a7bd1295e20837786acc45bdab7fb94f5a1b012 |
| 原已審 R2 content | c1d56496bb210518314254b88d9c8b52e56408d9 |
| 修補起始 review_record／PR #1 head | 67e0c7998054a253267cf94d6dee9b76fded7062 |
| reviewed content／fixed result | **02935f528b42a35b3a793d1dec370a5091691288** |
| 結果分支 | claude/tender-allen-89joyz |
| 寫前結果分支 live ref | 與 fixed result 相同，實際 fetch exit0 |
| 協調與治理紀錄分支 | PR #1／claude/stp-platform-plan-001（main 為 PR base），Draft、open、unmerged |
| review_record_head | 本檔寫後以遠端 ref 與通知核對，不要求正文含自身 SHA |
| merge_candidate_head | NOT_DEFINED；PR #1 目前未包含此修補，不能把結果 SHA 当作 PR #1 head |
| executor | Claude，session_01PNBQLMHHDqYoqVg1sxmAm9 |
| reviewer | GPT／Codex，未製作這12檔修補，僅在隔離副本重現／蒐證及寫治理紀錄 |
| 人類參與 | 未觀察到本輪 Frank 新授權、法律或機構核定 |

授權依據：原 [GPT R2 差異覆核與有限修補包](https://github.com/firekou/SaveThePeople/blob/ce10895c121682797881e9f9d374f6ffdeeaa3e9/docs/platform/revisions/GPT_REVIEW_R2_20261005.md)，以及 [交付路徑調整](https://github.com/firekou/SaveThePeople/blob/67e0c7998054a253267cf94d6dee9b76fded7062/docs/platform/revisions/GPT_REPAIR_DELIVERY_ROUTE_20261005.md)。
claim：[5993520380](https://github.com/firekou/SaveThePeople/pull/1#issuecomment-5993520380)；交付：[5993571280](https://github.com/firekou/SaveThePeople/pull/1#issuecomment-5993571280)；[12檔實際差異](https://github.com/firekou/SaveThePeople/compare/67e0c7998054a253267cf94d6dee9b76fded7062...02935f528b42a35b3a793d1dec370a5091691288)。

Claude 明確確認交付路徑（ACKNOWLEDGED），已有修補 commit 與固定成果（STARTED／DELIVERED）。這輪已觀察到工單→claim→固定結果→Reviewer 的往返；不推論永久喚醒或所有未來交接都已驗證。

原claim起始11:35Z晚於留言時間，作者於交付更正為約11:28Z；commit／交付可觀察，實際投入分鐘數仍 REPORTED。deadline 2026-10-06T08:00:00Z，repair_round_limit=1／used=1（本次修補已交付）；90分鐘實際投入／外部成本0仍依作者報告，沒有獨立工時計量。沒有另派修補輪次或重置額度。

## 範圍與歷史核對

- c1d564…→67e0c7…只有三份 reviewer/controller 紀錄，不含未審產品／政策內容。
- 67e0c7…→02935f5…是一筆 commit、parent=67e0c7998054a253267cf94d6dee9b76fded7062，12檔全部是 F-01／03／07 的必要文件／參考邏輯／檢查／回覆：ARCHITECTURE、DATA_MODEL、RESOURCE_AND_ELIGIBILITY_ENGINE、USER_JOURNEYS、check_examples、engine_cases、ref_engine、state_machines、check_docs、prose_policy、test_checks、R2_REPAIR_RESPONSE。
- 四份原始基線與9a7bd…的 diff 空；permissions.json、R1_RESPONSE、R2_RESPONSE與三份GPT歷史紀錄相對67e0c7… diff --exit-code=0。未修改作者原證據或擴權。
- 本輪完整讀main README與四份基線；main AGENTS.md／CLAUDE.md／固定Controller帳本MISSING。閱讀必要平台修補差異、原 finding／工單、修補回覆與下一開工條件。不是重做全部歷史平台審查。
- API完整可取得PR7則留言／submitted reviews=[]；本輪未見競爭claim或新Frank決策。結果exact-head check-runs=0、statuses=[]（aggregate pending）、workflow_runs=0。沒有遠端CI成功證據。

## Findings 裁定

| Finding | 本輪判定 | 直接證據與驗收 |
|---|---|---|
| F-01 | **CLOSED／VERIFIED＋REPRODUCED** | ref_engine.py 238～256：已支援 ALL/ANY 節點逐層拒絕未知鍵；不支援op仍明確拒絕。原not:true反例現在NOT_RECOMMENDED/RULE_INVALID；獨立深層reviewer_forbidden鍵由具體訊息指出；合法巢狀ALL/ANY維持FORMAL。不是以崩潰作攔截。移除鍵檢查後原反例重新FORMAL且檢查exit1。 |
| F-03 | **CLOSED／VERIFIED（文件／權限政策）** | USER_JOURNEYS P9 196～204、ENGINE §8.2、ARCHITECTURE transitions API已人工判讀：只承諾資源層級摘要、不含逐案ID／家庭／進度；逐案工作留P7/P8的R3·ASG／R4·SITE-REV。permissions.json完全未變；原P9／engine／API矛盾文字置回時產生各自明確政策錯誤。沒有產品物件授權證據。 |
| F-07 | **CLOSED／VERIFIED＋REPRODUCED** | DATA_MODEL §2.4/§2.4.1/§3.1與ENGINE §0.2/§8.0、state_machines一致：只在NEEDS_RECHECK有當前起算日；RV-08/09/12/13離開即清除；歷史留AuditEvent。ref_engine.py 580～584拒絕非法狀態×欄位，753～775為欄位效果模擬。八種非複查狀態帶起算日均VERSION_INVALID；四離開轉換清除且不改原物件；錯來源／角色／日期按預期原因拒絕。 |
| F-02／04／05／06／08 | 維持上一輪文件／純邏輯層CLOSED | 未因本修補新增相應範圍變更；原20項Reviewer探針也重跑20/20符合。F-04仍不是備份整合驗收、F-08仍需人工語意判讀。 |

本次沒有新的阻擋 finding。F-07 舊 F07-published-ignores-stale-recheck-start 預期值由 FORMAL 改 VERSION_INVALID，與原獨立 finding 及本次選定的單一規範一致，不是用執行輸出反填正解。14天暫行門檻與D-311／D-312未啟用狀態不變。

prose_policy 是已知文字矛盾的啟發式回歸檢查，不是通用語意、物件權限或隱私證明。P9極小彙總件數可能再識別，顯示門檻未定；維持真實資料閘門，不擅自訂數值或擴成真實資料展示許可。
apply_version_transition 不驗全部業務前提，也未寫真實AuditEvent／DB；本次只驗欄位生命週期。日期、清除、AuditEvent與主狀態同一交易仍須產品與整合證據。

## 獨立執行證據

先讀腳本／依賴及全部修補程式差異：標準函式庫；check_docs子程序限本repo工具，未使用外部資料／服務。從固定02935f5以git archive建立 **stp-repair-review-02935f5** 隔離副本；作者checkout與遠端原實作不改。

實際Git命令（每項exit0）：
```text
git -C stp-review fetch origin refs/heads/main:refs/remotes/origin/main refs/heads/claude/stp-platform-plan-001:refs/remotes/origin/claude/stp-platform-plan-001
git -C stp-review fetch origin refs/heads/claude/tender-allen-89joyz:refs/remotes/origin/claude/tender-allen-89joyz
git -C stp-review rev-parse origin/main origin/claude/stp-platform-plan-001 origin/claude/tender-allen-89joyz
9a7bd1295e20837786acc45bdab7fb94f5a1b012
67e0c7998054a253267cf94d6dee9b76fded7062
02935f528b42a35b3a793d1dec370a5091691288

git -C stp-review diff 9a7bd1295e20837786acc45bdab7fb94f5a1b012 02935f528b42a35b3a793d1dec370a5091691288 -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md
stdout: 空
git -C stp-review diff --exit-code 67e0c7998054a253267cf94d6dee9b76fded7062 02935f528b42a35b3a793d1dec370a5091691288 -- docs/platform/permissions.json docs/platform/revisions/R1_RESPONSE.md docs/platform/revisions/R2_RESPONSE.md docs/platform/revisions/GPT_REVIEW_R2_20261005.md docs/platform/revisions/GPT_SESSION_TAKEOVER_20261005.md docs/platform/revisions/GPT_REPAIR_DELIVERY_ROUTE_20261005.md
stdout: 空
mkdir -p stp-repair-review-02935f5
git -C stp-review archive 02935f528b42a35b3a793d1dec370a5091691288 | tar -x -C stp-repair-review-02935f5
```

五項必要命令在該副本根目錄實際執行；以下是Reviewer subprocess實際stdout/stderr/exit，非複製作者自述：
```json
[
  {
    "command": "python3 docs/platform/examples/check_examples.py",
    "sha": "02935f528b42a35b3a793d1dec370a5091691288",
    "stdout": "OK: 942 checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/gen_state_machines.py --check",
    "sha": "02935f528b42a35b3a793d1dec370a5091691288",
    "stdout": "OK: 6 state machines, 86 transitions, doc in sync\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/gen_permissions.py --check",
    "sha": "02935f528b42a35b3a793d1dec370a5091691288",
    "stdout": "OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/test_checks.py",
    "sha": "02935f528b42a35b3a793d1dec370a5091691288",
    "stdout": "OK: test_checks 62 counterexample checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/check_docs.py",
    "sha": "02935f528b42a35b3a793d1dec370a5091691288",
    "stdout": "OK: 2009 doc checks passed\n",
    "stderr": "",
    "exit_code": 0
  }
]
```

原 Reviewer 探針命令：
`python3 stp_independent_probes.py stp-repair-review-02935f5`，exit0；20項20符合、0不符，原F-01與F-07的兩個不符已消除。探針來源全文見原GPT_REVIEW_R2附錄；此腳本是Reviewer蒐證，不是作者產品測試。

追加獨立Python inline探針（`python3 - <<'PY'`，import ref_engine／prose_policy，全部在深拷貝操作），exit0；22項22符合。預期值依原finding／選定規範獨立指定。方法：CUSTOM深層增加reviewer_forbidden鍵，核對具體rule_problems與RULE_INVALID，再刪鍵作合法控制；八種非複查status＋起算日逐一測推薦入口；對RV-08/09/12/13逐一呼叫apply_version_transition並比對新狀態、清除與原物件；錯來源／角色／日期核對錯誤原因；將三处原P9承諾置回深拷貝文字核對prose_policy具体診斷。
```json
[
  {
    "probe": "F01 deep unknown key reason",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "RULE_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "RULE_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F01 reason names deep key",
    "actual": true,
    "expected": true,
    "matches": true
  },
  {
    "probe": "F01 nested legal control",
    "actual": {
      "status": "FORMAL",
      "reasons": []
    },
    "expected": {
      "status": "FORMAL",
      "reasons": []
    },
    "matches": true
  },
  {
    "probe": "F07 stale start CANDIDATE",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start DRAFT",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start IN_REVIEW",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start PUBLISHED",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start SUSPENDED",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start SUPERSEDED",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start EXPIRED",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 stale start RETIRED",
    "actual": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "expected": {
      "status": "NOT_RECOMMENDED",
      "reasons": [
        "VERSION_INVALID"
      ]
    },
    "matches": true
  },
  {
    "probe": "F07 clear RV-08",
    "actual": [
      "PUBLISHED",
      null,
      "2026-09-01"
    ],
    "expected": [
      "PUBLISHED",
      null,
      "2026-09-01"
    ],
    "matches": true
  },
  {
    "probe": "F07 clear RV-09",
    "actual": [
      "SUSPENDED",
      null,
      "2026-09-01"
    ],
    "expected": [
      "SUSPENDED",
      null,
      "2026-09-01"
    ],
    "matches": true
  },
  {
    "probe": "F07 clear RV-12",
    "actual": [
      "SUPERSEDED",
      null,
      "2026-09-01"
    ],
    "expected": [
      "SUPERSEDED",
      null,
      "2026-09-01"
    ],
    "matches": true
  },
  {
    "probe": "F07 clear RV-13",
    "actual": [
      "EXPIRED",
      null,
      "2026-09-01"
    ],
    "expected": [
      "EXPIRED",
      null,
      "2026-09-01"
    ],
    "matches": true
  },
  {
    "probe": "F07 specific error wrong source state",
    "actual": true,
    "expected": true,
    "matches": true
  },
  {
    "probe": "F07 specific error actor not allowed",
    "actual": true,
    "expected": true,
    "matches": true
  },
  {
    "probe": "F07 specific error requires an ISO-date",
    "actual": true,
    "expected": true,
    "matches": true
  },
  {
    "probe": "F03 prose baseline",
    "actual": [],
    "expected": [],
    "matches": true
  },
  {
    "probe": "F03 original P9 promise detected",
    "actual": true,
    "expected": true,
    "matches": true
  },
  {
    "probe": "F03 original engine promise detected",
    "actual": true,
    "expected": true,
    "matches": true
  },
  {
    "probe": "F03 original API promise detected",
    "actual": true,
    "expected": true,
    "matches": true
  }
]
```

人為破壞在另外三個TemporaryDirectory隔離副本進行，原固定副本不改；外層Python檢驗每次子檢查exit1且包含**預期失敗標籤與結果差異**，外層exit0：
```json
[
  {
    "mutation": "F01 remove unknown-key guard",
    "command": "python3 docs/platform/examples/check_examples.py",
    "exit_code": 1,
    "expected_exit": 1,
    "expected_failure_label": "F01-root-unknown-key-not",
    "matching_failure_lines": [
      " - illegal expression F01-root-unknown-key-not: want {'status': 'NOT_RECOMMENDED', 'reasons': ['RULE_INVALID']} got {'status': 'FORMAL', 'reasons': []}",
      " - F01-root-unknown-key-not reported as ValidationError: want True got False",
      " - F01-root-unknown-key-not names the unknown key: want True got False"
    ],
    "caught_for_expected_reason": true
  },
  {
    "mutation": "F07 remove state-field guard",
    "command": "python3 docs/platform/examples/check_examples.py",
    "exit_code": 1,
    "expected_exit": 1,
    "expected_failure_label": "F07-published-with-stale-recheck-start-rejected",
    "matching_failure_lines": [
      " - recommendation F07-published-with-stale-recheck-start-rejected: want {'status': 'NOT_RECOMMENDED', 'reasons': ['VERSION_INVALID']} got {'status': 'FORMAL', 'reasons': []}"
    ],
    "caught_for_expected_reason": true
  },
  {
    "mutation": "F07 remove clearing effect",
    "command": "python3 docs/platform/examples/check_examples.py",
    "exit_code": 1,
    "expected_exit": 1,
    "expected_failure_label": "RV-08 clears start",
    "matching_failure_lines": [
      " - RV-08 clears start: want ['PUBLISHED', None] got ['PUBLISHED', '2026-09-01']"
    ],
    "caught_for_expected_reason": true
  }
]
```

## 已證明與未證明

A/B：本修補差異APPROVED；既有F-01～F-08在所審文件／參考模擬範圍全部關閉。本報告不是整份平台重新全面批准，也不是PR #1全部candidate的merge批准。
C產品／DB、D產品合成E2E、E真實初篩、F真實案件服務、G實際取得及第二人驗證均NOT_VERIFIED／未驗收。G1～G8、AS-1～AS-6沒有本次通過證據，U-23法律／備份可接受性仍未確認。
沒有新增合作、人員到任、政策查核、真實家庭、送件、核准或取得證據。純參考模擬與正式資格核定分開。

## 下一checkpoint與具體決策包

本修補checkpoint：**COMPLETE**。沒有新增已授權READY實作工作；不派第二次修補。結果尚未整合PR #1／main，工程開工仍不成立。

**唯一眼前問題：Frank是否授權將已獨立通過的02935f5這12檔修補，以保留歷史、non-force方式整合進PR #1候選分支，仍維持Draft、不合併main、不開工？**
- 建議：授權此有限候選整合；它能讓PR #1真正包含已審修補，消除目前「結果已審但PR仍是舊內容」的落差。
- 放行範圍：仅本報告已審12檔修補；完整保留Claude原commit、GPT報告與歷史，沿同一work_id。作者程式不由GPT再改寫。可採保留歷史的一般候選分支整合；不可force／squash掉原證據。
- 未授權事項：main merge、auto-merge、產品開工、部署、真實資料、對外操作與支出全部排除。若只批准整合，不能擴解成上述許可。
- 成本／風險：外部成本0；只做repo規劃／合成參考差異整合。風險是版本並行或未知衝突；寫前重查main／PR／result／claim，未知差異即停，不自行解含新語意的衝突。
- 時間：原修補已在deadline前交付，不延長原工單；後續整合若获授權，由Controller具體化新的有界工作包與UTC期限，不虛構已核准期限。
- 停止／恢復：無明確授權就保持現狀；收到涵蓋範圍與策略的有效授權、版本與scope核對通過後續作，整合後重讀candidate與差異再裁定。不要求Frank返回原session。
- next_actor：Frank（候選整合授權）；GPT完成本次覆核後等待有效授權／新證據。Claude本次修補已交付。

第一批次BATCH1_EXECUTION_PACK仍寫「已備妥，本輪不開工」。啟動條件逐項：
| 條件 | 本次證據／狀態 |
|---|---|
| 獨立規劃批准 | 本次A/B修補差異APPROVED；整體開工放行未成立，不將局部裁定默認全面批准 |
| 工程人力D-307 | 未決；無本輪人員配置決策 |
| 技術D-201 | Django＋PostgreSQL＋HTMX推薦且可逆；無本輪開工選型確認 |
| 開發環境 | 文件建議本機Docker Compose；實際環境／DB能力NOT_VERIFIED |
| 合成規範 | 現有合成examples可讀／檢查重現；staging拒非合成個案尚無產品證據 |
| repo存取／分支規則 | 此次有限修補結果分支可交付已驗證；第一批次工程規範仍待指定，不能泛化成部署或全工程許可 |

D1（WP-00～03）→D2（WP-04）→D3（WP-05～06）→D4（WP-07／08a）仍為候選順序；47～68與107～161人日仍是規劃估算，不是支出或工期承諾。

## 目標藍圖對齊與意義

有效goal（main README v0.1，2026-10-03）：**讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。**

方向：**前進**。原先三個缺口已由独立重現關閉，交付限制也已有固定成果往返證據；下一步是受控候選整合與開工條件核對。服務P0～P3無新增真實成果，90天起算日未確認；工程D1～D4尚未開工。
可信能力增加在「規劃矛盾能被具體檢查與有限修補關閉」，不是家庭已取得福利。距離實際取得仍需工程／DB、服務閘門、資源查核、合作據點、人力與真實結果驗證。

現在：Claude〔固定修補已交付〕；GPT〔本次修補差異APPROVED，候選整合待授權〕；Frank〔決定是否授權上述12檔整合到PR #1候選，不含main合併與開工〕。

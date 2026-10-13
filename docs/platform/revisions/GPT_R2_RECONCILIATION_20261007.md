# R2 剩餘缺口核對與整合準備

日期：2026-10-07（Asia/Taipei）。Reviewer：GPT。Verdict：CHANGES_REQUESTED。

## 固定座標與範圍

- main/base：9a7bd1295e20837786acc45bdab7fb94f5a1b012。
- PR #1 live：af19c9983620ed248de5e13196162a16297aed21，open、Draft、未合併。
- Claude 修補：02935f528b42a35b3a793d1dec370a5091691288。
- 已實際讀取／測試修補 head：02935f528b42a35b3a793d1dec370a5091691288。
- 本機整合候選：50d2c56ac1e223dc2afdfe50f17e4ffb9fea6c75，保留兩個 parent，合併無衝突。
- 本輪核對先前 N-01～N-06；不是重做全平台覆核，不把另一份報告的 F 編號當成 N 編號。
- af19 相對 67e0c7 僅新增 GPT_REPAIR_REVIEW_02935F5_20261005.md。12 檔修補可無衝突併入，Reviewer 歷史檔案保留。
- 本輪未推送、未改遠端 PR 分支、未合併 main、未新增產品或部署。

## 結果

| ID | 嚴重度 | 結論 | 檔案與段落、直接證據及修正 |
|---|---|---|---|
| N-01 | MAJOR（已解決） | 已解決 | ref_engine.py::_expr_problems；CUSTOM ALL 節點加入 unseen_semantics 後 recommendation_status 回 NOT_RECOMMENDED/RULE_INVALID。遞迴未知鍵防護已補入。 |
| N-02 | MAJOR | 未解決 | ref_engine.py::where_problems/eval_criterion，ENGINE §5.2；where.in_school=false 合法但被 truthiness 判斷略過。H1 年齡 0～17、min_count=2 得 PASS/count=2；其中 8 歲成員在學未知仍得 PASS。規格須定義 false：支援「不在學」或明確拒絕，不能當作未設定。若採不在學，預期 count=1／FAIL_UNCONFIRMED，未知案例為 UNKNOWN。 |
| N-03 | MAJOR | 未解決 | OPERATIONS §1.3.3 還原步驟 3；ref_control.py::Witness/request_control/recover。文件稱獨立見證「定期」更新，參考實作同步更新。模擬定期更新尚未 flush：撤回寫入後主庫失敗回202，再遺失控制尾端，還原回 quarantined=false，通知仍 SCHEDULED、轉介仍 SENT。原同步 Witness 正確維持隔離。這是文件所允許時序的注入反例，不是宣稱同步原實作本身失敗。須定義確認前持久見證、水位失效與未確認狀態的 fail-closed 規則，加對應故障案例。 |
| N-04 | MINOR | 未解決 | gen_permissions.py::policy_problems；permissions.json::verify API/P9/resource_internal.R4；state_machines.json::RV-14。verify note 改成責任人／登錄人可驗證仍 policy_problems=[]。P9 稱 R4 可暫停／停用，但矩陣 R4 僅 RV-09/10，RV-14 僅 R5/R7。補結構化驗證排除與轉換允許清單、衍生文字；不能擴權解決。 |
| N-05 | MINOR | 未解決 | OPERATIONS §1.3.3 ControlRecord 定義；schemas/control_record.schema.json；ref_control.py::ControlLog.append。僅 type=CONSENT_REVOKE 通過 schema；文件要求 consent_id/seq/prev_hash/recorded_at 卻被 schema 視為未知鍵。定義 envelope/payload，統一欄位，依動作要求必要欄位，同步案例与模擬。 |
| N-06 | MINOR | 部分解決 | ARCHITECTURE §6「權限矩陣每格都有自動化測試」、BUILD §4.2「文件之間自洽」、R2_RESPONSE 各節「完成」、GPT_REPAIR_REVIEW 的全面 CLOSED 延伸聲明仍過寬。新報告對純模擬／非產品的限制已改善，但本次反例表明全關閉聲明不能沿用。保留歷史，以新狀態報告更正並收窄現行聲明。 |

原最新報告的 F-01/F-03/F-07 修補成果不因本核對被抹除；「本次12檔差異通過」與「所有先前缺口均已关闭」是不同命題。後者受到本次 N-02～N-05 證據否定。

## 實際執行

在固定02935f5隔離副本跑五工具與 reconcile_probe.py；在50d2c56整合候選再跑五工具與四基線 diff。結果見附錄 JSON。全部五工具 exit0、基線 diff 空。這只能證明既有檢查覆蓋項目通過，不能否定新反例。

git merge-tree --write-tree af19c9983620ed248de5e13196162a16297aed21 02935f528b42a35b3a793d1dec370a5091691288
stdout：2f7ea90d3f4d52e9ace59f66819aa68c7ef7545b；exit0、無衝突。

本機一般 merge 保留 Claude commit 與 GPT 覆核紀錄，候選50d2c56。它是整合準備，不是批准或公開發布。

## 下一步

Claude 僅修 N-02～N-06，交回 fixed head；GPT 按 exact head 重現新反例並覆核。通過後再決定更新 PR #1 候選。第一批網站工程未啟動。本輪没有发出远端工单或验证 Claude 已接单。

## 整合候選命令輸出

```json
[
  {
    "command": "python3 docs/platform/examples/check_examples.py",
    "stdout": "OK: 942 checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/gen_state_machines.py --check",
    "stdout": "OK: 6 state machines, 86 transitions, doc in sync\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/check_docs.py",
    "stdout": "OK: 2032 doc checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/gen_permissions.py --check",
    "stdout": "OK: permissions policy (25 classes, 143 matrix cells, 42 API, 12 pages), docs in sync\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "python3 docs/platform/tools/test_checks.py",
    "stdout": "OK: test_checks 62 counterexample checks passed\n",
    "stderr": "",
    "exit_code": 0
  },
  {
    "command": "git diff origin/main -- docs/PROJECT_BLUEPRINT.md docs/EXECUTION_PLAN.md docs/SERVICE_MODEL.md docs/DATA_AND_PRODUCT_SPEC.md",
    "stdout": "",
    "stderr": "",
    "exit_code": 0
  }
]
```

## 固定修補反例實際輸出

```json
{
  "N-01 unknown node key": {
    "status": "NOT_RECOMMENDED",
    "reasons": [
      "RULE_INVALID"
    ]
  },
  "N-02 false filter": {
    "result": "PASS",
    "derived": {
      "count": 2
    },
    "missing": [],
    "human_trigger": false
  },
  "N-02 unknown school": {
    "result": "PASS",
    "derived": {
      "count": 2
    },
    "missing": [],
    "human_trigger": false
  },
  "N-03 Witness": {
    "request": [
      202,
      "RECORDED_PENDING_APPLY"
    ],
    "quarantined": true,
    "reason": "LOG_INCOMPLETE:last=0<witness=1",
    "notification": "SCHEDULED",
    "referral": "SENT"
  },
  "N-03 PeriodicWitness": {
    "request": [
      202,
      "RECORDED_PENDING_APPLY"
    ],
    "quarantined": false,
    "reason": null,
    "notification": "SCHEDULED",
    "referral": "SENT"
  },
  "N-04 baseline policy": [],
  "N-04 self verification note mutation": [],
  "N-04 P9": [
    {
      "page": "P9",
      "title": "資源維護、查核與版本管理",
      "sections": [
        {
          "label": "頁面",
          "class": "resource_internal",
          "action": "V",
          "grants": [
            "R5·INT",
            "R4·INT",
            "R7·INT",
            "R9·INT"
          ],
          "note": "R5 可編輯與發布（發布人≠查核人）；R4、R7 僅可暫停／停用；R9 唯讀；個案內容一律不可見"
        }
      ]
    }
  ],
  "N-05 incomplete control": [],
  "N-05 documented envelope fields": [
    "$: unknown key 'consent_id'",
    "$: unknown key 'seq'",
    "$: unknown key 'prev_hash'",
    "$: unknown key 'recorded_at'"
  ]
}
```

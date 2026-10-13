# 合成範例資料與可執行規格
**本資料夾全部為合成資料（SYNTHETIC）。** 「示範縣」與所有資源、機構、家庭、門檻皆為虛構，網址使用保留的 `example.invalid` 網域。不得作為任何真實資格判斷依據，也不得加入真實個案。

| 檔案 | 內容 | 用途 |
|---|---|---|
| [synthetic_resources.json](synthetic_resources.json) | 6 項資源（含 1 項已過期、1 項期限未知且名額已滿的民間資源）、6 個來源、2 種家庭口徑 | 目錄匯入（WP-03）、引擎測試（WP-04） |
| [synthetic_households.json](synthetic_households.json) | 7 個家庭：口徑差異（H1）、全部不知道（H2）、自述不符與接近門檻（H3）、併領排除（H4）、成員事實未知（H5）、資料不足＋已確認不符（H6）、資料不足＋自述不符（H7）；成員屬性以含確認程度的 Fact 表示 | 測試情境 T-01～T-09、T-26～T-31 |
| [expected_assessments.json](expected_assessments.json) | 每個家庭 × 每項資源的預期結果、逐條條件、旗標、正式推薦狀態（**手算**，不是複製 runner 輸出） | 引擎驗收基準 |
| [expected_assessments.md](expected_assessments.md) | 上列 JSON 的可讀表格（由程式產生，勿手改） | 人工覆核 |
| [engine_cases.json](engine_cases.json) | 組合語意 18 案、無效規則 19 案、正式推薦判定 59 案（含複查寬限與版本欄位一致性）、口徑範圍 26 案、條件結構 42 案、非法條件與運算式變體 12 案、取得成果計數 9 情境、申請建立／送件前檢查／補件生命週期 24＋17＋2 案、冪等重播 5 案、回呼處理 7 情境 | T-21～T-31、T-39～T-47、T-55、T-57～T-60 |
| [ref_control.py](ref_control.py)、[control_cases.json](control_cases.json) | **純邏輯模擬**：先寫外部控制紀錄、失敗處理、還原後重新套用、水位與隔離、HARD_DELETE／REDACT 驗證差異（12 情境）。**不是資料庫、物件儲存或備份整合演練** | T-52～T-54 |
| [ref_engine.py](ref_engine.py) | 參考實作（非產品程式碼，只用標準函式庫） | 讓規格可被一致實作 |
| [check_examples.py](check_examples.py) | 執行全部檢查；`--write-md` 重新產生 md | 驗證規格本身 |

## 執行
```bash
python3 docs/platform/examples/check_examples.py            # 預期最後一行：OK: N checks passed
python3 docs/platform/tools/check_docs.py                   # 文件一致性
python3 docs/platform/tools/gen_state_machines.py --check   # 狀態機文件與 JSON 同步
python3 docs/platform/tools/gen_permissions.py --check      # 權限矩陣／API／頁面與 permissions.json 同步＋政策檢查
python3 docs/platform/tools/test_checks.py                  # 檢查工具的反例測試（刻意違規的資料必須被抓到）
```
任一檢查失敗 exit code 為 1。

## runner 的支援與不支援範圍
- **支援**：運算子 `EQ NEQ LT LTE GT GTE BETWEEN IN NOT_IN EXISTS REGION_IN COUNT_MEMBERS_WHERE NOT_RECEIVING HUMAN_JUDGMENT`；組合 `ALL`、`ANY`、`CUSTOM`（巢狀 ALL／ANY）；成員口徑（含未知成員事實→UNKNOWN）；正式推薦判定；取得事件計數；申請建立規則；回呼套用；Idempotency-Key 語意。
- **口徑與條件的鍵是封閉集合**：未知鍵、未支援鍵（口徑的 `age_between`、`in_school`、`military_service`、`exclusions`、年度所得期間、推估所得；`COUNT_MEMBERS_WHERE` 的非年齡就學條件）、型別錯誤一律報錯，不會默默忽略（引擎 §5.3）。
- **不支援，遇到即報錯（有測試）**：運算子 `AGE_BETWEEN`、`DATE_WITHIN`；區間值輸入 `{"min","max"}`；組合 `NOT`、`N_OF_M` 及其他未知組合；`min_confirmation_for_fail` 為 C1（自述不能確認不符合）；未定義 scope；缺 `evidence_level` 的取得事件。
- 資料格式為簡化版（例如成員歲數直接給整數）；正式實作以 [DATA_MODEL_AND_STATE_MACHINES.md](../DATA_MODEL_AND_STATE_MACHINES.md) 與 [RESOURCE_AND_ELIGIBILITY_ENGINE.md](../RESOURCE_AND_ELIGIBILITY_ENGINE.md) 為準。

## 防止「測試太寬鬆」
預期值由規格作者依規則手算（不是複製 runner 輸出）。檢查程式另外強制不變條件：含 UNKNOWN 的條件結果永遠是資料不足、資料不足永不顯示為不符合；預期值則覆蓋「自述不能產生已確認的不符合」與「未知成員不被默默排除」。第一輪（v0.2-draft）的檢查程式沒有覆蓋這些情況；R1 修正時另以三種人為破壞（把 UNKNOWN 優先序改成 FAIL 優先、允許 C1 確認不符合、丟掉未知成員）各自確認檢查會失敗，結果記錄於 [revisions/R1_RESPONSE.md](../revisions/R1_RESPONSE.md)。

R2 補充：R1 的自我檢查沒有覆蓋這些反例，GPT 覆核才發現——(1) 規則第一個條件之後出現的非法條件、非法 CUSTOM 運算式、缺 `rule.status`，在舊版 `recommendation_status` 仍為 FORMAL；(2) 口徑含 `age_between` 時被默默忽略而計入所有成員；(3) 權限一致性檢查只比對字串前綴；(4) AP-06 的防重複會擋掉合法的補件。R2 為每一項加入「若原缺陷存在就會失敗」的回歸檢查，並以人為破壞（例如把缺 `status` 預設回 PUBLISHED、讓未支援鍵再次被忽略、讓驗證在未知口徑時吞掉例外）確認它們會失敗；結果與限制記錄於 [revisions/R2_RESPONSE.md](../revisions/R2_RESPONSE.md)。這些是文件與純邏輯模擬層級的檢查，不代表產品行為或資料庫整合已被驗證。

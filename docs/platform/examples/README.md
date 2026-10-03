# 合成範例資料
**本資料夾全部為合成資料（SYNTHETIC）。** 「示範縣」與所有資源、機構、家庭、門檻皆為虛構，網址使用保留的 `example.invalid` 網域。不得作為任何真實資格判斷依據，也不得加入真實個案。

| 檔案 | 內容 | 用途 |
|---|---|---|
| [synthetic_resources.json](synthetic_resources.json) | 6 項資源（含 1 項已過期、1 項名額已滿的民間資源）、6 個來源、2 種家庭口徑 | 第一批次資源目錄匯入（WP-03）、規則引擎測試（WP-04） |
| [synthetic_households.json](synthetic_households.json) | 4 個家庭：口徑差異、全部不知道、自述接近門檻與地區不符、併領排除 | 測試情境 T-01～T-09 |
| [expected_assessments.json](expected_assessments.json) / [.md](expected_assessments.md) | 每個家庭 × 每項資源的預期結果、逐條條件、旗標 | 引擎驗收基準 |
| [check_examples.py](check_examples.py) | 參考檢查程式（非產品程式碼，只用標準函式庫）：參照完整性＋依規格計算並比對預期 | 驗證規格本身可被一致實作 |

執行：
```bash
python3 docs/platform/examples/check_examples.py
```
預期最後一行輸出 `OK: all synthetic expectations match`。

資料格式對應 [DATA_MODEL_AND_STATE_MACHINES.md](../DATA_MODEL_AND_STATE_MACHINES.md) 與 [RESOURCE_AND_ELIGIBILITY_ENGINE.md](../RESOURCE_AND_ELIGIBILITY_ENGINE.md) §5～§7；此處為簡化版（例如成員年齡直接給數值、成員屬性視為自述 C1），正式實作以規格為準。

# 資源資料規格 v1（P1-1）

版本：v1-draft｜2026-10-18｜作者：Claude Sonnet 5.5｜待覆核：Opus（依 PLAN_v1 §4）
依據：`docs/DATA_AND_PRODUCT_SPEC.md` §2 為準；本文件不修改基線。機器可讀版本：`schema/resource.schema.json`。

## 1. 與基線 §2 最低欄位的對照

基線列出 22 項最低欄位。下表逐項對應，沒有遺漏。

| 基線 §2 欄位 | schema 欄位 | 說明 |
|---|---|---|
| resource_id | `resource_id` | 中央 `C-nnn`；地方 `L-縣市碼-nnn`；民間 `P-nnn` |
| 名稱 | `name` | |
| 提供機構 | `provider` | |
| 中央／地方／民間 | `level` | 列舉：中央、地方、民間 |
| 適用地區 | `regions` | 全國寫 `["全國"]` |
| 需求類別 | `need_categories` | 對應藍圖 §4 的七類，見 §3 |
| 服務內容 | `service_content` | 用來源用語，不補充 |
| 資格條件 | `eligibility[]` | 每條一筆，見 §2 |
| 例外／排除／併領條件 | `exclusions_cumulation[]` | 同樣要逐字摘錄或標「未知」 |
| 家庭計算口徑 | `household_calculation_basis` | **每個方案各自記錄**，不統一口徑（基線 §2） |
| 有效期間 | `validity_period` | 來源未載明寫「未知」 |
| 申請期限 | `application_deadline` | 同上 |
| 文件 | `documents[]` | |
| 申請方式 | `application_method` | |
| 窗口 | `contact` | 只放機構層級的公開窗口，不放個人資料 |
| 來源 URL | `source_url` | 必須是實際讀取過的頁面 |
| 來源發布／更新日期 | `source_published_date` | 頁面沒標示寫「未標示」 |
| 最後查核日期 | `last_checked_date` | YYYY-MM-DD |
| 查核人 | `checked_by` | 桌面蒐集者。人工現場查核人於 P1-4 另填 |
| 版本 | `version` | 例 `v1-2026-10-18` |
| 有效狀態 | `status` | 四種，見 §4 |
| 量能確認 | `capacity_confirmation` | 候選階段一律「未確認」 |

另加一欄 `uncertainty_notes[]`，記錄所有疑慮。這是 PLAN_v1 §1.3 第 6 點「標明不確定性」的落點。

## 2. 資格條件：逐字摘錄規則

基線 §2：「每項資格條件記錄所需輸入、資料來源、判斷方法及人工確認點」。PLAN_v1 P1-1 另要求每個資格欄位有「來源原文摘錄＋定位」。因此 `eligibility[]` 每筆都有：

| 欄位 | 內容 |
|---|---|
| `condition_id` | 資源內唯一編號 |
| `value` | `已摘錄`：`source_excerpt` 是來源原文。`未知`：來源沒寫或無法對應，`source_excerpt` 留空 |
| `source_excerpt` | **逐字**複製的連續原文。不改寫、不合併句子、不補全、不推論 |
| `source_locator` | 條號、章節或頁面標題 |
| `required_input` | 判斷這條需要家庭提供什麼資訊 |
| `data_source` | 該資訊的來源（自述、文件、承辦確認） |
| `judgment_method` | 規則比對或人工判斷 |
| `manual_confirm_point` | 必須由人確認之處 |

規則：
1. 資料不足寫「未知」，不是「不符合」（原則 1）。
2. 金額、門檻若由地方政府每年公告，頁面沒有數字就寫「未知」，並在 `manual_confirm_point` 寫明要向誰確認。
3. 模型不得把摘錄改寫成規則。進入規則編碼（P1-5）的欄位必須是「已查核」資源中的 `已摘錄` 欄位。

## 3. 需求類別

`生活/急難救助`、`兒少/就學`、`食物/物資`、`居住`、`就業`、`醫療/健康`、`必要支持服務`。前五類對應藍圖 §4 的資源範圍；其餘兩類為涵蓋醫療與支持服務而加，若 Frank 認為不需要可刪除。

## 4. 有效狀態

| 狀態 | 意義 | 可否正式推薦 |
|---|---|---|
| 候選 | 桌面蒐集，未經人工查核 | **不可** |
| 已查核 | 人工查核人確認來源、窗口與量能，另一人抽查 | 可 |
| 暫停 | 來源失效、內容衝突或期限不明 | 不可（基線 §5） |
| 過期 | 已逾有效期間 | 不可 |

本批所有候選資源全部是「候選」。tools 會拒絕任何非候選狀態（`tools/validate_resources.py`）。

## 5. 版本化

額度、門檻與地區規則必須記錄在資料檔裡並隨 `version` 更新，不寫死在模型提示中（基線 §2）。更新流程沿用基線 §5：偵測變動 → 標記受影響資源 → 人工查核 → 發布新版本。

## 6. 工具

```
python3 tools/validate_resources.py      # 欄位、列舉、候選狀態檢查
python3 tools/verify_excerpts.py          # 重新抓取來源，檢查每段摘錄是否為逐字子字串
python3 tools/fetch_text.py URL           # 取得網頁可見文字
```

`verify_excerpts.py` 需要網路。檢查時忽略空白差異，其餘必須完全一致。這只能證明「摘錄確實出現在該頁」，不能證明該頁是最新、正確或適用於特定家庭，這些仍需人工查核。

## 7. 與 PLAN_v1 的差異（請覆核者留意）

- 候選檔用 JSON（`data/resources/candidates/*.json`），不是 PLAN_v1 P1-3a 寫的 YAML。原因：本機環境沒有 YAML 解析器，用 JSON 才能自動驗證。若要改 YAML，轉換是機械工作。
- 「JSON Schema」`schema/resource.schema.json` 是規格文件；`tools/validate_resources.py` 只實作其中的必填、列舉與格式檢查，不是完整的 JSON Schema 驗證器。

# D1-A 啟動指示轉錄與 claim
本檔是 Frank 指示下的 GPT 執行決策之轉錄，由 Claude 執行端記錄。不是 Claude 自行批准，不是獨立覆核，不是產品驗收。

## 身分與座標
- work_id：STP-PLATFORM-PLAN-001；task_id：STP-PLATFORM-PLAN-001-D1-A-CATALOG；stage：D1_A。
- 執行 session：session_01U1KQKyyLgpjSHBhBLGqRq6（本次排程／指示喚醒；與先前 D1 文件輪 session 不同，不冒充）。
- base／main：9a7bd1295e20837786acc45bdab7fb94f5a1b012（git fetch origin exit 0 後讀取）。
- 候選 head（claude/stp-platform-plan-001）：3e0bd9999e62787636843d8fe054e732b3f62305（與指示一致）。
- 上一作者內容（claude/tender-allen-c9p5u1）：d755256040b1fb8ff5c3a6a48d2be3b7afd6f0c5（已包含於候選 head 歷史）。
- 本次結果分支：claude/relaxed-maxwell-q2b86k（本 session 平台指定且允許推送）。以 non-force merge 將候選 head 3e0bd99 併入，保留候選與作者祖先；merge commit：00d40863452f1dbfa0c1eb8a100674ded6ffc797。不推 main。
- 既有產品結果核對：三個遠端分支與候選 head 皆無 product/ 目錄；先前 D1 輪次只有環境／LTS 文件與腳本證據，沒有可重用的產品程式。本次從零建立 product/，不重做已通過的文件成果。

## 指示摘要（授權範圍）
允許：本機隔離環境的產品程式、測試與示範；安裝必要開源依賴；建立本機測試資料庫；暫時啟動僅 loopback 可存取的網站；使用既有合成資料；推送功能分支、更新 Draft PR、回寫 PR #1。
不包含：公開部署、雲端資源、新費用、真實個案、外部 AI、通知發送、政府 API、申請送件、對外聯絡、讀取或操作正式環境憑證、main merge。

## 範圍
- scope_paths：product/**、docs/platform/revisions/D1_A_ACTIVATION_AND_CLAIM.md、docs/platform/revisions/D1_A_RESPONSE.md。
- 交付：合成資源目錄（列表、詳情、地區與類別篩選、合成標示／來源／查核日期／有效狀態、未知期限與過期說明、空白／錯誤／不存在頁）。
- 資料：既有 docs/platform/examples/synthetic_resources.json 的 6 項資源、6 個來源、2 種家庭口徑。
- 不做：問答、個案工作台、上傳、聯絡表單、登入、HTMX、CI 變更、四份基線與既有規格／證據修改。

## 時間與資源
- 開始 UTC：2026-10-13T12:09:39Z（本 session 首次 fetch 時刻）。
- deadline UTC：2026-10-13T14:09:39Z（開始後 120 分鐘）。
- 上限：120 分鐘實作與自檢、外部成本 0、最多一次初始交付；超限交付 PARTIAL 固定 SHA。
- 歷史額度：N 修補 3/3、ENV 修補 3/3、各 delivery 1/1 保留，不清除。

## 驗收（照指示第七節）
README 可重現安裝／設定／啟動／匯入／測試／停止；migration 與重複匯入冪等且不覆蓋版本歷史；拒絕非合成資料且失敗不留部分匯入；HTTP 列表／詳情／篩選符合規格；未知地區空態與不存在資源錯誤頁；資料庫失效不顯示 traceback 或連線字串；360px 無水平捲動且鍵盤可操作並附實際畫面；3 分鐘展示步驟；展示只含合成資料；服務啟動與停止後清理。另跑五支 repo 文件工具並附輸出；四份基線對 base 的 diff 須為空。

## 競爭 claim 核對
- PR #1 全部 46 則留言讀回；最後一則為 GPT 2026-10-13T03:06Z 的停滯對帳；其後無任何 D1-A claim、交付或在途結果。
- ls-remote／fetch：main、claude/stp-platform-plan-001、claude/tender-allen-89joyz、claude/tender-allen-sko8pq、claude/tender-allen-c9p5u1、claude/relaxed-maxwell-q2b86k；無其他 D1-A 結果分支。
- 結論：無競爭 claim，依指示 claim 後直接執行，不增加第二道等待。

## next_actor
GPT：固定成果獨立產品覆核。Frank：不需例行行動。

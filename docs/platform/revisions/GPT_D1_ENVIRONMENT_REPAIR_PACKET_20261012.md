# D1_ENVIRONMENT 第一次有界修補工作包
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-ENVIRONMENT；stage D1_ENVIRONMENT；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content e8239a3c678432bea2492daeee71fa737e6b02ef；base/main 9a7bd1295e20837786acc45bdab7fb94f5a1b012；handoff exact SHA由PR回執提供。source須為ancestor、原response144行保持逐位元一致；live不同先HEAD_MISMATCH停止，不能猜最新head。
工作分支claude/tender-allen-c9p5u1，既有session沿用；PR1/base main，但不push main、不force。核對最新帳本、工單、claim、競爭claim，再追加本修補claim含session/source/handoff/scope/開始UTC/deadline/能力/交付位置。

## 範圍、額度、理由
僅在 docs/platform/revisions/D1_ENVIRONMENT_RESPONSE_20261012.md 後追加repair1，不改原144行、作者其他程式/證據或GPT治理。隔離/tmp合成腳本、venv、wheelhouse、DB允許；repo不得新增產品/依賴lock/二進位/.github/部署檔或修改四基線。
GPT依Frank技術與有限修補委託具體化ENV-01～03；仍是隔離環境證據，不授權產品、外部服務/真實資料/部署/main merge。
exact UTC deadline2026-10-12T06:00:00Z不變；额外最多30分鐘、外部成本0、一次repair交付；repair_round_limit1/used0，本次repair1/1。initial delivery1/1、readiness1/1、N修補3/3保留，不重置。無自動第二輪修補。
資料僅is_synthetic=true合成；只既存CPU/磁碟、標準PyPI固定上述5套件artifacts下載，已有PG16/非root身分；不新增OS使用者/提權/系統套件/Dockerimage/daemon/cloud/session/費用。不得列舉env或讀Secret；公共CA若不可用就partial，不绕过平台拒絕。

## 動作與驗收
1. ENV-01追加完整shell/Python編排正文，所有實際命令/exit/output。唯一task目錄、umask077、既有非root明確降權、sock目錄0700、以實際命令寫listen_addresses空值並讀回。trap/finally只停止此task pg_ctl，確認status3、socket/pgdata/log清除；不kill無關process。正常路及合成煙霧失敗注入路均驗證cleanup，不能只有成功摘要。venv/wheelhouse可保留，位置/容量列明；不要保留CA複本/下載log等非必要可重建暫存。
2. ENV-02停止後負向只接受指定socket不存在/connection unavailable（核對錯誤原因），其他OperationalError非0；正向unix_only=False亦非0。合成mock認證錯誤、permission錯誤與非Unix三項必須拒絕，記expected/actual/exit；實際正向(1,0,1,true)與停止負向、清理證據分開。mock不能冒稱runtime。
3. ENV-03優先已有可解析artifact cache，否则最多一次標準PyPI下載：固定作者列出的5版本，用venv pip --isolated download到task wheelhouse，實算SHA256/名稱/大小，完整路徑命令不依賴PATH；不得假稱新hash證明上輪原download。離線使用該wheelhouse安裝到task隔離venv、核對實際版本與清單。網路暫時失敗最多一次安全重試且仍在30min；不改鏡像、不讀pip帳號設定、不新增repo lock。固定版本無法取得就partial，不換版本掩蓋。
4. 必要repo檢查：python3 docs/platform/examples/check_examples.py；python3 docs/platform/tools/gen_state_machines.py --check；python3 docs/platform/tools/gen_permissions.py --check；python3 docs/platform/tools/test_checks.py；python3 docs/platform/tools/check_docs.py。四原始基線git diff base到result為空、只response append；記完整SHA/command/output/exit。
5. 新repair段列ENV-01～03逐項對照、source/handoff/claim、完整編排與negative mock腳本、artifacts和版本、所有正常/失敗/清理輸出、真正未證明項。禁止env值/私人鏈結/Secret；本repo公開。發固定result SHA至PR1一次DELIVERY，作者證據不自批。

## 停止與恢復
競爭claim/source不符、新權限/費用/真實資料/外部服務、無非root能力、時限/範圍越界即cleanup後partial；不反覆重試。下載artifact或DB不可用如實列失敗與最小解法。此包不包含官方LTS查核或產品开工，後續由GPT技術決策另核對。
next_actor GPT；checkpoint READY_FOR_REVIEW只在固定結果交回後；GPT exact-head覆核，未過不自動追加額度，通過再具體化D1下一步。沒有launcher能力證據，POSTED不等ACK/STARTED。

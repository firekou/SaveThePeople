# D1 LTS 可重建交付包
status READY；work_id STP-PLATFORM-PLAN-001；task_id STP-PLATFORM-PLAN-001-D1-LTS-REPLAY；stage D1_LTS_REPLAY；executor Claude；reviewer GPT；next_actor Claude。
goal：讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。（main v0.1）
source_content6c87bebebe4473358c18867cd232734d5fd8bb76；base/main9a7bd1295e20837786acc45bdab7fb94f5a1b012；handoff由PR回執exact SHA核對，source須ancestor。分支claude/tender-allen-c9p5u1；交PR1 Draft/base main；non-force、不寫main。
GPT依最新一般技術/有限續作委託決定只整理既有交付，成本0、25分鐘、一次固定交付、exact deadline2026-10-12T06:00:00Z；repair_round_limit0/used0，原LTSdelivery1/1/ENVrepair3/3/N3/3等保留。新task不是重置修補。
scope_paths只新增docs/platform/revisions/D1_LTS_REPLAY_RESPONSE_20261012.md；只在/tmp隔離副本可提取既有文字/檢查bash語法。excluded所有作者/Reviewer歷史、既有工具/實作、product、.github、lock、二進位、四基線；不重新下載/install/跑DB/HTTP、不查外部、不讀Secret/CA、不部署/費用/通知/真實資料。
claim先核對競爭/在途，沿合法session，不冒充舊session；記work/task/stage/session/source/handoff/scope/UTC開始/deadline/資源/能力/交付位置。只一次交付。

## 明確交付與驗收
1. 新response以完整可提取fenced原文提供LTS orchestrate、smoke.py、smokelib.py、wheelhouse.sha256與必要離線verify/build命令；從既有LTS task腳本讀取或從固定歷史+完整diff重建，兩者分開標OBSERVED/RECONSTRUCTED。不要手改控制流程/exit/safety；列固定source原文件/章節、逐檔SHA256及與原文cmp/diff；沒有檔案就明確partial，不宣稱讀到。
2. 不依賴舊/tmp/stp-d1-scripts的隱含檔案：列目錄清單、每個helper引用與來源、五wheel檔名/hash/平台cp313及PG16/非root前置。只描述有授權時如何取得wheel，下載仍NOT_AUTHORIZED_IN_THIS_PACKET，不能默認cache永存。
3. 提供乾淨checkout提取原文與核hash/離線重建順序、私人socket/無TCP/降權/停止總budget2/失敗保留/清理步驟；命令不讀帳號配置/Secret。不產生全域帳號，不使用HOME新值作shell變數，不引入Docker/SQLite替代。
4. bash -n提取脚本，必要5 repo命令逐項exit/output、四基線diff空。只語法/完整性驗收，DB與artifact實檔仍AUTHOR_EVIDENCE/NOT_RUN/NOT_VERIFIED，不複製原數字成Reviewer結果；清楚區分回放說明與實際已跑。列98MB/tmp保留與容器失效恢復界線。
5. 固定result SHA+檔案/命令/結果/資源/未證明交PR1，不自批。D1-A仍PREPARED，本包不是產品開工。
stop：HEAD_MISMATCH/競爭claim/超scope/25min/deadline、缺helper或需新套件/權限/費用，交partial與唯一最小恢復；不自動修/重試。next_actor GPT exact-head完整性覆核→核對六gate與產品授權，再核發可見D1-A，沒有批准不冒充READY產品。新包POSTED不等ACK/STARTED，無launcher。

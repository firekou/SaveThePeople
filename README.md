# SaveThePeople
社會資源導航與申請協助專案。

## 專案目標
讓需要幫助的人被接觸到，理解可能適用的福利與服務，完成申請，實際取得資源，並在資格、政策或期限改變時持續受到協助。

核心成果是「新增實際取得幫助的家庭數」，同時追蹤等待時間、服務成本與續辦結果。

## 文件入口
- [專案目標與完整藍圖](docs/PROJECT_BLUEPRINT.md)
- [90 天執行計畫與驗收](docs/EXECUTION_PLAN.md)
- [服務流程與營運責任](docs/SERVICE_MODEL.md)
- [資料、資格規則與系統規格](docs/DATA_AND_PRODUCT_SPEC.md)

### 平台規劃（STP-PLATFORM-PLAN-001，v0.2-draft，待獨立覆核）
承接上列基線，細化為可直接開發的規格；與 90 天計畫的對照見各文件。
- [產品需求、角色權限與成果口徑](docs/platform/PRODUCT_REQUIREMENTS.md)
- [服務流程與頁面規格](docs/platform/USER_JOURNEYS_AND_SCREENS.md)
- [資料模型與狀態機](docs/platform/DATA_MODEL_AND_STATE_MACHINES.md)
- [資源蒐集更新與資格規則引擎](docs/platform/RESOURCE_AND_ELIGIBILITY_ENGINE.md)
- [技術架構與 API](docs/platform/ARCHITECTURE.md)
- [資料保護、營運與成本](docs/platform/OPERATIONS_AND_PRIVACY.md)
- [開發工作包、試點閘門與測試情境](docs/platform/BUILD_PLAN_AND_ACCEPTANCE.md)
- [決策、外部待確認事項與基線缺口](docs/platform/DECISIONS_AND_UNKNOWNS.md)
- [合成範例資料與檢查程式](docs/platform/examples/README.md)

## 當前狀態
2026-10-03：建立專案規劃基線 v0.1。尚未建立產品、部署服務、確認合作機構或服務真實家庭。
90 天由試點啟動日計算，不代表已有外部合作承諾。
2026-10-03：完成平台規劃 v0.2-draft（docs/platform/），待獨立覆核；仍未建置產品或部署，範例皆為合成資料。

## 第一階段範圍
以台灣一個縣市、兩個合作據點、經濟困難且有兒少的家庭為試點。
建立 30～50 項有效資源，協助約 20～30 戶家庭，目標至少 10 戶新增實際取得幫助。
上述數字是試點目標，核准與取得資源仍由提供機構及實際條件決定。

## 執行原則
- 資格初篩不等同核定；資料不足不等同不符合。
- 每項推薦附來源、適用地區、有效期間及查核日期。
- 每個案件都有負責人、下一步與期限。
- 線上、電話、紙本及現場協助並行。
- 真實個案、證件、聯絡資訊與申請文件不進入公開 GitHub。
- 公開成果使用匿名、彙總資料，不公開可辨識的弱勢身分。

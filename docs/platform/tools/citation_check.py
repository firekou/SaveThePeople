#!/usr/bin/env python3
"""決策與章節「引用語境」檢查（只使用標準函式庫）。

ID 存在不代表引用正確：例如把「停滯天數門檻」引用成 D-309（預算）而非 D-310（營運門檻），ID 存在檢查抓不到。
本檢查對**被引用的決策 ID 與跨文件章節**，要求引用所在的行（表格列或句子）含有該決策或章節的主題關鍵字之一；
找不到就報錯。這是啟發式檢查：關鍵字表是人工維護的（見 DECISION_KEYWORDS、SECTION_KEYWORDS），
不能證明所有引用語意正確，只能抓到「引用行完全沒有被引用對象主題」的錯位。例外必須列在 EXCEPTIONS，並寫明原因。
"""
import re

DECISION_KEYWORDS = {
    "D-105": ["取得驗證", "第二人", "驗證人", "驗證"],
    "D-106": ["排序"],
    "D-201": ["技術", "Django", "堆疊", "架構", "推薦 A"],
    "D-202": ["部署", "雲端", "Google Cloud"],
    "D-205": ["遮蔽", "n<5"],
    "D-301": ["保存", "RT-"],
    "D-302": ["承接", "未結案"],
    "D-303": ["控制者", "控管者"],
    "D-304": ["平台準備期", "人工優先", "G-01"],
    "D-305": ["觀察期", "180", "追蹤報告", "審查中"],
    "D-306": ["AI", "外部"],
    "D-307": ["工程人力", "工程"],
    "D-308": ["回溯", "新增"],
    "D-309": ["預算", "經費", "成本"],
    "D-310": ["營運", "門檻", "時限", "期限", "OP-", "停滯", "工作日", "失聯", "容量", "確認"],
    "D-311": ["期限不明", "放寬"],
    "D-312": ["放寬", "地區", "已確認", "C2"],
    "D-313": ["外部 AI", "文件"],
}

# (文件代碼, 章節) → 主題關鍵字；文件代碼：ENGINE、OPS、DM、PRD、ARCH、BP、DEC、UJ
SECTION_KEYWORDS = {
    ("ENGINE", "0"): ["推薦", "目錄", "展示", "期限不明", "MANUAL_CHECK_ONLY", "衝突", "暫停"],
    ("ENGINE", "0.1"): ["目錄", "catalog_visibility", "公開"],
    ("ENGINE", "0.2"): ["推薦", "NEEDS_RECHECK", "寬限", "人工查核", "FORMAL", "recommendation", "期限", "判定", "查核"],
    ("ENGINE", "5"): ["規則", "條件", "運算子", "口徑", "驗證", "格式", "結構"],
    ("ENGINE", "5.1"): ["門檻", "5%", "條件", "±5%"],
    ("ENGINE", "5.3"): ["口徑", "成員", "計算", "未知", "支援"],
    ("ENGINE", "5.5"): ["expression", "運算式", "CUSTOM"],
    ("ENGINE", "6"): ["結果", "組合", "評估"],
    ("ENGINE", "6.1"): ["單條件", "PASS", "FAIL", "5%"],
    ("ENGINE", "6.2"): ["組合", "資料不足", "節點", "ANY", "ALL", "CUSTOM", "已知不符"],
    ("ENGINE", "6.4"): ["自述", "確認", "不符"],
    ("ENGINE", "6.6"): ["排序", "權重"],
    ("ENGINE", "7"): ["併領", "排除", "相依", "stacking"],
    ("ENGINE", "8"): ["影響分析", "變動", "查核頻率", "既有案件"],
    ("ENGINE", "9"): ["容量", "名額", "失效", "衝突"],
    ("ENGINE", "11.1"): ["AI", "替代"],
    ("ENGINE", "11.2"): ["文件", "辨識", "OCR", "外部 AI"],
    ("OPS", "1.2"): ["同意", "兒少", "用途"],
    ("OPS", "1.3"): ["撤回", "副本", "清除", "刪除", "代理", "限制處理"],
    ("OPS", "1.3.3"): ["控制紀錄", "ControlRecord", "還原", "撤回", "刪除"],
    ("OPS", "1.4"): ["保存", "RT-"],
    ("OPS", "1.6"): ["AI", "外部"],
    ("OPS", "2.2"): ["查核", "品質"],
    ("OPS", "2.3"): ["責任人", "備援", "容量", "案件數", "量能"],
    ("OPS", "2.4"): ["升級", "失聯", "聯絡", "門檻", "期限", "急迫", "時限", "停滯"],
    ("OPS", "3"): ["成本", "費用", "金額", "人力"],
    ("DM", "2.13"): ["申請", "唯一", "kind"],
    ("DM", "2.13.1"): ["防重複", "kind", "AP-06", "送件"],
    ("DM", "2.14"): ["轉介", "回覆", "response_due"],
    ("DM", "2.4.1"): ["recheck", "effective_unknown", "欄位", "結構", "寬限", "複查"],
    ("DM", "2.9"): ["Fact", "區間", "事實"],
    ("PRD", "4"): ["權限", "角色", "矩陣", "範圍代碼", "R3", "R4"],
    ("PRD", "4.3"): ["驗證", "限制", "角色"],
    ("PRD", "7.2"): ["OutcomeEvent", "計數", "取得", "階段"],
    ("PRD", "7.2.1"): ["取得", "驗證", "OutcomeEvent"],
    ("PRD", "7.5"): ["品質", "漏追", "抽查", "停滯"],
    ("PRD", "7.6"): ["參數", "統計", "回溯", "PR-", "metric_spec_version"],
}

DOC_NAMES = {
    "RESOURCE_AND_ELIGIBILITY_ENGINE.md": "ENGINE", "引擎文件": "ENGINE", "引擎": "ENGINE",
    "OPERATIONS_AND_PRIVACY.md": "OPS", "OPERATIONS": "OPS",
    "DATA_MODEL_AND_STATE_MACHINES.md": "DM", "DATA_MODEL": "DM",
    "PRODUCT_REQUIREMENTS.md": "PRD", "PRD": "PRD",
}
SECTION_RX = re.compile(
    r"(RESOURCE_AND_ELIGIBILITY_ENGINE\.md|OPERATIONS_AND_PRIVACY\.md|DATA_MODEL_AND_STATE_MACHINES\.md|PRODUCT_REQUIREMENTS\.md|引擎文件|引擎|OPERATIONS|DATA_MODEL|PRD)"
    r"(?:\]\([^)]*\))?\s*§(\d+(?:\.\d+)*)")
# 例外：(檔名, 行內必含片段) → 原因。T-61 的說明文字刻意舉出錯誤引用作為反例。
EXCEPTIONS = [
    ("BUILD_PLAN_AND_ACCEPTANCE.md", "T-61", "T-61 的情境說明刻意以 D-309 為錯誤引用的例子"),
    ("DECISIONS_AND_UNKNOWNS.md", "修正（對應第一輪覆核", "修訂摘要行以範圍表示法 D-310～D-313 列出新增決策，不是主題引用"),
]


def _excepted(fname, line):
    return any(fname == f and frag in line for f, frag, _ in EXCEPTIONS)


def citation_problems(fname, text):
    """回傳 [(行號, 說明)]。"""
    probs = []
    for n, line in enumerate(text.splitlines(), 1):
        if _excepted(fname, line):
            continue
        is_decision_def = fname == "DECISIONS_AND_UNKNOWNS.md" and re.match(r"^\| D-\d{3} ", line)
        for m in re.finditer(r"\bD-\d{3}\b", line):
            did = m.group(0)
            if did not in DECISION_KEYWORDS:
                continue
            if is_decision_def and line.startswith(f"| {did} "):
                continue  # 定義本身
            if not any(k in line for k in DECISION_KEYWORDS[did]):
                probs.append((n, f"{did} cited without any of its topic keywords {DECISION_KEYWORDS[did]}: {line.strip()[:90]}"))
        for m in SECTION_RX.finditer(line):
            key = (DOC_NAMES[m.group(1)], m.group(2))
            kws = SECTION_KEYWORDS.get(key)
            if kws and not any(k in line for k in kws):
                probs.append((n, f"{m.group(1)} §{m.group(2)} cited without topic keywords {kws}: {line.strip()[:90]}"))
    return probs

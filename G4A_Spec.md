# 🚀 G4A (Gemma 4 Agent) 開發規格說明書

**文件目標：** 指導 AI 助手從零開始構建一個具備自我進化能力、高安全性且以 Gemma 4 為核心的通用型 Agent CLI。

---

## 🛠 第一部分：核心開發提示詞 (System Prompt for Dev)

> **Role:** 你是一位專精於 Python 與 AI 安全架構的資深工程師。你的目標是實作一個名為 `G4A` 的進化型 CLI。
>
> **Core Mission:** > 建立一個能理解任務、在現有工具不足時自動編寫 Python 代碼、經過安全審核後將代碼整合為新技能（Skills）的 Agent 系統。
>
> **Constraints:**
> 1. 代碼必須具備高度模組化，易於擴展。
> 2. 任何由 AI 生成的代碼必須經過 AST 掃描與沙盒隔離。
> 3. 介面需支援流式輸出與思維過程（Thinking Mode）的展示。
> 4. 嚴格遵守提示詞注入（Prompt Injection）防禦規範。

---

## 📋 第二部分：技術規格與功能清單

### 1. 系統架構 (Architecture)
* **語言與框架:** Python 3.10+, `Typer` (CLI), `Rich` (UI), `PydanticAI` (Agent Logic)。
* **推理引擎:** 對接本地 **vLLM** 或 **Ollama** 的 Gemma 4 接口 (API URL 需可配置)。
* **技能庫 (Skill Library):** 位於 `~/.g4a/skills/`，支持動態加載。
* **向量檢索 (RAG):** 整合本地 **BGE-M3** 模型，用於搜尋過往成功的技能腳本。

### 2. 功能模組 (Modules)
* **`/` 指令控制中心:**
    * `/brain <model>`: 切換模型名稱。
    * `/api <url>`: 修改後端 API 地址。
    * `/skills`: 列出當前學會的所有技能。
    * `/reset`: 清空對話記憶。
* **進化循環 (Evolution Loop):**
    * **偵測需求:** 當大腦判定無法完成任務時，自動進入「代碼編寫模式」。
    * **自我修正:** 執行報錯時，將 Traceback 回傳給 Gemma 4 進行 Self-Refinement。
* **安全性 (Security):**
    * **AST 分析:** 攔截 `os.system`, `subprocess` 等危險系統調用。
    * **Docker 沙盒:** 生成的工具必須在分離的容器環境中執行。
    * **XML 隔離:** 使用 XML 標籤包裹使用者輸入，防止指令劫持。

### 3. 使用者體驗 (UX)
* **Thinking Mode:** 捕捉並渲染 `<thinking>` 標籤內容，讓推理鏈可見。
* **Human-in-the-loop (HITL):** 生成新工具或執行系統操作前，必須強制顯示代碼並獲得 `(y/n)` 確認。

---

## 📝 第三部分：開發查核列表 (Checklist)

### ✅ 第一階段：基礎框架 (MVP)
- [ ] 實作 `cli_manager.py`，支援 `/` 指令攔截。
- [ ] 實作 `brain_engine.py`，串接 Gemma 4 串流 API。
- [ ] 支援配置檔 `config.json` 持久化儲存。
- [ ] 成功在終端渲染 Markdown 格式的回應。

### ✅ 第二階段：技能生成與動態加載
- [ ] 實作 `evolution_mgr.py` 的技能管理邏輯。
- [ ] 實作 `importlib` 動態加載已存在的 `.py` 技能腳本。
- [ ] 設計 System Prompt 引導 Gemma 4 產出標準化的 Tool 代碼。
- [ ] 實作捕捉代碼執行錯誤並觸發重新生成的邏輯。

### ✅ 第三階段：安全強化 (Hardening)
- [ ] 整合 `ast` 模組，完成靜態代碼安全審查器。
- [ ] 實作 Docker-py 連接器，將技能執行導向沙盒容器。
- [ ] 實作提示詞注入預審機制（由 Gemma 4 先行判斷安全性）。
- [ ] 確保 HITL 確認機制在每次新生成工具時正確觸發。

### ✅ 第四階段：高級功能
- [ ] 整合 BGE-M3 實現技能庫的 RAG 檢索。
- [ ] 支援多輪對話中的上下文壓縮與長文本處理 (256k)。
- [ ] 實作 Token 消耗統計與性能監控顯示。

---

## 🏗 第四部分：預期專案目錄結構

```text
g4a/
├── main.py                # 程式進入點
├── config.json            # 模型與 API 配置
├── core/
│   ├── cli_manager.py     # 指令與對話循環
│   ├── brain_engine.py    # LLM 調用封裝
│   └── safety.py          # AST 掃描與注入防禦
├── agent/
│   ├── evolution_mgr.py   # 技能生成與修正
│   └── sandbox.py         # Docker 沙盒執行器
└── skills/                # 存放生成之 .py 技能
    └── __init__.py
```
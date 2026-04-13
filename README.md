# 🚀 G4A (Gemma 4 Agent) CLI

G4A 是一個具備自我進化能力、高安全性且以 Gemma 4 (或其他相容的 LLM，如 Ollama/vLLM) 為核心的通用型 Agent CLI。

## 🌟 核心理念與特色功能

G4A 的目標是建立一個能理解任務的 Agent 系統。當現有工具不足以完成使用者的請求時，它會啟動進化循環，並具備以下強大特色：

1. **偵測需求與代碼生成**：當無法直接回答時，自動進入「代碼編寫模式」，編寫 Python 代碼解決問題。
2. **智慧命名**：系統會在背景利用 LLM 為生成的腳本產生簡潔、易讀的 Python 變數命名 (snake_case)。
3. **強制真實執行 (Anti-Simulation)**：提示詞嚴格禁止 LLM「模擬」結果，強制要求透過網路請求或計算取得真實數據。
4. **自我修正引擎 (Self-Refinement)**：如果生成的腳本在本地執行失敗，G4A 會自動將 Error Traceback 回傳給 LLM 要求修正，並支援最多 3 次的自動遞迴重試。
5. **對話式總結 (Conversational Summary)**：技能執行完成後，系統會將生硬的 Raw Data 交給 LLM，讓它用自然語言為使用者進行摘要報告。
6. **技能調用 (Tool Calling)**：下次遇到相同任務時，G4A 能自動從系統上下文中辨識並呼叫已經學會的工具 (`EXECUTE_SKILL`)，省去重複生成的麻煩。

## 🛠️ 安裝與初始化

本專案提供了一個自動化的初始化腳本，會為您檢查環境、建立虛擬環境 (venv) 並安裝所有必要的依賴套件。

1. **確保您已安裝 Python 3.10 或以上版本**。
2. **(選擇性但強烈建議)** 確保您已安裝 Docker，以啟用沙盒安全執行機制。
3. **確保您的本地 LLM 服務 (如 Ollama) 已啟動**。

在專案根目錄下執行初始化腳本：

```bash
python init_setup.py
```

## 🚀 啟動 G4A

初始化完成後，啟動虛擬環境並執行主程式：

**Windows:**
```cmd
.venv\Scripts\activate
python main.py
```

**macOS / Linux:**
```bash
source .venv/bin/activate
python main.py
```

## ⌨️ 內建指令

進入 G4A CLI 後，您可以直接與 AI 助手對話，或是使用以下系統指令：

- `/brain <model>`: 切換使用的模型名稱 (例如：`/brain gemma:7b`)。
- `/api <url>`: 修改後端 API 地址 (預設為 `http://localhost:11434/api`，支援 OpenAI 相容 API 如 `/v1/chat/completions`)。
- `/apikey <key>`: 設定 API Key 以進行外部 API 服務的身分驗證。
- `/skills`: 列出當前系統已學會的所有技能。
- `/reset`: 清空當前的對話記憶上下文。
- `/help`: 顯示幫助訊息。

## 🛡️ 安全與防護機制

- **AST 掃描**: 嚴格攔截生成的程式碼中對 `os`, `subprocess`, `sys`, `shutil`, `eval`, `exec` 等危險模組與函數的調用。
- **環境封印**: 強制規定 LLM 僅能使用 Python 內建函式庫與 `requests`，禁止使用未安裝的第三方套件 (如 `bs4`)，以防止環境崩潰 (`ModuleNotFoundError`)。
- **Docker 沙盒**: 新生成的技能代碼預設會在沒有網路且資源受限的容器環境中進行測試執行。
- **本地真實執行 (Fallback)**: 若系統未安裝 Docker，G4A 仍會使用 `subprocess` (並強制設定 UTF-8 編碼防呆) 在本地真實執行程式碼，以驗證邏輯有效性。
- **函數完整性檢查**: 執行前會驗證生成的程式碼是否確實包含必需的 `def run_skill():` 進入點。
- **Human-in-the-loop (HITL)**: 在正式儲存並執行新技能之前，會將程式碼展示給使用者，並需要輸入 `y` 確認。

## 📂 目錄結構說明

- `main.py`: 程式進入點。
- `init_setup.py`: 環境初始化腳本。
- `config.json`: 模型與 API 配置檔 (已設定 Git 忽略以防金鑰外洩)。
- `core/`: 核心模組 (CLI 介面、Brain 引擎通訊、AST 安全掃描)。
- `agent/`: Agent 邏輯 (技能進化管理器、Docker 沙盒執行器)。
- `~/.g4a/skills/`: 預設的技能庫目錄，存放由 AI 生成並通過測試的 `.py` 技能腳本 (路徑可於 `config.json` 修改)。

---
*專案規格詳見 [G4A_Spec.md](./G4A_Spec.md)*

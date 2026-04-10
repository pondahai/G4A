# 🚀 G4A (Gemma 4 Agent) CLI

G4A 是一個具備自我進化能力、高安全性且以 Gemma 4 (或其他相容的 LLM，如 Ollama/vLLM) 為核心的通用型 Agent CLI。

## 🌟 核心理念

G4A 的目標是建立一個能理解任務的 Agent 系統。當現有工具不足以完成使用者的請求時，它會：
1. **偵測需求**：自動進入「代碼編寫模式」。
2. **生成代碼**：編寫能達成任務的 Python 代碼。
3. **安全審核**：經過嚴格的 AST 靜態掃描與 Docker 沙盒隔離測試。
4. **自我進化**：將驗證通過的代碼整合為全新的「技能 (Skills)」，在未來遇到類似任務時直接調用。

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
- `/api <url>`: 修改後端 API 地址 (預設為 `http://localhost:11434/api`)。
- `/skills`: 列出當前系統已學會的所有技能。
- `/reset`: 清空當前的對話記憶上下文。
- `/help`: 顯示幫助訊息。

## 🛡️ 安全機制

- **AST 掃描**: 攔截生成的程式碼中對 `os.system`, `subprocess` 等危險系統調用的行為。
- **Docker 沙盒**: 新生成的技能代碼會在沒有網路且資源受限的容器環境中進行測試執行。
- **Human-in-the-loop (HITL)**: 在正式儲存並執行新技能之前，會將程式碼展示給使用者，並需要輸入 `y` 確認。

## 📂 目錄結構說明

- `main.py`: 程式進入點。
- `init_setup.py`: 環境初始化腳本。
- `config.json`: 模型與 API 配置檔。
- `core/`: 核心模組 (CLI 介面、Brain 引擎通訊、AST 安全掃描)。
- `agent/`: Agent 邏輯 (技能進化管理器、Docker 沙盒執行器)。
- `~/.g4a/skills/`: 預設的技能庫目錄，存放由 AI 生成並通過測試的 `.py` 技能腳本 (路徑可於 `config.json` 修改)。

---
*專案規格詳見 [G4A_Spec.md](./G4A_Spec.md)*
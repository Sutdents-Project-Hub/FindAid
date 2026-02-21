# LabMate AI 🧪🤖
**您的全方位智慧科研協作夥伴**

LabMate AI 是一款專為科研人員、學生及教育工作者設計的實驗管理與協作工具。它結合了嚴謹的資料結構與靈活的 AI 輔助功能，讓您可以輕鬆追蹤實驗進度、管理實驗變因，並獲得即時的實驗設計建議。

---

## ✨ 核心功能

### 1. 📊 實驗數據管理 (Experiment Management)
*   **版本控制**：自動記錄每次數據更新的版本，確保實驗數據的可追溯性。
*   **結構化儲存**：使用 SQLite 資料庫安全儲存實驗名稱、描述、創建者及詳細數據。
*   **歷史回溯**：(開發中) 支援查看與恢復實驗數據的歷史版本。

### 2. 📝 實驗計畫協作 (Plan Collaboration)
*   **計畫制定**：設定研究目標、建立實驗步驟與材料清單。
*   **多人協作**：支援新增與移除協作者，促進團隊合作。
*   **動態調整**：隨時修改步驟與材料，靈活應對實驗變化。

### 3. 🤖 AI 科研助理 (AI Research Assistant)
*   **流程設計**：輸入研究目標 (如「研究植物光合作用」)，AI 自動生成建議的實驗流程。
*   **問題拆解**：將複雜的研究問題拆解為可執行的子問題。
*   **標準作業程序 (SOP)**：生成實驗的標準操作步驟與安全注意事項。

### 4. 🔬 儀器使用指南 (Instrument Guide)
*   **智慧查詢**：透過關鍵字 (如「顯微鏡」) 快速查找儀器使用說明與文檔。
*   **擴充性**：支援自定義儀器資料庫 (JSON 格式)。

---

## 🚀 快速開始

### 系統需求
*   Python 3.6 或以上版本
*   內建 SQLite3 支援 (Python 標準庫已包含)

### 安裝步驟

1.  **下載專案**
    將專案下載至您的本地端電腦。

2.  **環境設定**
    本專案使用 Python 標準庫，無需額外安裝 `pip` 套件。

### 執行範例

在終端機 (Terminal) 中執行主程式，即可看到系統功能的演示：

```bash
python "LabMate AI.py"
```

程式將自動執行以下操作：
1.  初始化 `labmate_data.db` 資料庫。
2.  創建一個示範實驗 (葡萄糖對酵母生長影響)。
3.  更新實驗數據並記錄版本。
4.  創建實驗計畫並添加協作者。
5.  演示 AI 互動功能 (查詢儀器、設計流程)。

---

## 📖 詳細使用教學

### 1. 初始化系統
在您的 Python 腳本中引入 `LabMateAI` 類別並實例化：

```python
from LabMate_AI import LabMateAI # 假設檔名更名為模組化名稱，或直接在原檔修改

labmate = LabMateAI()
```

### 2. 管理實驗 (Experiments)

**創建新實驗：**
```python
experiment_id = labmate.create_experiment(
    name="觀察水的電解",
    description="使用不同電極觀察電解效率",
    created_by="Researcher_A"
)
```

**更新實驗數據：**
```python
labmate.update_experiment_data(
    experiment_id,
    new_data={"voltage": 5, "gas_produced": "10ml"},
    updated_by="Researcher_A"
)
```

### 3. 管理計畫 (Plans)

**建立計畫與步驟：**
```python
plan_id = labmate.create_plan(
    name="水電解實驗計畫",
    research_goal="測量氫氣生成速率",
    created_by="Researcher_A"
)

# 添加步驟
labmate.add_step_to_plan(plan_id, "準備直流電源供應器")
labmate.add_step_to_plan(plan_id, "連接石墨電極")
```

**添加協作者：**
```python
labmate.add_collaborator_to_plan(plan_id, "Assistant_B")
```

### 4. AI 互動與查詢

目前支援以下指令格式進行 `interact`：

*   **查詢儀器**：`"儀器使用 [儀器名稱]"`
*   **設計流程**：`"設計實驗流程 [研究目標]"`
*   **拆解問題**：`"拆分問題 [研究問題]"`
*   **生成 SOP**：`"標準流程 [實驗細節]"`

**範例：**
```python
response = labmate.interact("User_A", "text", "設計實驗流程 研究酸雨對植物的影響")
print(response)
```

---

## 📂 進階設定：新增儀器文檔

若要啟用儀器查詢功能，請在專案根目錄下建立 `instrument_docs` 資料夾，並放入 JSON 格式的儀器定義檔。

**檔案結構範例：** `instrument_docs/microscope.json`

```json
{
    "instrument_id": "inst_001",
    "name": "光學顯微鏡",
    "description": "利用可見光觀察微小物體的儀器。",
    "guide": "microscope_guide.txt"
}
```
*註：您還需要建立對應的 `microscope_guide.txt` 使用手冊檔案。*

---

## 🛠 未來規劃
*   [ ] 整合 OpenAI/Gemini API 進行真實的 AI 文獻分析。
*   [ ] 開發 Web 或 App 前端介面。
*   [ ] 支援語音輸入與圖像辨識功能實作。

---

**LabMate AI - 讓科研更簡單、更智慧。**

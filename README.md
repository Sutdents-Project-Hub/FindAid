# 行善台北｜青年共融資源助理（Streamlit Demo）

本專案以 AI 與政府開放資料為核心，將「資源資訊」轉成「可執行的下一步」，協助青年族群在就學、就業、心理健康、社福補助、居住、法律與志工參與等情境中，快速找到可用資源並產出行動計畫。

## 功能重點
- 需求快篩：用最少輸入整理需求方向
- 資源推薦：從資源庫（開放資料/主辦方 API/自蒐資料）做檢索與排序
- 地圖與附近：顯示具備座標的點位
- 行動計畫：輸出「下一步清單 + 準備清單」，可下載 JSON
- AI 助手：在資源庫脈絡下回答問題（避免憑空捏造）

## 資料來源與合規
- 專案內建 `data/sample/resources.json` 作為離線示例資料，參賽/上線前請替換為臺北市資料大平臺或主辦方指定資料來源，並保留每筆資源的 `source_*` 欄位（來源、授權、更新時間）。

## 環境需求
- Python 3.9+（建議）

## 安裝
```bash
pip install -r requirements.txt
```

## 設定（LLM）
本專案使用 OpenAI 相容介面，請用環境變數提供設定（不要把 key 寫在程式碼或 repo）。

你可以複製 `.env.example` 為 `.env` 後填入：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（可留空；若使用相容轉發服務才需要，例如 free_chatgpt_api 可填 `https://free.v36.cm`）
- `OPENAI_MODEL`（預設 `gpt-4o-mini`）

也可強制離線模式：
- `LABMATE_OFFLINE=1`

## 設定（開放資料同步）
在「資料來源」頁可一鍵同步雙北 YouBike2.0 即時站點資訊並寫入 SQLite（會以 `INSERT OR REPLACE` 更新）。

可用環境變數：
- `LABMATE_OPEN_DATA_ENABLED=1`（是否顯示同步 UI）
- `LABMATE_ALLOW_INSECURE_SSL=1`（僅在部分環境遇到新北資料平台 SSL 驗證失敗時才需要）

## 執行
```bash
streamlit run app.py
```

## 資源資料格式（resources）
示例：`data/sample/resources.json`
- `id`：唯一值
- `name`：資源名稱
- `category`：分類（就業/就學/心理健康/社福補助/…）
- `audience_tags`：服務對象標籤（字串即可）
- `description`、`address`、`lat`、`lng`、`phone`、`url`、`hours`
- `eligibility`：申請/服務條件
- `apply_steps`：申請方式
- `source_name`、`source_url`、`source_license`、`updated_at`

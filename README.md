# FindAid｜青年共融資源助理

FindAid 是一個以 AI 與雙北公部門公開資料為核心的資源搜尋工具，目標是把「知道有哪些資源」往前推進到「下一步該怎麼做」。它適合用在青年就業、就學、自修空間、法律諮詢、社福支持、租住資訊、共融服務與日常移動等情境。

目前專案提供：
- 需求快篩：先把需求整理成可搜尋的方向
- 資源推薦：從本地 SQLite 資源庫做檢索與排序
- 地圖與附近：顯示具座標的官方點位
- 行動計畫：根據需求與已勾選資源生成下一步
- AI 助手：在資源庫脈絡下回答問題，降低憑空捏造
- 公開資料同步：一鍵同步雙北官方公開資料/API

## 專案定位

FindAid 的中文名稱是「青年共融資源助理」。

它不是單一補助查詢器，而是把不同局處、不同類型的公開資訊整合進同一個搜尋介面，讓使用者可以在一個流程內完成：
- 釐清需求
- 找到可能的資源點
- 篩出適合自己的服務
- 產出實際可執行的下一步

## 已整合的雙北官方資料

以下資料源已於 2026-04-06 驗證可取得，並已接入「公開資料同步」頁面：

- 臺北市政府開放資料｜YouBike 2.0 即時站點資訊  
  API: [tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json](https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json)
- 新北市政府資料開放平臺｜YouBike 2.0 即時站點資訊  
  API: [data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json](https://data.ntpc.gov.tw/api/datasets/010e5b15-3823-4b20-b401-b1cf000550c5/json?size=10000)
- 新北市政府勞工局｜新北市政府所屬就業服務據點  
  API: [data.ntpc.gov.tw/api/datasets/4427db9f-2eb0-4646-a291-e6031d564c4f/json](https://data.ntpc.gov.tw/api/datasets/4427db9f-2eb0-4646-a291-e6031d564c4f/json?size=10000)
- 新北市政府法制局｜新北市法律諮詢服務處所暨時段  
  API: [data.ntpc.gov.tw/api/datasets/a4cfc560-c73f-4e54-aae0-492c13f10de1/json](https://data.ntpc.gov.tw/api/datasets/a4cfc560-c73f-4e54-aae0-492c13f10de1/json?size=10000)
- 新北市政府社會局｜新北市少年福利服務中心名冊  
  API: [data.ntpc.gov.tw/api/datasets/99ad6aba-dc13-47a1-a084-fe773ec5f15f/json](https://data.ntpc.gov.tw/api/datasets/99ad6aba-dc13-47a1-a084-fe773ec5f15f/json?size=10000)
- 新北市政府社會局｜新北市實物銀行分行及領用站一覽表  
  API: [data.ntpc.gov.tw/api/datasets/1c1d0066-a4e7-4753-b8bc-d7728d5f3e04/json](https://data.ntpc.gov.tw/api/datasets/1c1d0066-a4e7-4753-b8bc-d7728d5f3e04/json?size=10000)
- 新北市政府社會局｜新北市身心障礙者服務中心名冊  
  API: [data.ntpc.gov.tw/api/datasets/0c239921-dfca-45e4-a6d1-3a62920ca81b/json](https://data.ntpc.gov.tw/api/datasets/0c239921-dfca-45e4-a6d1-3a62920ca81b/json?size=10000)
- 新北市政府衛生局｜防毒保衛站  
  API: [data.ntpc.gov.tw/api/datasets/58031cc5-31b8-4f34-9953-5c066d66de35/json](https://data.ntpc.gov.tw/api/datasets/58031cc5-31b8-4f34-9953-5c066d66de35/json?size=10000)
- 臺北市立圖書館｜查詢座位狀況 API  
  API: [seat.tpml.edu.tw/sm/service/getAllArea](https://seat.tpml.edu.tw/sm/service/getAllArea)
- 臺北市政府都市發展局｜臺北市社會住宅興建工程進度  
  API: [hms.udd.gov.taipei/api/BigData/project](https://hms.udd.gov.taipei/api/BigData/project)
- 臺北市交通局｜輪行臺北設施資料（捷運站）  
  API: [wheelroute.gov.taipei/wheelrouteApi/api/facility/Get/20](https://wheelroute.gov.taipei/wheelrouteApi/api/facility/Get/20)

## 專案結構

```text
.
├── app.py
├── data/sample/resources.json
├── labmate/
│   ├── app_logic.py
│   ├── config.py
│   ├── db.py
│   ├── llm.py
│   ├── open_data.py
│   └── resources.py
└── smoke_test.py
```

## 安裝

需求：
- Python 3.9+

安裝：

```bash
pip install -r requirements.txt
```

## 環境變數

LLM 設定：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

FindAid 設定：
- `FINDAID_DATABASE_FILE`：預設 `findaid_data.db`
- `FINDAID_OFFLINE=1`：強制離線模式
- `FINDAID_OPEN_DATA_ENABLED=1`：是否顯示公開資料同步頁
- `FINDAID_ALLOW_INSECURE_SSL=1`：若你新增其他來源且遇到 SSL 驗證問題時可啟用
- `FINDAID_OPEN_DATA_TTL_SECONDS`：保留給後續快取控制

相容性說明：
- 舊版 `LABMATE_*` 環境變數目前仍可使用，但新設定建議改用 `FINDAID_*`

## 啟動

```bash
streamlit run app.py
```

啟動後可先進到「公開資料同步」頁，勾選要匯入的資料源，再按「立即同步官方資料」。

補充：
- 針對已內建的雙北官方來源，專案已內建 Python SSL 相容 fallback，避免部分環境下官方憑證鏈驗證失敗導致同步中斷

## 資料模型

FindAid 內部以單一 `resources` 結構整合不同來源，主要欄位如下：

- `id`
- `name`
- `category`
- `audience_tags`
- `description`
- `address`
- `lat`
- `lng`
- `phone`
- `url`
- `hours`
- `eligibility`
- `apply_steps`
- `source_name`
- `source_url`
- `source_license`
- `updated_at`

這個設計的目的是讓來自不同局處的資料，仍能用同一套搜尋、推薦、地圖與 AI 回答流程處理。

## 離線資料

專案內建 `data/sample/resources.json` 作為初始示例資料。

如果 SQLite 目前沒有資料，系統會先灌入示例資料，之後你可以用「公開資料同步」把雙北官方資料寫入資料庫；寫入方式採 `INSERT OR REPLACE`。

## 測試

```bash
python smoke_test.py
```

這個 smoke test 會檢查：
- schema 建立
- sample 資料載入
- 搜尋流程
- 行動計畫生成基本流程

## 授權與資料使用

本專案程式碼授權請依你的 repo 規範另行補充。

公開資料部分請注意：
- 各資料源的授權與更新頻率不同
- 上線前應保留每筆資料的 `source_*` 欄位
- 若要新增更多資料集，優先使用官方公開資料/API，並維持欄位可追溯性

## 後續可擴充方向

- 接入更多臺北市青年、社福、法律與心理健康官方資料集
- 為無座標資料加上正式地理編碼流程
- 新增資源去重、分群與多來源合併規則
- 增加依行政區、對象、時段、是否需預約的篩選器

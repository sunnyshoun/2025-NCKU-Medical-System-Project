# VectorDB 向量資料庫服務

## 概述
本組件提供基於 FAISS 和 Sentence Transformers 的向量搜尋服務，支援眼科知識庫的檢索功能。服務接收查詢問題，生成嵌入向量（embedding），檢索知識庫中最相關的知識點，並返回知識點 ID 與相似度分數，供 Spring 後端整合於 RAG（Retrieval-Augmented Generation）流程的檢索階段。同時支援新增知識點至向量資料庫並更新索引。

## 技術棧
- Python 3.11.2
- FastAPI
- FAISS
- Sentence Transformers（`intfloat/multilingual-e5-large`）

## 檔案結構
```
VectorDB/
├── app/                   # FastAPI 應用程式
│   ├── __init__.py
│   ├── config.py          # 配置參數（如模型名稱、索引路徑）
│   ├── dependencies.py    # 模型與 FAISS 索引初始化
│   ├── faiss_vectorDB.py  # FAISS 向量資料庫核心邏輯
│   ├── main.py            # API 端點定義
│   ├── schemas.py         # Pydantic 模型
├── scripts/               # 獨立運作的腳本
│   ├── knowledge_search.py   # 知識點搜尋彙整
│   ├── vector_embedding.py   # 生成 FAISS 索引
│   ├── vector_search.py   # FAISS 索引搜尋測試
├── data/                  # FAISS 索引和 ID 對應表
│   ├── index_cosine.faiss      # FAISS 索引
│   ├── index_id_mapping.pkl    # ID 對應表
│   ├── vision_health_knowledge_base.json   # 知識點列表
├── requirements.txt       # 依賴清單
├── README.md              # 本文件
```

## 設置與運行
1. **安裝依賴**：
   ```bash
   pip install -r requirements.txt
   ```

2. **準備索引**：
   - 確保 `data/` 包含 `index_cosine.faiss` 和 `index_id_mapping.pkl`。
   - 若需重新生成索引，運行：
     ```bash
     cd scripts
     python vector_embedding.py
     ```
     確保 `data/vision_health_knowledge_base.json` 存在。

3. **啟動服務**：
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## 呼叫 API (REST)

### 端點：搜尋知識點
- **Method**：`GET`
- **URL**：`http://localhost:8000/v1/knowledge`
- **說明**：根據輸入的查詢問題生成嵌入向量，檢索眼科知識庫中最相關的知識點，並返回知識點 ID 與相似度分數。

#### Request
- **Content-Type**：`application/json`
- **Query Parameters**：
  - **query（required）**：查詢問題的文字內容，例如 "SMILE雷射手術全名是什麼?"
  - **top_k（optional）**：返回的相關知識點數量，預設為 5

#### 範例請求
```bash
curl -X GET "http://localhost:8000/v1/knowledge?query=SMILE雷射手術全名是什麼?&top_k=5" \
     -H "Content-Type: application/json"
```

#### Response
- **Status Code**：`200 OK`
- **Content-Type**：`application/json`
- **Response Body**：
  ```json
  {
    "results": [
      {
        "rank": "integer",
        "id": "string",
        "similarity": "float"
      },
      ...
    ],
    "total": "integer",
    "query": "string"
  }
  ```
  - **results**：搜尋結果列表
    - **rank**：結果的排名，從 1 開始
    - **id**：知識點的唯一識別碼（UUID）
    - **similarity**：查詢與知識點的相似度分數，範圍為 0 到 1
  - **total**：返回的結果總數
  - **query**：原始查詢問題

#### 範例回應
```json
{
  "results": [
    {"rank": 1, "id": "57fb4f3c-c544-4465-9ef4-a53e3c7df1d7", "similarity": 0.95},
    {"rank": 2, "id": "c947d930-f8c6-4a77-9e6f-65e1d4249978", "similarity": 0.92},
    {"rank": 3, "id": "e5431414-8030-4463-bdb9-961393cdc53a", "similarity": 0.88},
    {"rank": 4, "id": "b5a38db3-6a5b-4334-85fa-4c1b9f04f425", "similarity": 0.85},
    {"rank": 5, "id": "547116a6-c37f-450d-9a54-795ea2df70a8", "similarity": 0.82}
  ],
  "total": 5,
  "query": "SMILE雷射手術全名是什麼?"
}
```

#### 錯誤回應
- **Status Code**：`400 Bad Request`
  - **說明**：查詢無效，例如 query 為空
  - **Response Body**：
    ```json
    {
      "status": "error",
      "message": "查詢無效",
      "detail": "查詢文本不能為空"
    }
    ```
- **Status Code**：`500 Internal Server Error`
  - **說明**：搜尋時發生伺服器錯誤
  - **Response Body**：
    ```json
    {
      "status": "error",
      "message": "搜尋時發生錯誤",
      "detail": "具體錯誤描述"
    }
    ```

### 端點：新增知識點
- **方法**：`POST`
- **URL**：`http://localhost:8000/v1/knowledge`
- **說明**：新增知識資料到向量資料庫，並更新 FAISS 索引和 ID 對應表。

#### Request
- **Content-Type**：`application/json`
- **Request Body**：
  ```json
  {
    "knowledges": [
      {
        "id": "string",
        "knowledge_point": "string",
        "tags": ["string", ...],
        "summary": "string",
        "source": "string"
      },
      ...
    ]
  }
  ```
  - **knowledges**：知識點列表
    - **id（required）**：知識點的唯一識別碼（UUID）
    - **knowledge_point（required）**：知識點的文字內容
    - **tags（required）**：標籤列表，至少包含一個標籤，用於分類
    - **summary（optional）**：知識點摘要
    - **source（optional）**：知識點來源

#### 範例請求
```bash
curl -X POST "http://localhost:8000/v1/knowledge" \
     -H "Content-Type: application/json" \
     -d '{
           "knowledges": [
             {
               "id": "57fb4f3c-c544-4465-9ef4-a53e3c7df1d7",
               "knowledge_point": "SMILE雷射手術全名是Small Incision Lenticule Extraction",
               "tags": ["眼科", "手術"],
               "summary": "SMILE手術簡介",
               "source": "https://www.xxx.org/eye-health/smile"
             }
           ]
         }'
```

#### Response
- **Status Code**：`201 Created`
- **Content-Type**：`application/json`
- **Response Body**：
  ```json
  {
    "status": "success",
    "message": "知識資料新增成功"
  }
  ```

#### 錯誤回應
- **Status Code**：`422 Unprocessable Entity`
  - **說明**：無效的知識資料，例如 id 或 knowledge_point 為空
  - **Response Body**：
    ```json
    {
      "status": "error",
      "message": "無效的知識資料",
      "detail": "知識 '57fb4f3c-c544-4465-9ef4-a53e3c7df1d7' 的 knowledge_point 不可為空"
    }
    ```
- **Status Code**：`500 Internal Server Error`
  - **說明**：新增知識資料時發生伺服器錯誤
  - **Response Body**：
    ```json
    {
      "status": "error",
      "message": "新增知識資料時發生錯誤",
      "detail": "具體錯誤描述"
    }
    ```

## 注意事項
- FAISS 索引：確保 index_cosine.faiss 與 scripts/vector_embedding.py 生成的格式一致，否則可能導致搜尋錯誤。
- 記憶體需求：載入 intfloat/multilingual-e5-large 模型和 FAISS 索引需要較多記憶體，建議在伺服器環境運行。
- 協同工作：本服務需與 SQL 後端配合，將知識點儲存在 SQL，並確保查詢與知識點儲存的 uuid 一致。
- 資料持久化：新增知識點後，FAISS 索引和 ID 對應表會自動更新並儲存至 data/index_cosine.faiss 和 data/index_id_mapping.pkl。
- 錯誤處理：確保輸入資料符合 Pydantic 模型定義，避免因格式錯誤導致 API 失敗。
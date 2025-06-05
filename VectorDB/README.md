# VectorDB 向量資料庫服務

## 概述
本組件提供基於 FAISS 和 Sentence Transformers 的向量搜尋服務，接受查詢問題，生成嵌入向量，檢索眼科知識庫中的相關知識點，回傳知識 ID 和相似度分數給 Spring 後端，支援 RAG 流程的檢索階段。

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
│   ├── main.py            # API 端點定義
│   ├── config.py          # 配置參數
│   ├── vector_search.py   # 搜尋邏輯
│   ├── dependencies.py    # 模型和索引初始化
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
- **方法**：`POST`
- **URL**：`http://localhost:8000/search`
- **說明**：根據輸入的查詢問題生成嵌入向量，檢索眼科知識庫中最相關的知識點，並返回知識點 ID 與相似度分數。

#### Request
- **Content-Type**：`application/json`
- **Request Body**：
  ```json
  {
    "query": "string",
    "top_k": "integer"
  }
  ```
  - **query**：查詢問題的文字內容，例如 "SMILE雷射手術全名是什麼?"
  - **top_k**：返回的相關知識點數量，預設為 5。

#### 範例請求
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "SMILE雷射手術全名是什麼?", "top_k": 5}'
```

#### Response
- **Status Code**：`200 OK`
- **Content-Type**：`application/json`
- **Response Body**：
  ```json
  [
    {
      "rank": "integer",
      "id": "string",
      "similarity": "float"
    },
    ...
  ]
  ```
  - **rank**：結果的排名，從 1 開始。
  - **id**：知識點的唯一識別碼（UUID）。
  - **similarity**：查詢與知識點的相似度分數，範圍為 0 到 1。

#### 範例回應
```json
[
  {"rank": 1, "id": "uuid-1234", "similarity": 0.95},
  {"rank": 2, "id": "uuid-5678", "similarity": 0.92},
  {"rank": 3, "id": "uuid-9012", "similarity": 0.88},
  {"rank": 4, "id": "uuid-3456", "similarity": 0.85},
  {"rank": 5, "id": "uuid-7890", "similarity": 0.82}
]
```

## 注意事項
- 確保 FAISS 索引與 `scripts/vector_embedding.py` 生成的格式一致。
- 服務需與 Spring 後端的問題向量化模組協同工作。
- 模型載入可能需要較多記憶體，建議在伺服器環境運行。
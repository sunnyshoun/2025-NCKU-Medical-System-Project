# VectorDB 向量資料庫服務

## 概述
本組件提供基於 FAISS 和 Sentence Transformers 的向量搜尋服務，支援眼科知識庫的檢索功能。服務通過 gRPC 協議接收查詢問題，生成嵌入向量，檢索知識庫中最相關的知識點，並返回知識點 ID 與相似度分數，供後端整合於 RAG（Retrieval-Augmented Generation）流程的檢索階段。同時支援新增知識點至向量資料庫並更新索引。

## 技術棧
- Python 3.11.2
- gRPC
- FAISS
- Sentence Transformers（`intfloat/multilingual-e5-large`）
- Docker
- PostgreSQL（用於知識點儲存）

## 檔案結構
```
VectorDB/
├── app/                   # gRPC 應用程式
│   ├── __init__.py
│   ├── config.py          # 配置參數（如模型名稱、索引路徑）
│   ├── dependencies.py    # 模型與 FAISS 索引初始化
│   ├── faiss_vectorDB.py  # FAISS 向量資料庫核心邏輯
│   ├── main.py            # gRPC 服務定義
│   ├── schemas.py         # Pydantic 模型
│   ├── proto/
│   │   ├── vector_db.proto # Protobuf 定義
│   ├── vector_db_pb2.py   # 生成的 Protobuf 消息
│   ├── vector_db_pb2_grpc.py # 生成的 gRPC 服務
├── scripts/               # 獨立運作的腳本
│   ├── knowledge_search.py   # 知識點搜尋彙整
│   ├── vector_embedding.py   # 生成 FAISS 索引
│   ├── vector_search.py   # FAISS 索引搜尋測試
│   ├── grpc_client.py     # gRPC 客戶端測試
│   ├── download_model.py  # 下載並儲存 Sentence Transformer 模型
│   ├── insert_knowledge.py # 將知識點插入 PostgreSQL 資料庫
├── data/                  # FAISS 索引和 ID 對應表
│   ├── index_cosine.faiss      # FAISS 索引
│   ├── index_id_mapping.pkl    # ID 對應表
│   ├── vision_health_knowledge_base.json   # 知識點列表（JSON 格式）
│   ├── knowledge.dump      # 知識點資料庫備份（PostgreSQL dump）
├── model/                 # 儲存 Sentence Transformer 模型
│   ├── multilingual-e5-large/  # 本地模型文件
├── requirements.txt       # 依賴清單
├── Dockerfile             # 應用程式 Docker 配置文件
├── Dockerfile.base        # 基礎映像 Docker 配置文件
├── README.md              # 本文件
```

## 設置與運行

### 環境準備
1. **安裝依賴**：
   ```bash
   pip install -r requirements.txt
   ```

2. **下載模型**：
   - 下載並儲存 Sentence Transformer 模型：
     ```bash
     python scripts/download_model.py
     ```
   - 模型將儲存至 `model/multilingual-e5-large/`。

3. **生成 gRPC 代碼**：
   ```bash
   python -m grpc_tools.protoc -Iapp/proto --python_out=app --grpc_python_out=app app/proto/vector_db.proto
   ```

4. **準備索引**：
   - 確保 `data/` 包含 `index_cosine.faiss` 和 `index_id_mapping.pkl`。
   - 若需重新生成索引，運行：
     ```bash
     cd scripts
     python vector_embedding.py
     ```
     確保 `data/vision_health_knowledge_base.json` 存在。

5. **準備 PostgreSQL 資料庫**：
   - 確保 PostgreSQL 服務運行並配置正確（參見 `insert_knowledge.py` 中的環境變數）。
   - 將知識點數據插入資料庫：
     ```bash
     python scripts/insert_knowledge.py
     ```
     - 預設從 `data/vision_health_knowledge_base.json` 讀取數據並插入 `knowledges` 表。
     - 可選：使用 `data/knowledge.dump` 恢復資料庫備份（需與 PostgreSQL 版本相容）：
       ```bash
       psql -h <POSTGRES_HOST> -U <POSTGRES_USER> -d postgres -f data/knowledge.dump
       ```

### 使用 Docker 運行
1. **構建基礎映像**：
   ```bash
   docker build -t vectordb-base:latest -f Dockerfile.base .
   ```

2. **構建應用映像**：
   ```bash
   docker build -t vectordb:latest -f Dockerfile .
   ```

3. **運行容器**：
   ```bash
   docker run -p 50051:50051 -v $(pwd)/data:/vectordb/data -v $(pwd)/model:/vectordb/model -e POSTGRES_HOST=<postgres_host> -e POSTGRES_PORT=<postgres_port> -e POSTGRES_USER=<postgres_user> -e POSTGRES_PASSWORD=<postgres_password> vectordb:latest
   ```
   - 將主機的 `data/` 和 `model/` 目錄掛載到容器，確保索引和模型可用。
   - 設置 PostgreSQL 環境變數以連接到資料庫。
   - 服務運行在 `localhost:50051`。

### 本地運行
1. **啟動 gRPC 服務**：
   ```bash
   python app/main.py
   ```
   服務默認運行在 `localhost:50051`。

2. **測試服務**：
   使用提供的客戶端腳本：
   ```bash
   python scripts/grpc_client.py
   ```
   或使用 gRPC 測試工具（如 `grpcurl`）：
   ```bash
   grpcurl -plaintext -import-path app/proto -proto vector_db.proto -d '{"query": "SMILE雷射手術全名是什麼?", "top_k": 5}' localhost:50051 vector_db.VectorDBService/SearchKnowledge
   ```

## 呼叫 API (gRPC)

### 響應規範
所有 gRPC 方法返回包含以下字段的響應：
- `status`: 表示請求結果，`"success"` 表示成功，`"error"` 表示失敗。
- `message`: 提供成功提示或錯誤詳情。
- 具體數據字段（如 `results` 或 `new_ids`）。

### 方法：SearchKnowledge
- **說明**：根據輸入的查詢問題生成嵌入向量，檢索眼科知識庫中最相關的知識點，並返回知識點 ID 與相似度分數。
- **輸入**：
  ```protobuf
  message SearchRequest {
    string query = 1; // 查詢問題的文字內容
    int32 top_k = 2;  // 返回的相關知識點數量，預設 5
  }
  ```
- **輸出**：
  ```protobuf
  message SearchResponse {
    string status = 1; // "success" 或 "error"
    string message = 2; // 錯誤時提供詳細信息
    repeated SearchResult results = 3; // 搜尋結果列表
  }
  message SearchResult {
    int32 rank = 1;       // 排名
    string id = 2;        // 知識點 ID
    float similarity = 3; // 相似度分數
  }
  ```

#### 範例請求（使用 grpcurl）
```bash
grpcurl -plaintext -import-path app/proto -proto vector_db.proto -d '{"query": "SMILE雷射手術全名是什麼?", "top_k": 5}' localhost:50051 vector_db.VectorDBService/SearchKnowledge
```

#### 範例響應
```json
{
  "status": "success",
  "message": "Search completed successfully",
  "results": [
    {
      "rank": 1,
      "id": "117239c6-483b-4d7a-a539-5131e51073d3",
      "similarity": 0.8952757120132446
    },
    {
      "rank": 2,
      "id": "b489eb14-da61-4521-bb74-1350851dbc31",
      "similarity": 0.8832905888557434
    }
  ]
}
```

### 方法：AppendKnowledge
- **說明**：新增知識資料到向量資料庫，並更新 FAISS 索引和 ID 對應表。
- **输入**：
  ```protobuf
  message AppendRequest {
    repeated KnowledgeData knowledges = 1; // 知識點列表
  }
  message KnowledgeData {
    string id = 1;            // 知識點 ID
    string knowledge_point = 2; // 知識點內容
    repeated string tags = 3;   // 標籤
    string summary = 4;        // 摘要
    string source = 5;         // 來源
  }
  ```
- **輸出**：
  ```protobuf
  message AppendResponse {
    string status = 1;         // "success" 或 "error"
    string message = 2;        // 錯誤信息
    repeated string new_ids = 3; // 新增的知識點 ID
  }
  ```

#### 範例請求（使用 grpcurl）
```bash
grpcurl -plaintext -import-path app/proto -proto vector_db.proto -d '{"knowledges": [{"id": "57fb4f3c-c544-4465-9ef4-a53e3c7df1d7", "knowledge_point": "SMILE雷射手術全名是Small Incision Lenticule Extraction", "tags": ["眼科", "手術"], "summary": "SMILE手術簡介", "source": "https://www.xxx.org/eye-health/smile"}]}' localhost:50051 vector_db.VectorDBService/AppendKnowledge
```

#### 範例響應
```json
{
  "status": "success",
  "message": "知識資料新增成功",
  "new_ids": ["57fb4f3c-c544-4465-9ef4-a53e3c7df1d7"]
}
```

## 使用 Postman 測試

### 前置條件
- 安裝 Postman 8.0 或更高版本（下載：https://www.postman.com/downloads/）。
- 確保 gRPC 服務運行在 `localhost:50051`（執行 `docker run` 或 `python app/main.py`）。
- 確保 PostgreSQL 資料庫已運行並包含知識點數據（通過 `insert_knowledge.py` 或 `knowledge.dump` 導入）。
- 準備 `app/proto/vector_db.proto` 文件。

### 測試步驟
1. **創建 gRPC 請求**：
   - 在 Postman 中選擇 **New > gRPC Request**。
   - 輸入服務地址：`localhost:50051`（使用 plaintext）。
   - 導入 `app/proto/vector_db.proto` 文件。
   - 選擇 `vector_db.VectorDBService` 下的方法（`SearchKnowledge` 或 `AppendKnowledge`）。

2. **測試 SearchKnowledge**：
   - 輸入請求：
     ```json
     {
       "query": "SMILE雷射手術全名是什麼?",
       "top_k": 5
     }
     ```
   - 點擊 **Invoke**，檢查響應是否包含 `status`, `message`, 和 `results`。

3. **測試 AppendKnowledge**：
   - 輸入請求：
     ```json
     {
       "knowledges": [
         {
           "id": "57fb4f3c-c544-4465-9ef4-a53e3c7df1d7",
           "knowledge_point": "SMILE雷射手術全名是Small Incision Lenticule Extraction",
           "tags": ["眼科", "手術"],
           "summary": "SMILE手術簡介",
           "source": "https://www.xxx.org/eye-health/smile"
         }
       ]
     }
     ```
   - 點擊 **Invoke**，檢查響應是否包含 `status`, `message`, 和 `new_ids`。

4. **錯誤測試**：
   - 測試無效輸入（如空 `query` 或無效 `top_k`），確保返回正確的錯誤響應。
     ```json
     {
       "query": "",
       "top_k": 5
     }
     ```
     預期響應：
     ```json
     {
       "status": "error",
       "message": "查詢文本不能為空",
       "results": []
     }
     ```

5. **保存請求**：
   - 將測試用例保存到 Postman Collection，方便重複測試。

## 注意事項
- **FAISS 索引**：確保 `index_cosine.faiss` 與 `scripts/vector_embedding.py` 生成的格式一致。
- **模型儲存**：確保 `model/multilingual-e5-large/` 包含下載的模型文件，可通過 `scripts/download_model.py` 生成。
- **資料庫同步**：執行 `insert_knowledge.py` 後，需運行 `vector_embedding.py` 更新 FAISS 索引，確保向量資料庫與 PostgreSQL 一致。
- **記憶體需求**：載入 `intfloat/multilingual-e5-large` 模型和 FAISS 索引需要較多記憶體，建議在伺服器環境運行。
- **協同工作**：本服務需與 SQL 後端配合，確保知識點的 UUID 一致。
- **資料持久化**：新增知識點後，FAISS 索引和 ID 對應表會自動更新並儲存至 `data/index_cosine.faiss` 和 `data/index_id_mapping.pkl`。
- **Docker 運行**：確保 `data/` 和 `model/` 目錄已掛載到容器中，以保持資料和模型的持久化。PostgreSQL 環境變數需正確配置。
- **錯誤處理**：gRPC 服務內建錯誤處理，返回標準化的 `status` 和 `message`。
- **安全性**：生產環境應啟用 gRPC 的 TLS 認證，並確保 PostgreSQL 連線使用安全憑證。
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

## 與 Spring 後端整合
- Spring 後端通過 POST 請求呼叫 `/search` 端點：
  ```bash
  curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d '{"query": "SMILE雷射手術全名是什麼?", "top_k": 5}'
  ```
- 回應格式：
  ```json
  [
    {"rank": 1, "id": "uuid", "similarity": 0.95},
    {"rank": 2, "id": "uuid", "similarity": 0.92},
    ...
  ]
  ```

## 注意事項
- 確保 FAISS 索引與 `scripts/vector_embedding.py` 生成的格式一致。
- 服務需與 Spring 後端的問題向量化模組協同工作。
- 模型載入可能需要較多記憶體，建議在伺服器環境運行。
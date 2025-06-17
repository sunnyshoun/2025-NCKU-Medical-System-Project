# Backend 後端服務

## 概述
本專案後端基於 Spring Boot 構建，整合了 PostgreSQL 資料庫和 VectorDB 向量搜尋服務，提供使用者管理、視力記錄管理和AI問答功能。系統採用微服務架構，支援 Docker 容器化部署。

## 技術架構
- **主服務**: Spring Boot 3.x + Java 21
- **資料庫**: PostgreSQL 16
- **向量搜尋**: VectorDB (gRPC) + FAISS + Sentence Transformers
- **AI服務**: Grok API 整合
- **容器化**: Docker + Docker Compose

## 系統組件
1. **Spring Boot 應用** (`spring-app`) - 主要後端服務
2. **PostgreSQL** (`postgres`) - 資料持久化
3. **VectorDB** (`vectordb`) - 向量搜尋與知識庫

## 環境配置

### 必要環境變數

#### Spring Boot 應用
```bash
# 資料庫連線
SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/postgres
SPRING_DATASOURCE_USERNAME=postgres
SPRING_DATASOURCE_PASSWORD=mysecretpassword

# VectorDB gRPC 連線
VECTORDB_HOST=vectordb
VECTORDB_PORT=50051

# Grok AI API 配置
GROK_API_KEY=your_xai_key
GROK_API_URL=https://api.x.ai/v1/chat/completions
GROK_MODEL=grok-3-latest

# 聊天設定
CHAT_MAX_MESSAGES=20
VECTOR_SEARCH_TOP_K=5
```

#### PostgreSQL 配置
```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=postgres
```

#### VectorDB 配置
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
```

## 快速部署

### 使用 Docker Compose (推薦)

1. **克隆專案並進入後端目錄**
```bash
git clone <repository-url>
cd Backend
```

2. **設定環境變數 (可選)**
建立 `.env` 檔案：
```bash
# .env
GROK_API_KEY=your_actual_xai_api_key
POSTGRES_PASSWORD=your_secure_password
```

詳情請見：[Env Example](./.envExample)


3. **啟動所有服務**
```bash
docker-compose up -d
```

4. **驗證服務狀態**
```bash
docker-compose ps
```

### 服務端點
- **Spring Boot API**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **VectorDB gRPC**: localhost:50051

## 手動部署

### 前置需求
- Java 21+
- Maven 3.9+
- PostgreSQL 16+
- Python 3.11+ (for VectorDB)

### 1. 資料庫設置
```bash
# 啟動 PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  postgres:16

# 執行初始化腳本
psql -h localhost -U postgres -d postgres -f PostgreSQL/init/init.sql
```

### 2. VectorDB 服務
```bash
cd VectorDB

# 安裝依賴
pip install -r requirements.txt

# 下載模型
python scripts/download_model.py

# 生成 gRPC 代碼
python -m grpc_tools.protoc -Iapp/proto --python_out=app --grpc_python_out=app app/proto/vector_db.proto

# 初始化知識庫 (可選)
python scripts/insert_knowledge.py

# 生成向量索引 (可選)
python scripts/vector_embedding.py

# 啟動服務
python app/main.py
```

### 3. Spring Boot 應用
```bash
# 設定環境變數
export SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/postgres
export SPRING_DATASOURCE_USERNAME=postgres
export SPRING_DATASOURCE_PASSWORD=mysecretpassword
export VECTORDB_HOST=localhost
export VECTORDB_PORT=50051
export GROK_API_KEY=your_xai_key

# 編譯並運行
mvn clean install
java -jar target/*.jar
```

## 配置說明

### application.yml 主要配置
```yaml
server:
  port: 8080

spring:
  datasource:
    username: ${SPRING_DATASOURCE_USERNAME:postgres}
    password: ${SPRING_DATASOURCE_PASSWORD:mysecretpassword}
    url: ${SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/postgres}
  jpa:
    hibernate:
      ddl-auto: update

grok:
  api:
    key: ${GROK_API_KEY:your_xai_key}
    url: ${GROK_API_URL:https://api.x.ai/v1/chat/completions}
  model: ${GROK_MODEL:grok-3-latest}

vectordb:
  host: ${VECTORDB_HOST:vectordb}
  port: ${VECTORDB_PORT:50051}
```

### Docker Compose 網路配置
```yaml
networks:
  net:
    driver: bridge
```

所有服務均運行在同一網路中，服務間可使用容器名稱進行通訊。

## 資料庫架構

### 主要資料表
- `users` - 使用者基本資訊
- `roles` - 角色管理
- `user_roles` - 使用者角色關聯
- `records` - 視力檢測記錄
- `knowledges` - 眼科知識庫

### 資料備份與恢復
```bash
# 備份
docker exec postgres pg_dump -U postgres postgres > backup.sql

# 恢復
docker exec -i postgres psql -U postgres postgres < backup.sql
```

## 監控與維護

### 日誌查看
```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f spring-app
docker-compose logs -f postgres
docker-compose logs -f vectordb
```

### 健康檢查
- Spring Boot Actuator: http://localhost:8080/actuator/health
- PostgreSQL: `docker exec postgres pg_isready`
- VectorDB: gRPC health check (需要實作)

### 常見問題排除

1. **服務啟動失敗**
   - 檢查端口是否被佔用
   - 確認環境變數設定正確
   - 查看容器日誌

2. **資料庫連線問題**
   - 確認 PostgreSQL 服務已啟動
   - 檢查連線字串和憑證
   - 驗證網路連通性

3. **VectorDB 無法連線**
   - 確認 gRPC 服務已啟動
   - 檢查模型和索引檔案是否存在
   - 驗證 PostgreSQL 資料是否已初始化

## 生產環境建議

### 安全性
- 使用強密碼並定期更換
- 啟用 HTTPS/TLS
- 設定防火牆規則
- 定期更新映像版本

### 效能調優
- 設定適當的記憶體限制
- 配置連線池參數
- 啟用 PostgreSQL 查詢最佳化
- 監控資源使用情況

### 備份策略
- 定期備份資料庫
- 備份 VectorDB 索引檔案
- 測試備份恢復流程
- 建立災難恢復計畫

## API 文件
詳細的 REST API 文件請參閱 `docs/rest-api.md`。

## 版本資訊
- Spring Boot: 3.x
- Java: 21
- PostgreSQL: 16
- Python: 3.11.2
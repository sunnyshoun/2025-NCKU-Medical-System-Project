**docker-compose.yml變更**

#### ** 1. `postgres volumes` 更新 **

```yaml
services:
  postgres:
    # ... (原有 postgres 服務設定，此處省略) ...
    volumes:
      - ./PostgreSQL/backups:/backups
      - ./PostgreSQL/config/:/etc/postgresql/ # 修正：將本地的 config 資料夾映射到容器內，避免單檔映射問題
      - ./PostgreSQL/init:/docker-entrypoint-initdb.d/
      - ./testfiles:/testfiles # 新增：掛載 testfiles 資料夾，如果不需要可移除
    # ... (原有postgres 服務設定，省略) ...
```
#### ** 2. `Spring Boot服務` **

```yaml
spring-app: # 服務名稱，其他 Docker 容器 (如 postgres) 可以透過這個名稱訪問它
    container_name: spring-server # 容器運行起來後，其名稱為 'spring-server'
    build: . # 關鍵：告訴 Docker Compose 在當前目錄 (專案根目錄) 查找 Dockerfile 來構建映像檔
    ports: # 埠號映射：將主機的 8080 埠映射到容器的 8080 埠，供外部訪問
      - "8080:8080"
    depends_on: # 關鍵：確保 `postgres` 服務在 `spring-app` 啟動前已經運行，保證資料庫可用
      - postgres
    environment: # 設定 Spring Boot 應用程式的環境變數，這些會覆蓋 `application.yml` 中的同名設定
      SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/postgres # 資料庫 URL：指向 Docker 網路中的 'postgres' 服務和 'postgres' 資料庫
      SPRING_DATASOURCE_USERNAME: postgres # 資料庫用戶名
      SPRING_DATASOURCE_PASSWORD: mysecretpassword # 資料庫密碼
    networks: # 將此服務連接到名為 'net' 的網路，以便與 `postgres` 容器通信
      - net
    restart: unless-stopped # 容器停止後（除非手動停止），會自動重啟
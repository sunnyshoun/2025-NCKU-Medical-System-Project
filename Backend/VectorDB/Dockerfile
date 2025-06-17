# VectorDB Application Dockerfile
FROM vectordb-base:latest

# 創建非 root 用戶和必要目錄
RUN groupadd -r vectordb && useradd -r -g vectordb vectordb \
    && mkdir -p /vectordb/data /vectordb/models /vectordb/scripts \
    && chown -R vectordb:vectordb /vectordb

# 設定工作目錄
WORKDIR /vectordb

# 複製應用程式碼和腳本
COPY --chown=vectordb:vectordb app/ ./app/
COPY --chown=vectordb:vectordb scripts/ ./scripts/

# 生成 gRPC 代碼（在切換用戶前執行，確保有寫入權限）
RUN python -m grpc_tools.protoc \
    -I app/proto \
    --python_out=app \
    --grpc_python_out=app \
    app/proto/vector_db.proto \
    && chown -R vectordb:vectordb app/

# 確保腳本具有執行權限
RUN chmod +x app/main.py scripts/download_model.py

# 執行模型下載腳本（在切換用戶前，以 root 權限執行）
RUN python3 scripts/download_model.py

# 確保下載的模型檔案擁有者正確
RUN chown -R vectordb:vectordb /vectordb

# 切換到非 root 用戶
USER vectordb

# 定義啟動命令
CMD ["python3", "app/main.py"]
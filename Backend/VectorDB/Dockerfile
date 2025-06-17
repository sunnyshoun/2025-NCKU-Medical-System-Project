# 使用預安裝依賴的基礎映像
FROM vectordb-base:latest

# 設定工作目錄
WORKDIR /vectordb

# 複製應用程式碼、資料和模型
COPY app/ ./app/

# 生成 gRPC 代碼，直接輸出到 app/ 目錄
RUN python -m grpc_tools.protoc -I app/proto --python_out=app --grpc_python_out=app app/proto/vector_db.proto

# 定義啟動命令
CMD ["python3", "app/main.py"]
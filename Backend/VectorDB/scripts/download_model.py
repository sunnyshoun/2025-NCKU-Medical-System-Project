import os
from sentence_transformers import SentenceTransformer

# 指定模型名稱
model_name = 'intfloat/multilingual-e5-large'
# 指定本地儲存路徑
local_model_path = 'models/multilingual-e5-large'

# 檢查模型是否已存在
if os.path.exists(local_model_path):
    print(f"模型已存在於 {local_model_path}")
    # 載入本地模型
    model = SentenceTransformer(local_model_path)
    print("已載入本地模型")
else:
    print(f"模型不存在，開始下載 {model_name}...")
    
    # 確保父目錄存在
    os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
    
    try:
        # 下載並儲存模型
        model = SentenceTransformer(model_name)
        model.save(local_model_path)
        print(f"模型已成功下載並儲存至 {local_model_path}")
    except Exception as e:
        print(f"下載模型時發生錯誤: {e}")
        raise

# 驗證模型是否可用
try:
    # 測試編碼功能
    test_sentence = "這是一個測試句子"
    embedding = model.encode(test_sentence)
    print(f"模型載入成功，測試句子維度: {embedding.shape}")
except Exception as e:
    print(f"模型測試失敗: {e}")
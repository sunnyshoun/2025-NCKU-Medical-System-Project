from sentence_transformers import SentenceTransformer

# 指定模型名稱
model_name = 'intfloat/multilingual-e5-large'
# 指定本地儲存路徑
local_model_path = 'models/multilingual-e5-large'

# 下載並儲存模型
model = SentenceTransformer(model_name)
model.save(local_model_path)
print(f"模型已儲存至 {local_model_path}")
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# --- 配置路徑 ---
MODEL_NAME = 'intfloat/multilingual-e5-large'
FAISS_INDEX_PATH = 'data/index_cosine.faiss'
ID_MAPPING_PATH = 'data/index_id_mapping.pkl'

# --- 載入模型與索引 ---
print(f"載入模型: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)
print("模型載入完成。")

print(f"載入 FAISS 索引: {FAISS_INDEX_PATH}...")
index = faiss.read_index(FAISS_INDEX_PATH)
print(f"索引載入完成，共有 {index.ntotal} 筆向量。")

print(f"載入 ID 對應表: {ID_MAPPING_PATH}...")
with open(ID_MAPPING_PATH, 'rb') as f:
    mapping = pickle.load(f)

index_to_id = mapping["index_to_id"]

# --- 查詢處理函數 ---
def search(query_text, top_k=5):
    print(f"\n查詢句子: \"{query_text}\"")
    
    # 產生查詢 embedding，並正規化以符合 cosine similarity
    embedding = model.encode([query_text], normalize_embeddings=True)
    embedding_np = np.array(embedding).astype('float32')

    # 搜索 top_k 相似項
    similarities, indices = index.search(embedding_np, top_k)

    for rank, (idx, score) in enumerate(zip(indices[0], similarities[0])):
        if idx == -1:
            continue
        matched_id = index_to_id[idx]
        print(f"Top {rank+1}: ID = {matched_id}, 相似度 = {score:.4f}")

if __name__ == "__main__":
    query = "SMILE雷射手術全名是什麼?"
    results = search(query)

    print("\n查詢結果：")
    for item in results:
        print(f"Top {item['rank']}: ID = {item['id']}, 相似度 = {item['similarity']:.4f}")

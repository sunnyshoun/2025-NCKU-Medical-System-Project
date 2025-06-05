import json
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

# --- 配置 ---
MODEL_NAME = 'intfloat/multilingual-e5-large'
JSON_FILE_PATH = 'data/vision_health_knowledge_base.json'
FAISS_INDEX_PATH = 'data/index_cosine.faiss'
ID_MAPPING_PATH = 'data/index_id_mapping.pkl'
BATCH_SIZE = 32

# --- 載入模型 ---
print(f"載入模型: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)
print("模型載入完成。")

# --- 載入並處理 JSON 資料 ---
print(f"載入 JSON 資料: {JSON_FILE_PATH}...")
try:
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"錯誤: 找不到 JSON 檔案 {JSON_FILE_PATH}")
    exit()
except json.JSONDecodeError:
    print(f"錯誤: JSON 檔案格式錯誤 {JSON_FILE_PATH}")
    exit()

if not data:
    print("錯誤: JSON 檔案為空。")
    exit()
print(f"成功載入 {len(data)} 筆資料。")

texts_to_embed = []
original_ids = []
for item in data:
    combined_text = f"{item.get('knowledge_points', '')} {item.get('summary', '')}".strip()
    if combined_text:
        texts_to_embed.append(combined_text)
        original_ids.append(item['id'])
    else:
        print(f"警告: ID {item.get('id')} 的 knowledge_points 或 summary 為空，已跳過。")

if not texts_to_embed:
    print("錯誤: 沒有可供 embedding 的有效文本資料。")
    exit()
print(f"準備 embedding {len(texts_to_embed)} 筆文本...")

# --- 生成 Embeddings ---
print("開始生成 embeddings...")
embeddings = model.encode(texts_to_embed, batch_size=BATCH_SIZE, show_progress_bar=True, normalize_embeddings=True)
embeddings_np = np.array(embeddings).astype('float32')
print(f"Embeddings 生成完成，形狀: {embeddings_np.shape}")

# --- 建立 FAISS 索引 ---
dimension = embeddings_np.shape[1]
index = faiss.IndexFlatIP(dimension)  # 使用 Inner Product = Cosine 相似度（需 normalize）
index.add(embeddings_np)
print(f"FAISS 索引建立完成，共包含 {index.ntotal} 個向量。")

# --- 儲存 FAISS 索引 ---
print(f"儲存 FAISS 索引至 {FAISS_INDEX_PATH}...")
faiss.write_index(index, FAISS_INDEX_PATH)
print("索引儲存完成。")

# --- 建立並儲存 ID 對應表為 Pickle ---
print(f"儲存 ID 對應表至 {ID_MAPPING_PATH}...")
index_id_mapping = {
    "index_to_id": {i: id_ for i, id_ in enumerate(original_ids)},
    "id_to_index": {id_: i for i, id_ in enumerate(original_ids)}
}
with open(ID_MAPPING_PATH, 'wb') as f_pickle:
    pickle.dump(index_id_mapping, f_pickle)
print("ID 對應表 (Pickle) 儲存完成。")

print("全部處理完成！")

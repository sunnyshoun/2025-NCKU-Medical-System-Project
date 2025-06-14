import uuid
import faiss
import numpy as np
import pickle
from typing import List
from sentence_transformers import SentenceTransformer
from schemas import SearchResult, AppendRequest
from config import MODEL_NAME, FAISS_INDEX_PATH, ID_MAPPING_PATH, BATCH_SIZE

class FAISSVectorDB:
    def __init__(self):
        print("正在初始化向量資料庫...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(ID_MAPPING_PATH, 'rb') as f:
            mapping = pickle.load(f)
        self.index_to_id = mapping["index_to_id"]
        self.id_to_index = mapping["id_to_index"]
        print("初始化成功")

    def search(self, query_text: str, top_k: int) -> List[SearchResult]:
        """
        搜尋與查詢文本最相似的 top_k 筆資料。
        """
        if not query_text.strip():
            raise ValueError("查詢文本不能為空")
        if not 1 <= top_k <= 50:
            raise ValueError("top_k 必須在 1 ~ 50 之間")
        
        print(f"\nQuery text: \"{query_text}\"")
        
        # 生成查詢 embedding
        embedding = self.model.encode([query_text], normalize_embeddings=True)
        embedding_np = np.array(embedding).astype('float32')

        # 搜尋 top_k 相似的項目
        similarities, indices = self.faiss_index.search(embedding_np, top_k)

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], similarities[0])):
            if idx == -1:
                continue
            matched_id = self.index_to_id[idx]
            results.append(SearchResult(rank=rank+1, id=matched_id, similarity=float(score)))
        
        return results

    def append_knowledge(self, append_data: AppendRequest) -> List[str]:
        """
        新增知識資料到向量資料庫。
        """
        if not append_data.knowledges:
            raise ValueError("新資料為空")

        texts_to_embed = []
        new_ids = []
        for item in append_data.knowledges:
            if not item.id:
                raise ValueError(f"知識列表中包含空的 id")
            elif not item.knowledge_point:
                raise ValueError(f"知識 '{item.id}' 的 knowledge_point 不可為空")
            elif len(item.tags) == 0:
                raise ValueError(f"知識 '{item.id}' 的 tags 不可為空")
            
            combined_text = f"{item.knowledge_point} tags:[{', '.join(item.tags)}]".strip()
            texts_to_embed.append(combined_text)
            new_ids.append(item.id)

        if not texts_to_embed:
            raise ValueError("沒有可供 embedding 的有效文本資料")

        try:
            # 生成 embeddings
            new_embeddings = self.model.encode(texts_to_embed, batch_size=BATCH_SIZE, 
                                            show_progress_bar=True, normalize_embeddings=True)
            new_embeddings_np = np.array(new_embeddings).astype('float32')

            # 更新 FAISS 索引
            start_index = self.faiss_index.ntotal
            self.faiss_index.add(new_embeddings_np)

            # 更新 ID 對應表
            for i, new_id in enumerate(new_ids):
                index = start_index + i
                self.index_to_id[index] = new_id
                self.id_to_index[new_id] = index

            # 儲存更新
            faiss.write_index(self.faiss_index, FAISS_INDEX_PATH)

            index_id_mapping = {
                "index_to_id": self.index_to_id,
                "id_to_index": self.id_to_index
            }
            with open(ID_MAPPING_PATH, 'wb') as f_pickle:
                pickle.dump(index_id_mapping, f_pickle)

            return new_ids
        except Exception as e:
            raise RuntimeError(f"新增知識資料時發生錯誤: {str(e)}")
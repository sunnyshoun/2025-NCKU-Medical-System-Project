import faiss
import pickle
from sentence_transformers import SentenceTransformer
from .config import MODEL_NAME, FAISS_INDEX_PATH, ID_MAPPING_PATH

class FAISSVectorDB():
    def __init__(self):
        print("正在初始化向量資料庫...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(ID_MAPPING_PATH, 'rb') as f:
            mapping = pickle.load(f)
        self.index_to_id = mapping["index_to_id"]
        self.id_to_index = mapping["id_to_index"]
        print("初始化成功")

faiss_vector_db = FAISSVectorDB()

def get_vector_db():
    return faiss_vector_db
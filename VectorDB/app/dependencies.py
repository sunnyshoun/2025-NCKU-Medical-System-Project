import faiss
import pickle
from sentence_transformers import SentenceTransformer
from .config import MODEL_NAME, FAISS_INDEX_PATH, ID_MAPPING_PATH

class FAISSVectorDB():
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        with open(ID_MAPPING_PATH, 'rb') as f:
            mapping = pickle.load(f)
        self.index_to_id = pickle.load(mapping["index_to_id"])
        self.id_to_index = pickle.load(mapping["id_to_index"])

def get_vector_db():
    return FAISSVectorDB()
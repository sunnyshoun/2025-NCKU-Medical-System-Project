import numpy as np
from typing import List
from .schemas import SearchResponse

def search(query_text: str, top_k: int, model, index, index_to_id) -> List[SearchResponse]:
    print(f"\nQuery text: \"{query_text}\"")
    
    # Generate query embedding and normalize for cosine similarity
    embedding = model.encode([query_text], normalize_embeddings=True)
    embedding_np = np.array(embedding).astype('float32')

    # Search top_k similar items
    similarities, indices = index.search(embedding_np, top_k)

    results = []
    for rank, (idx, score) in enumerate(zip(indices[0], similarities[0])):
        if idx == -1:
            continue
        matched_id = index_to_id[idx]
        results.append(SearchResponse(rank=rank+1, id=matched_id, similarity=float(score)))
        print(f"Top {rank+1}: ID = {matched_id}, Similarity = {score:.4f}")

    return results
from fastapi import FastAPI, Depends
from .schemas import SearchRequest, SearchResponse
from .vector_search import search
from .dependencies import get_vector_db
from typing import List

app = FastAPI(title="VectorDB Search API", description="A FastAPI service for vector search using FAISS", version="1.0.0")

@app.post("/search", response_model=List[SearchResponse])
async def search_endpoint(request: SearchRequest, vector_db=Depends(get_vector_db)):
    results = search(query_text=request.query, top_k=request.top_k, model=vector_db["model"], index=vector_db["index"], index_to_id=vector_db["index_to_id"])
    return results
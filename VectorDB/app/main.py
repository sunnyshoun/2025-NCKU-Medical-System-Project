from fastapi import FastAPI, status, Depends
from .schemas import SearchResponse, AppendRequest, ApiResponse
from .faiss_vectorDB import FAISSVectorDB
from .dependencies import get_vector_db
from .exceptions import register_exception_handlers
from typing import Optional

app = FastAPI(title="VectorDB Search API", description="A FastAPI service for vector search using FAISS", version="1.0.0")

# 註冊全局異常處理器
register_exception_handlers(app)

@app.get("/v1/knowledge", response_model=ApiResponse[SearchResponse])
async def get_knowledge_v1(query: str, top_k: Optional[int] = 5, vector_db: FAISSVectorDB = Depends(get_vector_db)):
    results = vector_db.search(query, top_k)
    search_response = SearchResponse(
        results=results,
        total=len(results),
        query=query
    )
    return ApiResponse.success(
        message="Search completed successfully",
        data=search_response
    )

@app.post("/v1/knowledge", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def append_knowledge_v1(request: AppendRequest, vector_db: FAISSVectorDB = Depends(get_vector_db)):
    new_ids = vector_db.append_knowledge(request)
    return ApiResponse.success(
        message="知識資料新增成功",
        data={"new_ids": new_ids}
    )
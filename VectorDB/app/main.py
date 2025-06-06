from fastapi import FastAPI, status, Depends, HTTPException
from .schemas import SearchResponse, AppendRequest
from .faiss_vectorDB import FAISSVectorDB
from .dependencies import get_vector_db
from typing import Optional

app = FastAPI(title="VectorDB Search API", description="A FastAPI service for vector search using FAISS", version="1.0.0")

@app.get("/v1/knowledge", response_model=SearchResponse)
async def get_knowledge_v1(query: str, top_k: Optional[int] = 5, vector_db: FAISSVectorDB = Depends(get_vector_db)):
    try:
        results = vector_db.search(query, top_k)
        return SearchResponse(
            results=results,
            total=len(results),
            query=query
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "查詢無效",
                "detail": str(e)
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "搜尋時發生錯誤",
                "detail": str(e)
            }
        )

@app.post("/v1/knowledge", status_code=status.HTTP_201_CREATED)
async def append_knowledge_v1(request: AppendRequest, vector_db: FAISSVectorDB = Depends(get_vector_db)):
    try:
        vector_db.append_knowledge(request)
        return {"status": "success", "message": "知識資料新增成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "status": "error",
                "message": "無效的知識資料",
                "detail": str(e)
            }
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "新增知識資料時發生錯誤",
                "detail": str(e)
            }
        )
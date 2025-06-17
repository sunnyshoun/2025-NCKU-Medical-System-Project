from pydantic import BaseModel
from typing import Optional, List, TypeVar, Generic

# 定義泛型類型
T = TypeVar("T")

class SearchResult(BaseModel):
    rank: int
    id: str
    similarity: float
    
class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str

class KnowledgeData(BaseModel):
    id: str
    knowledge_point: str
    tags: List[str]
    summary: Optional[str]
    source: Optional[str]
    
class AppendRequest(BaseModel):
    knowledges: List[KnowledgeData]

class ApiResponse(BaseModel, Generic[T]):
    status: str
    message: str
    data: Optional[T]

    @classmethod
    def success(cls, status: str = "success", message: str = "", data: T = None) -> "ApiResponse[T]":
        return cls(status=status, message=message, data=data)

    @classmethod
    def error(cls, status: str = "error", message: str = "", data: T = None) -> "ApiResponse[T]":
        return cls(status=status, message=message, data=data)
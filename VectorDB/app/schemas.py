from pydantic import BaseModel
from typing import Optional, List
    
class SearchResult(BaseModel):
    rank: int
    id: str
    similarity: float
    
class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str

class KnowledgData(BaseModel):
    id: str
    knowledge_point: str
    tags: List[str]
    summary: Optional[str]
    source: Optional[str]
    
class AppendRequest(BaseModel):
    knowledges: List[KnowledgData]
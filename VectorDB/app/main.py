import grpc
from concurrent import futures
import logging
from vector_db_pb2 import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    AppendRequest,
    AppendResponse,
    KnowledgeData,
)
from vector_db_pb2_grpc import VectorDBServiceServicer, add_VectorDBServiceServicer_to_server
from faiss_vectorDB import FAISSVectorDB

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBService(VectorDBServiceServicer):
    def __init__(self):
        self.vector_db = FAISSVectorDB()
        logger.info("gRPC VectorDBService initialized")

    def SearchKnowledge(self, request: SearchRequest, context: grpc.ServicerContext) -> SearchResponse:
        try:
            # 驗證輸入
            if not request.query.strip():
                return SearchResponse(
                    status="error",
                    message="查詢文本不能為空"
                )
            if not 1 <= request.top_k <= 50:
                return SearchResponse(
                    status="error",
                    message="top_k 必須在 1 ~ 50 之間"
                )

            # 執行搜尋
            results = self.vector_db.search(request.query, request.top_k)
            search_results = [
                SearchResult(rank=r.rank, id=r.id, similarity=r.similarity)
                for r in results
            ]

            return SearchResponse(
                status="success",
                message="Search completed successfully",
                results=search_results
            )

        except ValueError as e:
            logger.error(f"ValueError in SearchKnowledge: {e}")
            return SearchResponse(
                status="error",
                message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in SearchKnowledge: {e}")
            return SearchResponse(
                status="error",
                message="搜尋時發生未知錯誤"
            )

    def AppendKnowledge(self, request: AppendRequest, context: grpc.ServicerContext) -> AppendResponse:
        try:
            # 驗證輸入
            if not request.knowledges:
                return AppendResponse(
                    status="error",
                    message="新資料為空"
                )

            # 將 Protobuf 消息轉換為 AppendRequest（Pydantic 模型）
            pydantic_request = self._convert_to_pydantic_append_request(request)
            new_ids = self.vector_db.append_knowledge(pydantic_request)

            return AppendResponse(
                status="success",
                message="知識資料新增成功",
                new_ids=new_ids
            )

        except ValueError as e:
            logger.error(f"ValueError in AppendKnowledge: {e}")
            return AppendResponse(
                status="error",
                message=str(e)
            )
        except RuntimeError as e:
            logger.error(f"RuntimeError in AppendKnowledge: {e}")
            return AppendResponse(
                status="error",
                message=f"新增知識資料時發生錯誤: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in AppendKnowledge: {e}")
            return AppendResponse(
                status="error",
                message="新增知識資料時發生未知錯誤"
            )

    def _convert_to_pydantic_append_request(self, proto_request: AppendRequest) -> 'AppendRequest':
        from schemas import AppendRequest as PydanticAppendRequest, KnowledgeData as PydanticKnowledgeData
        knowledges = [
            PydanticKnowledgeData(
                id=k.id,
                knowledge_point=k.knowledge_point,
                tags=k.tags,
                summary=k.summary if k.summary else None,
                source=k.source if k.summary else None
            )
            for k in proto_request.knowledges
        ]
        return PydanticAppendRequest(knowledges=knowledges)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_VectorDBServiceServicer_to_server(VectorDBService(), server)
    server.add_insecure_port('[::]:50051')
    logger.info("gRPC server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
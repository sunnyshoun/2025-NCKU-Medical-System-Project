from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .schemas import ApiResponse
from starlette import status
import logging

# 配置日誌
logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI):
    """
    註冊全局異常處理器，將所有異常響應包裝為 ApiResponse 格式。
    
    Args:
        app (FastAPI): FastAPI 應用實例
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        errors = exc.errors()
        # Join error messages into a single string for cleaner output
        error_message = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiResponse.error(
                status="無效的請求格式",
                message=error_message
            ).model_dump()
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ApiResponse.error(
                message=str(exc)
            ).model_dump()
        )

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request, exc: RuntimeError):
        logger.error(f"Runtime error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse.error(
                status="服務器處理錯誤",
                message=str(exc)
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse.error(
                status="搜尋時發生未知錯誤",
                message=str(exc)
            ).model_dump()
        )
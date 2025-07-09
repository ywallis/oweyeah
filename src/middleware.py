from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.logger import logger

sensitive_key = ["password", "secret", "token"]


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/login"):
            body = ""
        else:
            body_bytes = await request.body()
            body = body_bytes.decode()
        log_dict = {
            "url": request.url.path,
            "method": request.method,
            "headers": request.headers,
            "body": body,
            "query_parameters": request.query_params,
        }
        logger.info(log_dict, extra=log_dict)

        response = await call_next(request)
        return response

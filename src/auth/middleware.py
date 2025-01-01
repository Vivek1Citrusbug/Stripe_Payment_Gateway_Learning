from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback


class ErrorMiddleware(BaseHTTPMiddleware):
    """
    Middlewar to catch unhandleed exceptions
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "details": traceback.format_exc(),
                    }
                },
            )


def http_exception_handler(request: Request, exc):
    """
    Function to handle http exceptions
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
            }
        },
    )

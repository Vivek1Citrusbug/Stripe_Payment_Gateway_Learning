from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from src.auth.dependencies import create_db_and_tables
from src.auth.interface import router as auth_router
from src.auth.middleware import ErrorMiddleware,http_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    for loadiing resources that need to be present before the start of the application
    """

    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(ErrorMiddleware)
app.add_exception_handler(HTTPException,http_exception_handler)
app.include_router(auth_router.router, prefix="/auth", tags=["Users"])

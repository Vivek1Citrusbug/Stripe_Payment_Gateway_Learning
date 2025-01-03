import stripe
from fastapi import FastAPI, HTTPException, Request, status
from contextlib import asynccontextmanager
from src.auth.dependencies import create_db_and_tables
from src.auth.interface import router as auth_router
from src.auth.middleware import ErrorMiddleware, http_exception_handler
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from config import STRIPE_ENDPOINT_SECRET
from src.auth.domain.models import UserModel
from datetime import datetime, timedelta
from typing import Annotated
from database import SessionDep
from src.auth.application.schemas import (
    UserPublicModel,
)
from fastapi import APIRouter, Depends, HTTPException
from src.auth.dependencies import get_current_active_user
from sqlmodel import SQLModel, select


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    for loadiing resources that need to be present before the start of the application
    """

    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(ErrorMiddleware)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(auth_router.router, prefix="/auth", tags=["Users"])

app.mount("/static/", StaticFiles(directory="static"), name="static")



    # if event["type"] == "payment_intent.succeeded":
    #     payment_intent = event["data"]["object"]
    #     print(f"PaymentIntent was successful! ID: {payment_intent['id']}")
    # elif event["type"] == "payment_intent.payment_failed":
    #     payment_intent = event["data"]["object"]
    #     print(
    #         f"Payment failed. Reason: {payment_intent['last_payment_error']['message']}"
    #     )
    # else:
    #     print(f"Unhandled event type: {event['type']}")

    # return {"message": "Webhook received successfully"}


# @app.get("/", response_class=HTMLResponse)
# async def payment_page():
#     html_content = Path("templates/checkout.html").read_text()
#     return HTMLResponse(content=html_content)

import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status, responses
from sqlmodel import SQLModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import engine, SessionDep
from src.auth.application.schemas import TokenData
from src.auth.domain.models import UserModel
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from typing import Annotated
from jwt.exceptions import InvalidTokenError


oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/token")


def create_db_and_tables():
    """
    Creating database tables
    """

    print("All database model created#######")
    SQLModel.metadata.create_all(engine)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_schema)], session: SessionDep
):
    """
    Function to get current logged in user
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_user(session: SessionDep, username: str):
    """
    Function to get user from given username
    """

    user = session.get(UserModel, username)
    print("############", user, "#############")
    if not user:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user


async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Function to get current active user
    """

    return current_user

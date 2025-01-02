# authentication/services.py
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from passlib.context import CryptContext
from .models import UserModel
from src.auth.application.schemas import Token
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from src.auth.dependencies import get_current_active_user, get_user
import jwt
from database import SessionDep
from fastapi import Depends
from typing import Annotated

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    Function o verify password if user
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Function to geet password hashing
    """

    return pwd_context.hash(password)


def authenticate_user(session, username: str, password: str):
    """
    Function to authenticate user
    """

    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Function to create access token
    """

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class RoleChecker:
    """
    Role checker class to check for the roles assigned to particular user and given neccessary permissions according to roles.
    """

    def __init__(self, allowed_roles: list):
        print("init")
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserModel = Depends(get_current_active_user)):
        print("call")
        # Superuser role check
        if user.is_superuser:
            if "superuser" not in self.allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operation not permitted: Requires access.",
                )
            return

        # Staff role check
        if user.is_staff:
            if "staff" not in self.allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operation not permitted: Requires access.",
                )
            return

        # Generic role check
        if "user" not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted: Requires access.",
            )

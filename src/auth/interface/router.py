import jwt
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, select
from database import SessionDep
from src.auth.domain.services import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
    RoleChecker,
)
from src.auth.domain.models import UserBaseModel, UserModel
from src.auth.application.schemas import Token
from fastapi import status
from datetime import datetime, timedelta, timezone
from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from src.auth.application.schemas import (
    UpdateUserModel,
    UserPublicModel,
    UserBaseModel,
    CreateUserModel,
    Token,
    TokenData,
)
from src.auth.dependencies import get_current_active_user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import engine, SessionDep
from jwt.exceptions import InvalidTokenError


router = APIRouter()


allow_user_create_resource = RoleChecker(["superuser"])
allow_user_delete_resource = RoleChecker(["superuser"])


######################
##### Routes #########
######################


@router.post(
    "/token",
    status_code=status.HTTP_201_CREATED,
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    """
    Function to login user and return access token in return
    """

    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/")
async def index():
    """
    Landing page
    """

    return "Landing page"


@router.get(
    "/users",
    response_model=list[UserPublicModel],
    status_code=status.HTTP_200_OK,
)
async def list_users(
    session: SessionDep,
    current_user: Annotated[UserPublicModel, Depends(get_current_active_user)],
    dependencies=Depends(allow_user_create_resource),
):
    """
    Function to list user basd on the permission
    """

    query = select(UserModel)

    if current_user.is_superuser:
        pass
    elif current_user.is_staff:
        query = query.where(UserModel.is_superuser == False)
    else:
        query = query.where(
            UserModel.is_superuser == False,
            UserModel.is_staff == False,
        )

    users = session.exec(query).all()
    return users


@router.post(
    "/users",
    response_model=UserPublicModel,
    status_code=status.HTTP_201_CREATED,
)
async def crate_user(
    user: CreateUserModel,
    session: SessionDep,
    dependencies=Depends(allow_user_create_resource),
):
    """
    Function to create user based on the allowed roles
    """

    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump()
    user_data["password"] = hashed_password
    UserDatabase = UserModel.model_validate(user_data)
    session.add(UserDatabase)
    session.commit()
    session.refresh(UserDatabase)
    return UserDatabase


@router.get(
    "/users/{username}",
    response_model=UserPublicModel,
    status_code=status.HTTP_200_OK,
)
async def show_user_details(
    username: str,
    session: SessionDep,
    current_user: Annotated[UserPublicModel, Depends(get_current_active_user)],
):
    """
    Function to print user details based on the given role.
    """

    target_user = session.get(UserModel, username)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if current_user.is_superuser:
        return target_user
    elif current_user.is_staff and (not target_user.is_superuser):
        return target_user
    elif current_user.username == username:
        return target_user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.patch(
    "/users/{username}",
    response_model=UserPublicModel,
    status_code=status.HTTP_200_OK,
)
async def update_user_details(
    username: str,
    user: UpdateUserModel,
    session: SessionDep,
    current_user: Annotated[UserPublicModel, Depends(get_current_active_user)],
):
    """
    Function to update user details based on the given role.
    """

    user_database_details = session.get(UserModel, username)
    if not user_database_details:
        raise HTTPException(status_code=404, detail="User not found")
    user_entered_data = user.model_dump(exclude_unset=True)
    user_database_details.sqlmodel_update(user_entered_data)
    session.add(user_database_details)
    session.commit()
    session.refresh(user_database_details)
    return user_database_details


@router.delete(
    "/users/{username}",
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    username: str,
    session: SessionDep,
    current_user: Annotated[UserPublicModel, Depends(get_current_active_user)],
    dependencies=Depends(allow_user_delete_resource),
):
    """
    Function to delete user based on the given role.
    """

    user = session.get(UserModel, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"User deleted successfully": True}

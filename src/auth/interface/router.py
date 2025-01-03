import jwt
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, select
import stripe.error
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
from fastapi import status, Request
from datetime import datetime, timedelta, timezone, UTC
from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    STRIPE_PUBLISHABLE_KEY,
    STRIPE_SECRET_KEY,
    STRIPE_ENDPOINT_SECRET,
)
from src.auth.application.schemas import (
    UpdateUserModel,
    UserPublicModel,
    UserBaseModel,
    CreateUserModel,
    Token,
    TokenData,
)
from src.auth.domain.models import UserBaseModel
from src.auth.dependencies import get_current_active_user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import engine, SessionDep
from jwt.exceptions import InvalidTokenError
import stripe
from stripe import stripe
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from tasks.task import revert_user_role

router = APIRouter()


allow_user_create_resource = RoleChecker(["superuser"])
allow_user_delete_resource = RoleChecker(["superuser"])

stripe.api_key = STRIPE_SECRET_KEY

######################
##### Routes #########
######################


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db_session: SessionDep,
):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = STRIPE_ENDPOINT_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if event["type"] in [
        "payment_intent.succeeded",
        "charge.updated",
        "charge.succeeded",
    ]:
        payment_obj = event["data"]["object"]
        customer_email = payment_obj.get("billing_details", {}).get("email")
        if not customer_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in payment details",
            )

        statement = select(UserModel).where(UserModel.email == customer_email)
        user = db_session.exec(statement).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        user.subscription_count += 1
        user.is_staff = True
        user.is_superuser = True

        if user.subscription_count % 4 == 0:
            user.expiration_time = datetime.now(UTC) + timedelta(minutes=2)
            print(f"User {user.username} upgraded to advanced plan for 2 minutes.")
        else:
            user.expiration_time = datetime.now(UTC) + timedelta(minutes=1)
            print(f"User {user.username} assigned admin role for 1 minutes.")

        db_session.add(user)
        db_session.commit()

        # schedule task for the eta
        revert_user_role.apply_async(args=[user.email], eta=user.expiration_time)

    else:
        print(f"Unhandled event type: {event['type']}")
    return {"status": "success"}


@router.post("/create-checkout-session")
async def checkout(amount: int, session: SessionDep):
    if amount != 500:
        raise HTTPException(status_code=400, detail="Amount must be $5")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "Be Admin"}, 
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url="https://example.com/success", ## Given this sample link for success and failure but we have to take this as environment variable.
            cancel_url="https://example.com/failure",
        )
        print(session)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error creating checkout session: {str(e)}"
        )


@router.get("/success/{session_id}")
async def success(
    session_id: str,
    db_session: SessionDep,
    current_user: Annotated[UserPublicModel, Depends(get_current_active_user)],
):
    session = stripe.checkout.Session.retrieve(session_id)
    user = db_session.get(UserModel, current_user.username)
    if user:
        user.is_staff = True
        user.is_superuser = True
        db_session.commit()
        return {"message": "Payment successful, role upgraded to admin."}
    else:
        raise HTTPException(status_code=404, detail="User not found")


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
    # dependencies=Depends(allow_user_create_resource),
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

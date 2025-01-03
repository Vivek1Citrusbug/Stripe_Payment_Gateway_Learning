from sqlmodel import Session, select
from datetime import datetime
from src.auth.domain.models import UserModel 
from database import engine  
from tasks.celery import celery_app

@celery_app.task
def revert_user_role(user_email):
    with Session(engine) as session:
        statement = select(UserModel).where(UserModel.email == user_email)
        user = session.exec(statement).first()
        if user and user.expiration_time and datetime.now() >= user.expiration_time:
            user.is_staff = False
            user.is_superuser = False
            user.expiration_time = None
            session.add(user)
            session.commit()
            print(f"Reverted roles for user {user.username}")
        else:
            print(f"No action needed for user {user_email}")

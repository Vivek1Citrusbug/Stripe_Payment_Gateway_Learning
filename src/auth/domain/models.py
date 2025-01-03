from src.auth.application.schemas import UserBaseModel
from sqlmodel import Field,SQLModel
from datetime import datetime
from typing import Optional

#############################
##### Database model ######
#############################


class UserModel(UserBaseModel, table=True):
    username: str | None = Field(default=None, primary_key=True)    
    password: str
    expiration_time: Optional[datetime] = None
    subscription_count: int = Field(default=0)   

class AccessToken(SQLModel, table=True):  
    id: int = Field(default=None, primary_key=True)
    access_token: str
    token_type: str

class UserExtraDetails(SQLModel,table=True):
    id:int = Field(default=None,primary_key=True)
    birth_year:int
    address: str

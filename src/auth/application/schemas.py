from sqlmodel import SQLModel, Field


#############################
##### PYDANTIC schemas ######
#############################


class UserBaseModel(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    email: str | None = None
    is_superuser :bool = Field(default=False)
    is_staff :bool = Field(default=False)
    
    # disabled: bool | None = None


class UserPublicModel(UserBaseModel):
    username:str
    is_superuser :bool = Field(default=False)
    is_staff :bool = Field(default=False)

class CreateUserModel(UserBaseModel):
    username:str
    password: str


class UpdateUserModel(UserBaseModel):
    name: str | None = None
    age: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str
    email: str | None = None



# class UserBaseModel(SQLModel):
#     username: str 
#     name: str = Field(index=True)
#     age: int | None = Field(default=None, index=True)
#     first_name: str | None = Field(default=None)
#     last_name: str | None = Field(default=None)
#     email:str | None = None
#     disabled: bool | None = None


# class UserPublicModel(UserBaseModel):
#     id: int


# class CrateUserModel(UserBaseModel):
#     hashed_password: str


# class UpdateUserModel(UserBaseModel):
#     name: str | None = None
#     age: int | None = None
#     first_name: str | None = None
#     last_name: str | None = None
#     hashed_password: str | None = None

# class token(SQLModel):
#     access_token: str
#     token_type: str

# class token_data(SQLModel):
#     username:str
#     email:str | None = None



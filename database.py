from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated

sqlite_file_name = "NewDatabase.db"
sqlite_url = f"sqlite:///database/{sqlite_file_name}"
connect_args = {"check_same_thread": False}

# connetction to database
engine = create_engine(sqlite_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session
     
SessionDep = Annotated[Session, Depends(get_session)]

base = declarative_base()

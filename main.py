"""API FastAPI pour le site EERI avec une base de données SQLAlchemy."""
from fastapi import FastAPI
from typing import Union
from sqlalchemy.orm import configure_mappers

from routers import auth, community, admin, strongWord, user  
from database import engine 

import models

configure_mappers()

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(community.router)
app.include_router(admin.router) 
app.include_router(user.router)
app.include_router(strongWord.router)

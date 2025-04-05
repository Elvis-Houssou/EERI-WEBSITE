from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from database import SessionLocal
from models import Community, User
from routers.auth import get_current_user, get_current_admin

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

def get_db():
    """Crée et gère une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbDependency = Annotated[Session, Depends(get_db)]
UserDependency = Annotated[dict, Depends(get_current_user)]
AdminDependency = Annotated[dict, Depends(get_current_admin)]

class UserRequest(BaseModel):
    """Modèle de création d'utilisateur."""
    username: str
    firstname: str | None = None
    lastname: str | None = None
    email: str
    password: str
    age: int | None = None
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    address: str | None = None
    role: str | None = None
    # is_verified: bool = False
    # is_active: bool = True

# liste des utilisateurs
@router.get("/all")
async def get_all_users(db: DbDependency, admin: AdminDependency):
    """Recupère tous les utilisateurs."""
    users = db.query(User).all()
    return {"users": users}

# recuperer un utilisateur par son id
@router.get("/{user_id}")
async def get_one_user(user_id: int, db: DbDependency, admin: AdminDependency):
    """Recupère un utilisateur par son Id"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user": user}

# modifier un utilisateur
@router.put("/{user_id}")
async def update_user(user_id: int, user_request: UserRequest, db: DbDependency, admin: AdminDependency):
    """Modifie un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Mettre à jour les champs de l'utilisateur
    user.username = user_request.username
    user.firstname = user_request.firstname
    user.lastname = user_request.lastname
    user.email = user_request.email
    user.password = user_request.password
    user.age = user_request.age
    user.city = user_request.city
    user.country = user_request.country
    user.phone = user_request.phone
    user.address = user_request.address
    user.role = user_request.role if user_request.role else user.role
    user.is_admin = True if user_request.role == "admin" else False
    db.commit()
    return {"message": "User updated successfully"}

# supprimer un utilisateur
@router.delete("/{user_id}")
async def delete_user(user_id: int, db: DbDependency, admin: AdminDependency):
    """Supprime un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}



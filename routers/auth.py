from typing import Annotated
from datetime import datetime, timedelta

# import os
# print(os.urandom(32).hex())
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from database import SessionLocal
from models import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = "302fa698cb4d866ae48592a2d46656a78b94626d1d9b9876dee7692c5a7f1e7b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):
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

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    """Crée et gère une session de base de données."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbDependency = Annotated[Session, Depends(get_db)]

def create_access_token(username: str, user_id: int, role: str, is_admin: bool, expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, 'role': role, 'is_admin': is_admin}
    expires = datetime.utcnow()  + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: DbDependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        is_admin: bool = payload.get('is_admin')

        if None in (username, user_id, user_role, is_admin):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
            
        return {
            "username": username,
            "id": user_id,
            "role": user_role,
            "is_admin": is_admin
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials.')

def get_current_admin(current_user: Annotated[dict, Depends(get_current_user)], db: DbDependency):
    
    # Vérification dans la base de données pour plus de sécurité
    user = db.get(User, current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

def authenticate_user(db: Session, username: str, password: str):
    """Authentifie un utilisateur."""
    user = db.query(User).filter(User.username == username).first()
    if not user: 
        return False 
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

# Dépendance pour le manager de la communauté "Communication"
def get_communication_manager(current_user: Annotated[dict, Depends(get_current_user)], db: DbDependency):
    user = db.get(User, current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role != "president":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="President role required")
    if not user.community or not user.community.is_communication:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User must be the president of the Communication community")
    return user

# Dépendance pour vérifier le privilège d’ajout
def get_add_privilege_user(current_user: Annotated[dict, Depends(get_current_user)], db: DbDependency):
    user = db.get(User, current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.community or not user.community.is_communication:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User must belong to the Communication community")
    if not user.can_add and user.role != "president" and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Add privilege required")
    return user

# Dépendance pour vérifier le privilège d’édition
def get_edit_privilege_user(current_user: Annotated[dict, Depends(get_current_user)], db: DbDependency):
    user = db.get(User, current_user["id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.community or not user.community.is_communication:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User must belong to the Communication community")
    if not user.can_edit and user.role != "president" and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Edit privilege required")
    return user

@router.get("/users", status_code=status.HTTP_200_OK)
async def get_users(db: DbDependency):
    """Récupère tous les utilisateurs."""
    users = db.query(User).all()
    return users


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbDependency):
    """Génère un token JWT pour l'utilisateur."""
    logger.debug(f"Authentification pour username: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.username, user.id, user.role, user.is_admin, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer"}
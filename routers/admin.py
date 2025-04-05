from typing import Annotated
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Community, User
from routers.auth import get_current_user, get_current_admin

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

# Dépendance pour obtenir la session de base de données
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

@router.get("/dashboard")
async def admin_dashboard(db: DbDependency, admin: UserDependency):
    return {"message": "Welcome to dashboard"}

    # recuperer toutes les communautés
@router.get("/communities")
def get_community_all(db: DbDependency, admin: AdminDependency):
    """Recupère toutes les communautés."""
    return db.query(Community).all()
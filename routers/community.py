from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from database import SessionLocal
from models import Community, User
from routers.auth import get_current_user, get_current_admin, get_communication_manager, get_add_privilege_user, get_edit_privilege_user

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/community",
    tags=["community"],
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
# role et privilège d'un utilisateur
CommunicationManagerDependency = Annotated[User, Depends(get_communication_manager)]
AddPrivilegeDependency = Annotated[User, Depends(get_add_privilege_user)]
EditPrivilegeDependency = Annotated[User, Depends(get_edit_privilege_user)]

class CommunityRequest(BaseModel):
    """Modèle de création de communauté."""
    image: str | None = None
    name: str
    description: str | None = None
    area: str | None = None
    

# recuperer une communauté par son id
@router.get("/{community_id}")
async def get_one_community(community_id: int, db: DbDependency, admin: AdminDependency):
    """Recupère une communauté par son ID."""
    return db.query(Community).filter(Community.id == community_id).first()

# afficher toutes les communautés
@router.get("/all")
async def get_all_communities(db: DbDependency):
    """Recupère toutes les communautés."""
    communities = db.query(Community).all()
    return {"communities": communities}

# créer une communauté
@router.post("/create")
async def crreate_community(community_request: CommunityRequest, db: DbDependency, admin: AdminDependency, raw_request: Request):
    """Crée une communauté."""
    logger.debug(f"Raw body received: {await raw_request.body()}")
    community = Community(
        image=community_request.image if community_request.image else None,
        name=community_request.name,
        description=community_request.description if community_request.description else None,
        area=community_request.area if community_request.area else None,
    )
    
    logger.debug(f"information communauté: {community}")
    db.add(community)
    db.commit()
    db.refresh(community)
    return {"message": "Community created successfully", "community": community}

# modifier une communauté
@router.put("/{community_id}/update")
async def update_community(community_id: int, community_request: CommunityRequest, db: DbDependency, admin: AdminDependency):
    """"Met à jour une communauté"""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    # Mettre a jour les champs de la communauté
    community.image = community_request.image if community_request.image else community.image
    community.name = community_request.name if community_request.name else community.name
    community.description = community_request.description if community_request.description else community.description
    community.area = community_request.area if community_request.area else community.area

    db.commit()
    db.refresh(community)
    return {"message": "Community updated successfully", "community": community}

# supprimer une communauté
@router.delete("/{community_id}/delete")
async def delete_community(community_id: int, db: DbDependency, admin: AdminDependency):
    """Supprime une communauté."""
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    
    db.delete(community)
    db.commit()
    return {"message": "Community deleted successfully"}


# assigner une communauté à un utilisateur
@router.post("/{community_id}/assign-user/{user_id}")
async def assign_user_to_community(community_id: int, user_id: int, db: DbDependency, admin: AdminDependency):
    """Assigne une communauté à un utilisateur."""
    community = db.query(Community).filter(Community.id == community_id).first()
    user = db.query(User).filter(User.id == user_id).filter(User.community_id == None).first()
    if not community:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # if user.community_id:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already assigned to a community")
    user.community_id = community.id
    db.commit()
    db.refresh(user)
    return {"message": "User assigned to community successfully", "user": user}
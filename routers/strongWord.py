from typing import Annotated
from fastapi import Depends, APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status

from database import SessionLocal
from models import Community, User, StrongWord
from routers.auth import get_current_user, get_current_admin

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/parole-forte",
    tags=["parole-forte"],
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


class StrongWordRequest(BaseModel):
    """Modèle de création de communauté."""
    sentence: str
    reference: str | None = None
    user_id: int


# afficher toutes les paroles fortes
@router.get("/all")
async def get_all_strong_words(db: DbDependency, admin: AdminDependency):
    """Recupère toutes les paroles fortes."""
    strong_words = db.query(StrongWord).all()
    return {"strong_words": strong_words}


# créer une parole forte
@router.post("/create")
async def create_strong_word(strong_word_request: StrongWordRequest, db: DbDependency, admin: AdminDependency):
    """Crée une parole forte."""
    user = db.query(User).filter(User.id == strong_word_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    strong_word = StrongWord(
        sentence=strong_word_request.sentence,
        reference=strong_word_request.reference if strong_word_request.reference else None,
        user_id=strong_word_request.user_id,
    )
    try:
        db.add(strong_word)
        db.commit()
        db.refresh(strong_word)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating strong word: {str(e)}"
        )
    return {"message": "Strong word created successfully", "strong_word": strong_word}

# modifier une parole forte
@router.put("/update/{strong_word_id}")
async def update_strong_word(strong_word_id: int, strong_word_request: StrongWordRequest, db: DbDependency, admin: AdminDependency):
    """Modifie une parole forte."""
    strong_word = db.query(StrongWord).filter(StrongWord.id == strong_word_id).first()
    if not strong_word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strong word not found")
    
    strong_word.sentence = strong_word_request.sentence
    strong_word.reference = strong_word_request.reference if strong_word_request.reference else None
    strong_word.user_id = strong_word_request.user_id
    db.commit()
    db.refresh(strong_word)
    return {"message": "Strong word updated successfully", "strong_word": strong_word}
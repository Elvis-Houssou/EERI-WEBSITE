from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String, unique=True)
    firstname = Column(String, default=None, nullable=True)
    lastname = Column(String, default=None, nullable=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    age = Column(Integer, default=None, nullable=True)
    city = Column(String, default=None, nullable=True)
    country = Column(String, default=None, nullable=True)
    phone = Column(String, default=None, nullable=True)
    address = Column(String, default=None, nullable=True)
    community_id = Column(Integer, ForeignKey("communities.id"), default=None, nullable=True)
    role = Column(String, default="member", nullable=False)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    can_add = Column(Boolean, default=False)  # Privilège d’ajout
    can_edit = Column(Boolean, default=False)  # Privilège d’édition

    community = relationship("Community", back_populates="users")
    strong_words = relationship("StrongWord", back_populates="user")


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, index=True, primary_key=True)
    image = Column(String, default=None, nullable=True)
    name = Column(String, unique=True)
    description = Column(String, default=None, nullable=True)
    area = Column(String, default=None, nullable=True)
    is_active = Column(Boolean, default=True)
    is_communication = Column(Boolean, default=False)  # Identifie la communauté "Communication"

    users = relationship("User", back_populates="community")


class StrongWord(Base):
    __tablename__ = "strong_words"

    id = Column(Integer, index=True, primary_key=True)
    sentence = Column(String, nullable=False)
    reference = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=None, nullable=True)
    date_added = Column(DateTime, default=None, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="strong_words")
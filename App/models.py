from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey

from .database import BASE
from sqlalchemy.orm import relationship

class User(BASE):
    __tablename__ = "users"
    id = Column(Integer, index=True, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    
    items = relationship("Item", back_populates="owner", cascade="all, delete")
    
class Item(BASE):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True)
    description = Column(String, index=True)
    price = Column(String)
    location = Column(String)
    image = Column(String, nullable = False)
    contact_info = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="items")
from pydantic import BaseModel, EmailStr

from typing import Optional


# users schema
class UserCreate(BaseModel): 
    email: EmailStr
    password:str
    admin_key: Optional[str] = None
 
class LoginRequest(BaseModel):
     email: EmailStr
     password: str
        
class Login(BaseModel):
    password: str
    email:EmailStr
       
class UserOut(BaseModel):
    id:int
    email: EmailStr
    
    class Config:
        orm_mode = True
        
class CreateSuperUser(BaseModel):
    email: EmailStr
    password: str        

class ItemBase(BaseModel):
    item_name: str
    description: str
    price: float
    location: str
    image_url: Optional[str] = None
     
class ItemOut(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True
         
class CreateItem(ItemBase):
     pass          


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    
class RefreshRequest(BaseModel):
    refresh_token: str
    
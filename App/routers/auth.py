from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form, File
from sqlalchemy.orm import Session
from .. import models, schemas, database
import bcrypt
import shutil
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from config import  SECRET_KEY, ALGORITHM, MY_ADMIN_KEY
from utils import verify_password
from ..models import User
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import sessionLocal
from sqlalchemy.future import select
import os

import aiofiles

def create_access_token(data: dict, expires_minutes: int = 30):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_minutes: int = 43200):  # 30 days
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm=ALGORITHM)
        return payload
    except JWTError:
        return None
                




router = APIRouter()

async def get_db():
    async with sessionLocal() as session:
        yield session
   
        

from fastapi.security import OAuth2PasswordBearer

oauth_2scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(token: str = Depends(oauth_2scheme), db: AsyncSession=Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="invalid token",
        headers={"www-Authenticate": "Bearer"}
    )
    
    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    
    return user
            
    
        
@router.post("/signup", response_model=schemas.UserOut )
async def SignUp(user: schemas.UserCreate,  db: AsyncSession=Depends(get_db)  ):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            detail = "user already registered",
            status_code=status.HTTP_400_BAD_REQUEST
            
        )
        
    is_superuser = False
    
    if user.admin_key == MY_ADMIN_KEY:
        is_superuser = True
        
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    new_user= models.User(email = user.email, hashed_password = hashed_password.decode('utf-8'),
                          is_superuser = is_superuser)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
async def Login(username: str = Form(), password: str = Form(),db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            detail = "invalid credentials",
            status_code= 401
        )
        
    payload = {
        "sub": user.email,
        "user_id": user.id,
        "is_superuser": user.is_superuser
    }
    
    access_token = create_access_token(payload)
    
    refresh_token = create_refresh_token(payload)
  
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
 
UPLOAD_DIR = "uploads" 
   
@router.post("/Items", response_model = schemas.ItemOut)
async def CreateItem(
      image: UploadFile = File(),
      item_name: str = Form(),
      description: str = Form(),
      price: float = Form(),
      location: str = Form(),
      contact_info: str = Form(),
      db: AsyncSession = Depends(get_db),
      current_user: User = Depends(get_current_user)
  ) :
    file_ext = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await image.read()  
        await buffer.write(content)
        
    new_item = models.Item(
    item_name = item_name,
    description = description,
    price = price,
    location = location,   
    image = f"{file_path}",
    contact_info = contact_info,
    owner_id = current_user.id
    )  
    
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item) 
    return new_item  


@router.delete("/user/{user_id}")
async def delete_user(
      user_id: int,
      db: AsyncSession = Depends(get_db),
      current_user: User = Depends(get_current_user)   
    ): 
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail=" only super users can delete users"
        )
        
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user_to_delete = result.scalar_one_or_none()
        
    if not user_to_delete:
        raise HTTPException(
            status_code= 404,
            detail="user not found"
        )
    
    for item in user_to_delete.items:
        if item.image and os.path.exists(item.image):
            os.remove(item.image)
    
    await db.delete(user_to_delete)
    
    await db.commit()
    
    return {"detail": f"user with id{user_id} and their items were deleted successfully"}

@router.delete("/delete-me", status_code=200)
async def delete_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(models.User).where(models.User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            detail= "user not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
        
    await db.delete(user)
    await db.commit()
    
    return {"detail": "your account has been successfully deleted"}

@router.put("/edit_item/{item_id}", response_model=schemas.ItemOut)
async def update_item(
    item_id: int,
    item_name: str = Form(),
    description: str = Form(...),
    price: float = Form(...),
    location: str = Form(...),
    contact_info: str = Form(...),
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(models.Item).where(models.Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            detail = "item not found",
            status_code = 404
        )
        
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code = 403,
            detail = "you are not allowed to update this item"
        )
        
    if image:
        if item.image and os.path.exists(item.image):
            os.remove(item.image)
            
    file_ext = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await image.read() 
        
      
    item.image = file_path 
        
    item.item_name = item_name
    item.description = description
    item.price = price
    item.location = location
    item.contact_info = contact_info
    
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/delete_item/{item_id}", status_code = 204)
async def delete(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(models.Item).where(models.Item.id == item_id))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            detail = "item not found",
            status_code =404
        )
    if item.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            detail= "you are not allowed to delaete this item",
            status_code=403
        )
        
    await db.delete(item)
    await db.commit()
    
    return {"detail": "item deleted successfully"}
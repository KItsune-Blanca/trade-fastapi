from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import List
from . import models
from . database import engine
from fastapi.staticfiles import StaticFiles
from . import schemas
from sqlalchemy.orm import Session
from fastapi import  Depends
from fastapi import Request
from .routers import auth
from fastapi import Query
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from .routers.auth import get_db


models.BASE.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)

app.mount("/uploads", StaticFiles(directory = "uploads"), name = "uploads" )
 
@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/Items", response_model = list[schemas.ItemOut])
async def get_all_items(
    request: Request,
    db: AsyncSession = Depends(get_db),
    location: str = Query(None, description= "Filter By Location"),
    item_name:str = Query(None, description  = "Filter By Item Name")
    
    ):
     query = select(models.Item)
     
     if location:
         query = query.where(models.Item.location.ilike(f"%{location}%"))

     if item_name:
        query = query.where(models.Item.item_name.ilike(f"%{item_name}%"))
        
     result = await db.execute(query)    
     
     items = result.scalar.all()
     return items
        
     

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
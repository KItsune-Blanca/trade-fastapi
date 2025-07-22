from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL =os.getenv("DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
    
)

BASE = declarative_base()

sessionLocal = sessionmaker(autoflush=False, class_ = AsyncSession,  autocommit=False, bind=engine)


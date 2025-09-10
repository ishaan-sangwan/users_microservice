from fastapi import FastAPI, Depends
from data_layer import Base, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import asyncio

from data_layer import UserCreate

engine = create_async_engine(
    'postgresql+asyncpg://postgres:q123@192.168.122.53:5432/testing'
)

async def get_session():
    session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )()
    try:
        yield session
    except:
        await session.rollback()
        raise
    finally:
        await session.close()

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created!")

@app.post("/signup")
async def create_user(user_in: UserCreate,  session: AsyncSession = Depends(get_session)):
    user = User(
        name=user_in.name,
        email=user_in.email,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
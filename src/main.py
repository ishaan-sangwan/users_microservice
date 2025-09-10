from fastapi import FastAPI, Depends, Header
from sqlalchemy.sql.functions import current_user

from data_layer import Base, User
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import asyncio
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from data_layer import UserCreate
import os
from sqlalchemy import select
import jwt
import datetime

pg_address = os.environ.get('PG_ADDRESS', '192.168.122.53:5432')

SECRET_KEY = os.environ.get('SECRET_KEY')
engine = create_async_engine(
    f'postgresql+asyncpg://postgres:q123@{pg_address}/testing'
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


def validate_jwt(token: str):
    try:
        print(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        id = payload.get('user_id')
        return id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Expired token')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid Token')

def get_token(authorization: str = Header('Authorization')):
    token = authorization.replace('Bearer ', '')
    return validate_jwt(token)
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created!")

@app.post("/signup")
async def create_user(user_in: UserCreate,  session: AsyncSession = Depends(get_session)):
    try:
        user = User(
            name=user_in.name,
            email=user_in.email,
        )
        user.password = user_in.password
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(status_code=409, detail=f'the user email already exists {user_in.email}')
    except Exception as error:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session), current_user=Depends(get_token)):
    try:
        query = select(User)
        result = await session.execute(query)
        users = result.scalars().all()
        return users
    except Exception as error:
        pass

@app.post('/login')
async def login(user_in: UserCreate,session: AsyncSession = Depends(get_session)):
    try:
        query = select(User).where(User.email == user_in.email)
        result = await session.execute(query)
        result = result.scalars().first()
        if result is None:
            return {
                "error":'no user found'
            }

        if result.verify_password(user_in.password):

            payload = {
                'user_id': result.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
                'iat':datetime.datetime.utcnow()
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return {
                "access":token
            }
        else:
            return False
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
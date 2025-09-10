import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from pydantic import BaseModel
from passlib.hash import sha256_crypt

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    _password = Column(String, nullable=False, server_default='not set')
    description = Column(String)

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self._password = sha256_crypt.hash(password)

    def verify_password(self, password):
        return sha256_crypt.verify(password, self._password)

class UserCreate(BaseModel):
    name: str = None
    email: str
    password: str

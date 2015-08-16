import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key = True)
    project_title = Column(String(255), nullable = False)
    client = Column(String(255))
    project_value = Column(Float)
    completed_date = Column(Date)
    description = Column(String())
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
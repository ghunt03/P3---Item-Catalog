import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """Table defintion for users"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    """Table defintion for categories"""
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'id': self.id,
            'name': self.name
        }


class Project(Base):
    """Table defintion for Projects"""
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    project_title = Column(String(255), nullable=False)
    client = Column(String(255))
    project_value = Column(Float)
    completed_date = Column(DateTime)
    description = Column(String())
    last_updated = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        # Returns object data in easily serializeable format
        return {
            'project_title': self.project_title,
            'client': self.client,
            'id': self.id,
            'project_value': self.project_value,
            'description': self.description,
            'category': self.category.name,
            'last_updated': self.last_updated
        }

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)

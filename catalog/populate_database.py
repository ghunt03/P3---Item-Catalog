from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Project, User

import datetime
import csv

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user

User1 = User(
    name="GHunt",
    email="g.hunt@manteena.com.au",
    picture='http://www.manteena.com.au/images/logo.gif')
session.add(User1)
session.commit()

with open('sample_data\categories.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        category = Category(name=row[0])
        session.add(category)
        session.commit()

with open('sample_data\projects.csv', 'rb') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        category = session.query(Category).filter_by(name=row[0]).one()
        completed_date = datetime.datetime.strptime(
            row[4], "%d/%m/%Y").date()
        project = Project(
            project_title=row[1],
            client=row[2],
            project_value=row[3],
            completed_date=completed_date,
            description=row[5],
            category_id=category.id,
            user_id=User1.id
        )
        session.add(project)
        session.commit()

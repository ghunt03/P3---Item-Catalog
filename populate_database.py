from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Project

import datetime

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


category1 = Category(name="Education")
session.add(category1)
session.commit()

project1 = Project(
    project_title="Edmund Rice College Gymnasium",
    client="Edmund Rice College Wollongong",
    project_value=5000000,
    completed_date=datetime.date(2014, 5, 1),
    description='''This multi-purpose sports building comprises 2 levels of 
        building structure approximately 2,200m2.
        The building is founded on piles and consists of: convential reinforced 
        concrete systems for slabs, beams and columns; steel columns and 
        roof structure; and steels frame facade. 
        The cladding system comprises facade blockwork, metal cladding and 
        fibre cement, aluminium framed glazed windows and sunscreens 
        and Ritek metal deck roofing.
        The fitout includes a fully integrated fitout to the whole building.
''',
    category=category1)
session.add(project1)
session.commit()

project2 = Project(
    project_title="Namadgi P-10 School",
    client="ACT Procurement Solutions",
    project_value=50000000,
    completed_date=datetime.date(2011, 11, 1),
    description='''The new Kambah P-10 School, re-named Namadgi School is 
        constructed on the old Kambah High School site. The project required 
        the demolition of the existing buildings & the 
        construction of buildings and facilities for: Preschool & Kindergarten,
        Years 1 to 10; a Performing Arts, Design Technology, Visual Arts, 
        Science Laboratories, Learning Resource Centre, 
        Administration, Gymnasium and Canteen.
    ''',
    category=category1)
session.add(project2)
session.commit()

category2 = Category(name="Health")
session.add(category2)
session.commit()

project3 = Project(
    project_title="Gungahlin Community Health Centre",
    client="ACT Government - ACT Health Directorate",
    project_value=18000000,
    completed_date=datetime.date(2011, 7, 1),
    description='''The Gungahlin Community Health Centre formed part of a roll 
        out of new and refurbished facilities managed by the ACT Health 
        Directorate as part of their Capital Assets Development Program 
        (CADP). The Gungahlin Community Health Centre was the first of three 
        community health centres, with centres in Belconnen and Tuggeranong 
        following close behind. The design of the three centres was 
        awarded to Architecture firm McConnel Smith & Johnson / 
        May+Russell Architects JV whom where novated to Manteena 
        upon award of the Project Management.''',
    category=category2)
session.add(project3)
session.commit()

project4 = Project(
    project_title="UC: Health Sciences Annex Building",
    client="University of Canberra",
    project_value=7600000,
    completed_date=datetime.date(2006, 12, 1),
    description='''Additional teaching facilities were required to address an 
        urgent need for trained nursing and allied health professionals in the 
        community. Manteena was engaged to arrange for design teams, manage 
        the design and construct the building in time to provide facilities 
        for the increased numbers in the academic intake in 2007.
    ''',
    category=category2
)
session.add(project4)
session.commit()
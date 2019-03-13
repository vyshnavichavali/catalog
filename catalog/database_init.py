from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from Data_Setup import *

engine = create_engine('sqlite:///Gold.db')
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

# Delete Gold CompanyName if exisitng.
session.query(GoldCompanyName).delete()
# Delete GoldName if exisitng.
session.query(GoldName).delete()
# Delete User if exisitng.
session.query(User).delete()

# Create sample users data
User1 = User(name="chavali vyshnavi",
             email="chavalivyshnavi124@gmail.com",
                   picture='http://www.enchanting-costarica.com/wp-content/'
                           'uploads/2018/02/jcarvaja17-min.jpg')
session.add(User1)
session.commit()
print ("Successfully Add First User")
# Create sample gold companys
Company1 = GoldCompanyName(name="kalyan jewellers",
                           user_id=1)
session.add(Company1)
session.commit()

Company2 = GoldCompanyName(name="Bombay jewellers",
                           user_id=1)
session.add(Company2)
session.commit

Company3 = GoldCompanyName(name="Malabar Gold and Daimonds",
                           user_id=1)
session.add(Company3)
session.commit()


# Populare a gold with models for testing
# Using different users for gold names year also
Name1 = GoldName(name="Rings",
                 price="20000",
                 discount="20%",
                 date=datetime.datetime.now(),
                 goldcompanynameid=1,
                 user_id=1)
session.add(Name1)
session.commit()

Name2 = GoldName(name="Bangles",
                 price="420000",
                 discount="30%",
                 date=datetime.datetime.now(),
                 goldcompanynameid=2,
                 user_id=1)
session.add(Name2)
session.commit()

Name3 = GoldName(name="Ear Rings",
                 price="40000",
                 discount="40%",
                 date=datetime.datetime.now(),
                 goldcompanynameid=3,
                 user_id=1)
session.add(Name3)
session.commit()


print("Your gold database has been inserted!")

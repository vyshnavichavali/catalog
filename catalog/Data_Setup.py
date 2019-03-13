import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    picture = Column(String(300))


class GoldCompanyName(Base):
    __tablename__ = 'goldcompanyname'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="goldcompanyname")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self.name,
            'id': self.id
        }


class GoldName(Base):
    __tablename__ = 'goldname'
    id = Column(Integer, primary_key=True)
    name = Column(String(350), nullable=False)
    price = Column(String(150))
    discount = Column(String(150))
    date = Column(DateTime, nullable=False)
    goldcompanynameid = Column(Integer, ForeignKey('goldcompanyname.id'))
    goldcompanyname = relationship(
        GoldCompanyName, backref=backref('goldname', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="goldname")

    @property
    def serialize(self):
        """Return objects data in easily serializeable formats"""
        return {
            'name': self. name,
            'price': self. price,
            'discount': self. discount,
            'date': self. date,
            'id': self. id
        }

engin = create_engine('sqlite:///Gold.db')
Base.metadata.create_all(engin)

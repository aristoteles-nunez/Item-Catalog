from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

__author__ = 'Sotsir'

Base = declarative_base()


class User(Base):
    """It stores data obtained from google oauth to manage users
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    picture = Column(Text)


class Category(Base):
    """It stores every category specifying which user has created it
    """
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    items = relationship("Item", cascade="all,delete", backref="parent")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'items': [r.serialize for r in self.items]
        }


class Item(Base):
    """It stores every category's item specifying which user has created it
    """
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    image_path = Column(Text)
    modified_date = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'modified_date': self.modified_date,
            'image_path': self.image_path,
            'category_id': self.category_id
        }

engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.create_all(engine)

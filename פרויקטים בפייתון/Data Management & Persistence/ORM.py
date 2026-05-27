import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
import math
import sqlite3
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

# יצירת מסד נתונים פיזי
engine = create_engine('sqlite:///chef.db')
# גישת Class מסד נתונים
Base = declarative_base()
# # מאפשר לבצע פעולות במסד נתונים
Session = sessionmaker(bind=engine)
session = Session()

# הגדרות טבלה
class Chef(Base):
    __tablename__ = 'chef'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    experience_years = Column(Integer)

    dishes = relationship("Dish", back_populates="chef")
    def __init__(self, name, id, experience_years):
         self.name = name
         self.id = id
         self.experience_years = experience_years

    def __str__(self):
         return f"Chef(name={self.name}, id={self.id}, experience_years={self.experience_years})"

class Dish(Base):
    __tablename__ = 'dish'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    chef_id = Column(Integer, ForeignKey('chef.id'))
    price = Column(Integer)
    
    chef = relationship("Chef", back_populates="dishes")

    def __init__(self, name, chef_id, price):
        self.name = name
        self.chef_id = chef_id
        self.price = price
    def __str__(self):
        return f"Dish(name={self.name}, chef_id={self.chef_id}, price={self.price})"

# יצירת טבלה בפועל
Base.metadata.create_all(engine)

chef1 = Chef('John', 1, 5)
chef2 = Chef('Jane', 2, 10)
chef3 = Chef('Bob', 3, 15)

dish1 = Dish(name="Pasta Bolognese", price=55, chef=chef1)
dish2 = Dish(name="Spaghetti Carbonara", price=65, chef=chef1)
dish3 = Dish(name="Rizotto", price=40, chef=chef2)

session.add_all([chef1, chef2, chef3, dish1, dish2, dish3])
session.commit()

# שליפה ממסד נתונים
chefs = session.query(Chef).all()
for chef in chefs:
    print(chef)
print('\n')
 # עדכון נתונים
chef_to_update = session.query(Chef).filter_by(id=3).first()
chef_to_update.experience_years = 20

# מחיקת נתונים
chef_to_delete = session.query(Chef).filter_by(id=2).first()
session.delete(chef_to_delete)
session.commit()

# שליפה ממסד נתונים
chefs = session.query(Chef).all()
for chef in chefs:
    print(chef)
    

# סינון ממסד נתונים
expensive_dishes = session.query(Dish).filter(Dish.price > 50).all()

for dish in expensive_dishes:
    print(dish)

# מיון ממסד נתונים
sorted_dishes = session.query(Dish).order_by(Dish.price.desc()).all()

for dish in sorted_dishes:
    print(dish)

# הצגת 3 מנות היקרות ביותר
top_3_dishes = session.query(Dish).order_by(Dish.price.desc()).limit(3).all()

for dish in top_3_dishes:
    print(dish)


# כמה מנות יש לכל טבח
chef_dish_count = (session.query(chef.name), func.count(dish.id).join(Dish).group_by(chef.id)).all()


for chef, dish_count in chef_dish_count:
    print(f"{chef}: {dish_count} dishes")

# ממוצע מחיר למנות של כל טבח
avg_price_per_chef = (session.query(chef.name, func.avg(dish.price)).join(Dish).group_by(chef.id)).all()

for chef, avg_price in avg_price_per_chef:
    print(f"{chef}: Average price: {avg_price}")

# שליפת שם טבח יחד עם שם מנה
chef_dish_names = session.query(chef.name, dish.name).join(Dish).all()

for chef_name, dish_name in chef_dish_names:
    print(f"{chef_name}: {dish_name}")
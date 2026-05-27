# ==============================
# ORM & SQLAlchemy – Advanced Queries
# ==============================

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.orm import joinedload
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import random

# ------------------------------
# הגדרת בסיס ומנוע
# ------------------------------
Base = declarative_base()
engine = create_engine("sqlite:///restaurant.db", echo=False)
Session = sessionmaker(bind=engine)
session = Session()


# ------------------------------
# הגדרת טבלאות (Models)
# ------------------------------
class Chef(Base):
    __tablename__ = "chefs"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    experience_years = Column(Integer)

    # קשר למנות
    dishes = relationship("Dish", back_populates="chef")

    def __init__(self, name, experience_years):
        self.name = name
        self.experience_years = experience_years
    def __repr__(self):
        return f"<Chef(name='{self.name}', experience_years={self.experience_years})>"


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    chef_id = Column(Integer, ForeignKey("chefs.id"))

    # קשר הפוך
    chef = relationship("Chef", back_populates="dishes")

    def __init__(self, name, price, chef_id):
        self.name = name
        self.price = price
        self.chef_id = chef_id

    def __repr__(self):
        chef_name = self.chef.name if self.chef else "Unknown"
        return f"<Dish: {self.name} | Price: {self.price}₪ | Chef: {chef_name}>"


# ------------------------------
# יצירת הטבלאות במסד הנתונים
# ------------------------------
Base.metadata.create_all(engine)


# ------------------------------
# פונקציות עזר להוספת נתונים לדוגמה
# ------------------------------
def seed_data():
    if session.query(Chef).first():
        return  # נתונים כבר קיימים

    chefs = [
        Chef(name="John", experience_years=5),
        Chef(name="Jane", experience_years=10),
        Chef(name="Bob", experience_years=15),
        Chef(name="Alice", experience_years=20),
    ]

    dishes = [
        Dish(name="Pasta Bolognese", price=55, chef_id=1),
        Dish(name="Spaghetti Carbonara", price=65, chef_id=1),
        Dish(name="Rizotto", price=40, chef_id=2),
        Dish(name="Lasagna", price=60, chef_id=2),
        Dish(name="Pizza Margherita", price=45, chef_id=3),
        Dish(name="Chicken Alfredo", price=55, chef_id=3),
    ]

    session.add_all(chefs + dishes)
    session.commit()


# ------------------------------
# שאילתות מתקדמות (למימוש)
# ------------------------------

def get_expensive_dishes(min_price):
    return session.query(Dish).options(joinedload(Dish.chef)).filter(Dish.price > min_price).all()


def sort_dishes_by_price(descending=False):
    #מיון המנות לפי מחיר (בסדר עולה או יורד)
    sort_dishes_by_price = session.query(Dish).order_by(Dish.price.desc() if descending else Dish.price).all()
    return sort_dishes_by_price


def get_top_n_dishes(n):
    #החזר את n המנות היקרות ביותר
    TopN = session.query(Dish).order_by(Dish.price.desc()).limit(n).all()
    return TopN


def count_dishes_per_chef():
    #החזר רשימה של (שם טבח, כמות מנות)
    CountDishesPerChef = session.query(Chef.name, func.count(Dish.id)).join(Dish).group_by(Chef.name).all()
    return CountDishesPerChef


def avg_price_per_chef():
    #החזר רשימה של (שם טבח, ממוצע מחיר)
    AvgPricePerChef = session.query(Chef.name, func.avg(Dish.price)).join(Dish).group_by(Chef.name).all()
    return AvgPricePerChef


def list_dishes_with_chefs():
    #הצג רשימה של (שם מנה, שם טבח)
    ListDishesWithChefs = session.query(Dish.name, Chef.name).join(Chef).all()
    return ListDishesWithChefs


def get_dishes_by_chef_name(chef_name):
    #החזר את כל המנות של טבח לפי שמו
    GetDishesByChefName = session.query(Dish).join(Chef).filter(Chef.name == chef_name).all()
    return GetDishesByChefName


def get_most_expensive_dish():
    #החזר את שם המנה היקרה ביותר
    GetMostExpensiveDish = session.query(Dish).order_by(Dish.price.desc()).first()
    return GetMostExpensiveDish


def get_top_chef_by_dish_count():
    #החזר את שם הטבח עם הכי הרבה מנות
    GetTopChefByDishCount = session.query(Chef.name, func.count(Dish.id)).join(Dish).group_by(Chef.name).order_by(func.count(Dish.id).desc()).first()
    return GetTopChefByDishCount


def dishes_by_experienced_chefs(min_years):
    #החזר את כל המנות שטבחים עם ניסיון מעל min_years הכינו
    DishesByExperiencedChefs = session.query(Dish).join(Chef).filter(Chef.experience_years >= min_years).all()
    return DishesByExperiencedChefs


# ------------------------------
# פונקציה ראשית לבדיקה
# ------------------------------
def main():
    # שלב 1 – הוספת נתוני דוגמה (אם אין)
    # שלב 1 – הוספת נתוני דוגמה (אם אין)
    seed_data()

# שלב 2 – קריאות לבדיקה

    print("\n=== Dishes with price above 60 ===\n")
    for dish in get_expensive_dishes(60):
        print(f"{dish.name} : {dish.price}₪ (Chef: {dish.chef.name})")

    print("\n=== Dishes sorted by price in descending order ===\n")
    for dish in sort_dishes_by_price(descending=True):
        print(f"{dish.name} : {dish.price}₪ (Chef: {dish.chef.name})")

    print("\n=== Top 3 most expensive dishes ===\n")
    for dish in get_top_n_dishes(3):
        print(f"{dish.name} : {dish.price}₪ (Chef: {dish.chef.name})")

    print("\n=== Number of dishes per chef ===\n")
    for chef_name, count in count_dishes_per_chef():
        print(f"{chef_name}: {count} Dishes")

    print("\n=== Average price per chef ===\n")
    for chef_name, avg_price in avg_price_per_chef():
        print(f"{chef_name}:{round(avg_price, 2)}₪")

    print("\n=== List of dishes with chefs ===\n")
    for dish_name, chef_name in list_dishes_with_chefs():
        print(f"{dish_name} : Chef: {chef_name}")
    
    names = ["John","Jane","Bob","Alice"]
    name = random.choice(names)
    print(f"\n=== Dishes of chef '{name}' ===\n")
    dishes = get_dishes_by_chef_name(name)
    if dishes:
        for dish in dishes:
            print(f"{dish.name} : {dish.price}₪")
        else:
            print("No dishes found for a chef with this name.")

    print("\n=== Most expensive dish ===\n")
    dish = get_most_expensive_dish()
    print(f"{dish.name} : {dish.price}₪ (Chef: {dish.chef.name})")

    print("\n=== Top chef by number of dishes ===\n")
    chef_name, count = get_top_chef_by_dish_count()
    print(f"{chef_name} : {count} Dishes")

    print("\n=== Dishes of experienced chefs with at least 8 years of experience ===\n")
    for dish in dishes_by_experienced_chefs(8):
        print(f"{dish.name} : {dish.price}₪ (Chef: {dish.chef.name})")


if __name__ == "__main__":
    main()


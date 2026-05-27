import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
import random
import json
import os
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

# ------------------------------
# הגדרת בסיס ומנוע
# ------------------------------
Base = declarative_base()
engine = create_engine("sqlite:///restaurant.db", echo=False)
Session = sessionmaker(bind=engine)
session = Session()

class Driver(Base):
    __tablename__ = 'drivers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)

    vehicles = relationship("Vehicle", back_populates="driver")
    def __init__(self, name, email, phone, id):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
    def __repr__(self):
        return f"<Driver(name={self.name}, email={self.email}, phone={self.phone})>"
    

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    driver = relationship("Driver", back_populates="vehicles")
    def __init__(self, name, driver_id, id):
        self.id = id
        self.name = name
        self.driver_id = driver_id
    def __repr__(self):
        return f"<Vehicle(name={self.name}, driver_id={self.driver_id})>"
    
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    driver = relationship("Driver", back_populates="orders")
    def __init__(self, customer_name, driver_id, id):
        self.id = id
        self.customer_name = customer_name
        self.driver_id = driver_id
    def __repr__(self):
        return f"<Order(customer_name={self.customer_name}, driver_id={self.driver_id})>"
    

Base.metadata.create_all(engine)
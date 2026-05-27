import json
import os
from pathlib import Path
import sqlite3  # מודול מובנה – מאפשר חיבור למסד SQLite
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random


# פתיחת קובץ לכתיבה – מצב 'w' מוחק תוכן קודם אם קיים
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("שלום עולם\n")             # כותב שורה אחת
    f.write("זה קובץ לדוגמה בפייתון\n")
    f.writelines(["שורה שלישית\n", "שורה רביעית\n"])  # כתיבת רשימה של שורות

# קריאת קובץ
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()  # קורא את כל התוכן כ־string אחד
    print("תוכן הקובץ:\n", content)

# מצב 'a' מוסיף שורה לקובץ מבלי למחוק את הקודם
with open("notes.txt", "a", encoding="utf-8") as f:
    f.write("שורה חדשה נוספה בסוף!\n")

# שימוש בלולאה – יעיל לקבצים גדולים
with open("notes.txt", "r", encoding="utf-8") as f:
    for line in f:
        print("שורה:", line.strip())  # strip להסרת רווחים ושבירות שורה

import csv  # מודול מובנה לעבודה עם CSV

# כתיבה לקובץ CSV
with open("menu.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["שם מנה", "מחיר"])      # כותרות
    writer.writerow(["פסטה", 45])
    writer.writerow(["פיצה", 55])

# קריאה מקובץ CSV
with open("menu.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    for row in reader:
        print("שורה:", row)



# נתונים לדוגמה – מילון שמייצג תפריט
menu = {
    "items": [
        {"name": "פסטה", "price": 45},
        {"name": "פיצה", "price": 55},
        {"name": "סלט", "price": 32}
    ]
}

# כתיבה לקובץ JSON
with open("menu.json", "w", encoding="utf-8") as f:
    json.dump(menu, f, ensure_ascii=False, indent=4)
# ensure_ascii=False מאפשר עברית, indent=4 מוסיף הזחה יפה

# קריאה מקובץ JSON
with open("menu.json", "r", encoding="utf-8") as f:
    loaded_menu = json.load(f)
    print("תפריט שהתקבל:", loaded_menu)


# בדיקה אם קובץ קיים
if os.path.exists("menu.json"):
    print("הקובץ קיים!")

# מחיקת קובץ
# os.remove("menu.json")
# print("הקובץ נמחק.")

# קריאת קובץ תמונה
with open("photo.jpg", "rb") as f:
    data = f.read()
    print("אורך הנתונים:", len(data), "בייטים")

# כתיבה חזרה לקובץ חדש
with open("photo_copy.jpg", "wb") as f:
    f.write(data)

try:
    with open("non_existing.txt", "r", encoding="utf-8") as f:
        data = f.read()
except FileNotFoundError:
    print("⚠️ הקובץ לא קיים, ניצור חדש.")
    with open("non_existing.txt", "w", encoding="utf-8") as f:
        f.write("נוצר קובץ חדש בהצלחה.")



# יצירת נתיב
p = Path("data/menu.csv")

# בדיקת קיום תיקיה / קובץ
if not p.parent.exists():
    p.parent.mkdir(parents=True)  # יצירת תיקיות במידת הצורך

# כתיבה לנתיב
p.write_text("שם,מחיר\nפסטה,45\nפיצה,55", encoding="utf-8")

# קריאה
print(p.read_text(encoding="utf-8"))





# חיבור למסד נתונים (אם לא קיים – ייווצר קובץ חדש)
connection = sqlite3.connect("restaurant.db")

# יצירת "Cursor" – מאפשר שליחת פקודות SQL
cursor = connection.cursor()

# יצירת טבלה חדשה
cursor.execute("""
CREATE TABLE IF NOT EXISTS chefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- מזהה ייחודי
    name TEXT NOT NULL,                     -- שם השף
    specialty TEXT,                         -- תחום התמחות
    experience INTEGER                      -- שנות ניסיון
);
""")

# שמירת השינויים (commit = כתיבה פיזית לקובץ)
connection.commit()

# סגירת החיבור
connection.close()



connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

# הכנסת נתון עם ערכים ישירים
cursor.execute("""
INSERT INTO chefs (name, specialty, experience)
VALUES ('דנה', 'קינוחים', 5);
""")

# הכנסת נתונים עם placeholders (בטוח נגד SQL Injection)
cursor.execute("""
INSERT INTO chefs (name, specialty, experience)
VALUES (?, ?, ?);
""", ("בנימין", "מנות עיקריות", 10))

connection.commit()
connection.close()



connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

# שליפה של כל הרשומות
cursor.execute("SELECT * FROM chefs;")

# fetchall() מחזיר רשימה של tuples
rows = cursor.fetchall()

# מעבר על כל השפים
for row in rows:
    print("ID:", row[0], "| שם:", row[1], "| תחום:", row[2], "| ניסיון:", row[3])

connection.close()

connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

# שליפת שפים עם ניסיון מעל 7 שנים
cursor.execute("SELECT * FROM chefs WHERE experience > ?;", (7,))
rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()

connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

# עדכון ניסיון של שף בשם "דנה"
cursor.execute("UPDATE chefs SET experience = ? WHERE name = ?;", (6, "דנה"))

# מחיקת שף בשם "בנימין"
cursor.execute("DELETE FROM chefs WHERE name = ?;", ("בנימין",))

connection.commit()
connection.close()


connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM chefs ORDER BY experience DESC LIMIT 2;")
rows = cursor.fetchall()

for r in rows:
    print("שף:", r[1], "| ניסיון:", r[3])

connection.close()


connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*), AVG(experience), MAX(experience) FROM chefs;")
count, avg, max_exp = cursor.fetchone()
print(f"סה\"כ שפים: {count}, ממוצע ניסיון: {avg:.1f}, מקסימום: {max_exp}")

connection.close()


# מאפשר החזרת תוצאות כמילון – במקום tuple
connection = sqlite3.connect("restaurant.db")
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("SELECT * FROM chefs;")
for row in cursor.fetchall():
    print(dict(row))  # {'id': 1, 'name': 'דנה', ...}

connection.close()

chefs = [
    ("רותי", "מנות טבעוניות", 4),
    ("אור", "מנות אסייתיות", 6)
]

connection = sqlite3.connect("restaurant.db")
cursor = connection.cursor()

cursor.executemany("INSERT INTO chefs (name, specialty, experience) VALUES (?, ?, ?);", chefs)
connection.commit()
connection.close()

if os.path.exists("restaurant.db"):
    print("✅ מסד הנתונים נשמר בהצלחה בגודל:", os.path.getsize("restaurant.db"), "בייטים")



# יצירת מנוע חיבור למסד (SQLite – קובץ מקומי)
engine = create_engine("sqlite:///restaurant_orm.db", echo=True)
# echo=True גורם להדפסת כל פקודות ה-SQL שמתבצעות מאחורי הקלעים

# בסיס לכל המחלקות – “תבנית על”
Base = declarative_base()

# מחלקה שממפה לטבלת chefs במסד הנתונים
class Chef(Base):
    __tablename__ = "chefs"  # שם הטבלה

    id = Column(Integer, primary_key=True)  # עמודת מפתח ראשי
    name = Column(String, nullable=False)   # שם השף
    specialty = Column(String)              # תחום התמחות
    experience = Column(Integer)            # שנות ניסיון

    def __repr__(self):
        return f"<Chef name={self.name}, specialty={self.specialty}, exp={self.experience}>"

# יצירת כל הטבלאות שהוגדרו על בסיס המחלקות
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()  # פתיחת “סשן” חדש לעבודה

# יצירת אובייקטים של שפים
chef1 = Chef(name="דנה", specialty="קינוחים", experience=5)
chef2 = Chef(name="בנימין", specialty="מנות גורמה", experience=10)

# הוספה לסשן
session.add_all([chef1, chef2])

# ביצוע השינויים במסד
session.commit()

# שליפה של כל השפים
all_chefs = session.query(Chef).all()
for chef in all_chefs:
    print(chef)

# סינון לפי תנאי (WHERE)
pro_chefs = session.query(Chef).filter(Chef.experience > 7).all()
for chef in pro_chefs:
    print("שף מנוסה:", chef.name)

# שליפה של שף ספציפי
chef = session.query(Chef).filter_by(name="דנה").first()

if chef:
    chef.experience = 6  # שינוי ישיר באובייקט
    session.commit()      # השינוי מתעדכן אוטומטית בטבלה

chef_to_delete = session.query(Chef).filter_by(name="בנימין").first()

if chef_to_delete:
    session.delete(chef_to_delete)
    session.commit()


# מחלקה שממפה לטבלת dishes
class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    chef_id = Column(Integer, ForeignKey("chefs.id"))  # קשר לטבלת chefs

    # כל מנה שייכת לשף מסוים
    chef = relationship("Chef", backref="dishes")

# יצירת הטבלה החדשה במסד
Base.metadata.create_all(engine)

# הוספת מנה לשף קיים
chef = session.query(Chef).filter_by(name="דנה").first()
dish = Dish(name="עוגת שוקולד", price=32, chef=chef)
session.add(dish)
session.commit()

# הדפסת כל המנות של שף
for d in chef.dishes:
    print(f"{chef.name} מכינה {d.name} במחיר {d.price}₪")
session.close()


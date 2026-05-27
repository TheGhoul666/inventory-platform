import sys ,io
import time
import re

l = [1,2,3]
l1 = l
l1.append(4)
print(l)

print("Count: ",sys.getrefcount(l)) # כמה פעמים נשתמש במשתנה


print()
s = "hi"
s1 = s
s1 += "!"
print(s)  # hi  ← נוצר אובייקט חדש

print()
nums = [1,2,3]
nums1 = nums
nums1.append(4)
print(nums) # [1, 2, 3, 4] ← אותו אובייקט בזיכרון
print("Count: ",sys.getrefcount(nums)) # כמה פעמים נשתמש במשתנה

print()
# פייתון שומרת בזיכרון מספרים בין 5 ל256
integer = 100
integer1 = 100
print(integer is integer1) # True בודק את המקום בזיכרון

print()
integer2 = 1000
integer3 = 1000
print(integer2 is integer3) # False בודק את המקום בזיכרון

print()
# שגיאה נפוצה במקרה שנשתמש במשתנה שאינו ישר מקום בזיכרון
def add_to_list(val, lst=[]):
    lst.append(val)
    return lst
print(add_to_list(1))
print(add_to_list(2))
print(add_to_list(3))

print()
sys.stdin = io.StringIO("Beni \n") # מקבל מהמשתמש שם
name = input("Enter your name: ") # מקבל מהמשתמש שם
print("Your name is", name) # יוצר אובייקט חדש  

# בדיקת טיפוסים casting
print()
num = "5"
print(type(num)) # <class 'str'>
nums1 = int(num)
print(type(nums1))  # <class 'int'>

# בדיקת טיפוסים casting
# int("5.2")  # ❌ ValueError
# float("5.2")  # ✅ 5.2

# בדיקת טיפוסים isinstance
print()
print(isinstance(1, int)) # True
print(isinstance(1, str)) # False

# בדיקת is ובדיקת ==
# בדיקת is מבדיק את המקום בזיכרון
# בדיקת == מבדיק את הערך
print()
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)  # True
print(a is b)  # False

# בדיקת טיפוס
print()
x = 5
print(isinstance(x, int))  # True
print(isinstance(x, (int, float)))  # True – אם אחד מהם

# id() מחזיר את כתובת האובייקט בזיכרון.
# hash() מחזיר חתימה מתמטית קבועה (אם האובייקט immutable).
print()
x = "hello"
print(id(x))
print(hash(x))

# לא שינינו אובייקט, אלא יצרנו חדש — כי int הוא immutable.
# דוגמה להרכבת ידע
print()
a = 10
b = a
a += 1


print("\n\n\n\n")
print("Exercise recall: ")

def id_test(var, var2): # בדיקה שהמשתנה שנשתמש בו ישר מקום בזיכרון
    print(f"{var is var2}")

def mutbale_vs_immutable(var): # בדיקה אם המשתנה mutable או immutable
    if var == list:
        print("mutable")
    else:
        print("immutable")

def hash_id_test(var): # בדיקה שהמשתנה שנשתמש בו ישר מקום בזיכרון
    print(hash(var))
    print(id(var))

def mutable_default(value, lst=[]): # בדיקה שהמשתנה שנשתמש בו ישר מקום בזיכרון
    if lst is None:
        lst = []
    lst.append(value)
    return lst
def equal_and_is_test(var1, var2): # בדיקת שווה או שונה בזיכרון ובערכים
    print(var1 == var2)
    print(var1 is var2)

def nums_test(num): # הוכחה שפייתון שומר מספרים בין 5 ל256
    if num > 5 | num <257:
        print("true")
    else:
        print("false")


# פייתון מעריכה כל ביטוי ל־ True או False.
# רק בלוק אחד יורץ.
x = 10
if x > 10:
    print("Upper than 10")
elif x == 10:
    print("Equal to 10")
else:
    print("Smaller than 10")

# כל אלה נחשבים False:
# 0, "", [], {}, None, False

# כל אלה נחשבים True:
# 1, "a", [1], {"a": 1}, True

# כל if פוגע בביצעוים לכן עדיף להשתמש ב and / or
# if user == "chef" and access == "admin":
#   print("גישה מלאה")

# Short-Circuit Evaluation
def a(): print("a"); return True
def b(): print("b"); return False
print()
if a() or b():
    print("It's true")
# פלט:
# a
# נכנס

print()
# for is Iterator
for i in [1, 2, 3]:
    print(i)

print()
nums = [1, 2, 3]
it = iter(nums) # יצירת Iterator
# גישה מלאה לIterator
print(next(it))  # 1 
print(next(it))  # 2
print(next(it))  # 3
# StopIteration

print()
# כל עוד הביטוי True — הלולאה ממשיכה.
i = 0
while i < 5:
    print(i)
    i += 1

print()
# הלולאה תמשיך עד שנגיע ל break
for i in range(5):
    if i == 3:
        break
else:
    print("It's not break")

print()
# continue מדלג על החלק הנוכחי וממשיך לסיבוב הבא.
for i in range(5):
    if i == 3:
        continue
    print(i)

print()
# range לא יוצר רשימה בזיכרון!
for i in range(5):
    print(i)

print()
# אם אתה רוצה גם את המיקום והערך:
# שימוש בenumerate
for index, value in enumerate(["A", "B", "C"], start=1):
    print(index, value)

print("\n\n\n\n")


# List - מערך
# רשימה היא מערך דינמי – גודל גמיש, ניתן לשינוי (mutable)
numbers = [1, 2, 3]

# הוספת איבר לסוף הרשימה – פעולה בזמן O(1)
numbers.append(4)

# הכנסת איבר באמצע מזיזה את כל האיברים שמימין לו – פעולה בזמן O(n)
numbers.insert(1, 10)

# הסרה לפי ערך (אם לא קיים -> ValueError)
numbers.remove(3)

# הסרה לפי מיקום (אם לא קיים -> IndexError)
numbers.pop(1)

# מחיקת כל האיברים
numbers.clear()

# מדפיסה את הרשימה
print(numbers)  # [1, 10, 2, 4]

# מלכודת של רשימה
# 3 פניות לאותה רשימה
x = [[0]*3]*3
x[0][0] = 1
print(x)
# [[1, 0, 0], [1, 0, 0], [1, 0, 0]]

# פתרון למלכודת
x = [[0 for j in range(3)] for i in range(3)]

# Tuple - טאפלים
# כמו רשימה אבל immutable (לא ניתן לשנות)
coordinates = (10, 20)

# יתרון hashable 
# שימוש נפוץ: החזרת כמה ערכים מפונקציה:
def get_position():
    return (10, 20)

x, y = get_position()


# מילונים (Dictionary)
# כל ערך נשמר תחת “מפתח” ייחודי.
# כל key עובר דרך פונקציית hash.
# מילון מבוסס על Hash Table – מיפוי מפתח לערך
user = {"name": "Beni", "age": 29}

# שליפה לפי מפתח (גישה בזמן O(1))
print(user["name"])  # Beni

# הוספת מפתח חדש
user["job"] = "Engineer"

# עדכון ערך קיים
user["age"] = 30

print(user)

# שימוש ב-get() למניעת KeyError אם המפתח לא קיים
print(user.get("salary", "לא קיים"))

# הדפסת כל המפתחות
for key in user.keys():
    print(key)

# הדפסת כל הערכים
for value in user.values():
    print(value)

# הדפסת זוגות מפתח–ערך
for key, value in user.items():
    print(key, ":", value)

# הערה: מפתחות חייבים להיות Immutable (int, str, tuple)
# valid_key = {(1, 2): "נקודה"}   # עובד
# invalid_key = {[1, 2]: "נקודה"} # ❌ שגיאה – רשימה היא mutable ולכן לא ניתנת ל-hash

# הערה: ערכים חייבים להיות Hashable
# valid_value = "נקודה"  # עובד
# invalid_value = [1, 2]  # ❌ שגיאה






# Set הוא אוסף ייחודי של איברים (אין כפילויות)
nums = {1, 2, 3, 3, 2}
print(nums)  # {1, 2, 3}

# הוספה והסרה
nums.add(4)
nums.discard(2)
print(nums)

# בדיקת שייכות מהירה מאוד (O(1))
print(3 in nums)  # True

# פעולות קבוצתיות (תורת הקבוצות)
a = {1, 2, 3}
b = {3, 4, 5}
print(a | b)  # איחוד
print(a & b)  # חיתוך
print(a - b)  # הפרש
print(a ^ b)  # התוספות
print()


# Immutable – האובייקט לא משתנה, נוצר חדש בכל שינוי
a = "hello"
b = a
b += " world"
print(a)  # hello (נשאר זהה)
print()


# Mutable – שינוי משפיע על אותו אובייקט בזיכרון
x = [1, 2]
y = x
y.append(3)
print(x)  # [1, 2, 3]
print()


# רשימה של מילונים – דוגמה אמיתית לייצוג משתמשים
users = [
    {"name": "Beni", "skills": ["Python", "SQL"]},
    {"name": "Dana", "skills": ["HTML", "CSS"]}
]

# גישה לנתון פנימי
print(users[1]["skills"][0])  # HTML
print()

# הוספת כישור חדש למשתמש הראשון
users[0]["skills"].append("Pandas")
print(users[0])
print()

# יצירת רשימה של ריבועים
squares = [x**2 for x in range(5)]

# יצירת set של מספרים זוגיים
evens = {x for x in range(10) if x % 2 == 0}

# יצירת מילון (מפה בין אינדקס לאות)
index_map = {i: chr(65+i) for i in range(5)}

print()
print(squares)
print()
print(evens)
print()
print(index_map)
print()

# יצירת רשימה וחדשה
data = list(range(1_000_000))
target = 999_999

# חיפוש ברשימה – איטי (O(n))
print()
start = time.time()
print(target in data)
print("List time:", time.time() - start)
print()

# המרת הרשימה ל-Set – חיפוש מהיר (O(1))
print()
data = set(data)
start = time.time()
print(target in data)
print("Set time:", time.time() - start)



# String (מחרוזת)
# מחרוזת היא רצף Immutable של תווים (כלומר – אי אפשר לשנותה)
text = "Hello, world!"
print(text)
print()

# כל תו במחרוזת הוא למעשה Unicode code point (מספר שמייצג תו)
print(ord('H'))  # מציג את הקוד המספרי של האות H
print(chr(1513))  # מציג את התו לפי הקוד המספרי
print()

# גישה לתווים ו Slicing
text = "Python"
print(text[0])     # 'P' – תו ראשון
print(text[-1])    # 'n' – תו אחרון
print(text[0:3])   # 'Pyt' – חיתוך (slice)
print(text[:2])    # 'Py' – מתחילת המחרוזת
print(text[2:])    # 'thon' – מהתו השלישי עד הסוף
print()

# חיתוך עם צעדים (step)
print(text[::2])   # 'Pto' – כל תו שני
print(text[::-1])  # 'nohtyP' – הפוך
print()

# חיבור מחרוזות
greeting = "Hello" + " " + "world!"
print(greeting)
print()

# חיבור באמצעות f-string – הדרך המומלצת (מהירה וברורה)
name = "Beni"
print(f"Hello, {name}!")
print()

# בעיה בביצועים: חיבור מחרוזות רבות בתוך לולאה
result = ""
for i in range(10000):
    result += str(i)
# כל איטרציה יוצרת מחרוזת חדשה בזיכרון!

# הפתרון היעיל:
result = "".join(str(i) for i in range(10000))

sentence = "  Python is Awesome!  "

print(sentence.lower())     # כל התווים באותיות קטנות
print(sentence.upper())     # כל התווים באותיות גדולות
print(sentence.strip())     # הסרת רווחים מההתחלה והסוף
print(sentence.replace("Awesome", "Powerful"))  # החלפת מחרוזת
print(sentence.split())     # פיצול לפי רווחים → ['Python', 'is', 'Awesome!']
print("-".join(["one", "two", "three"]))        # חיבור עם מפריד
print()

# בדיקות פשוטות
text = "hello world"
print(text.startswith("he"))  # True
print(text.endswith("ld"))    # True
print("wor" in text)          # True
print()


# חשוב מאוד: לפתוח קבצים עם encoding מתאים
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("שלום עולם")

# קריאה נכונה של קובץ בעברית
with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()
print(text)

data = "12345"
print(data.isdigit())   # True
print()

word = "Python"
print(word.isalpha())   # True
print()

mixed = "Python3"
print(mixed.isalnum())  # True – אותיות או ספרות
print()

spacey = "   "
print(spacey.isspace())  # True – רק רווחים
print()

# חיפוש תת מחרוזות
text = "Python programming language"
print(text.find("pro"))  # 7 – המיקום הראשון של 'pro'
print(text.find("xyz"))  # -1 – לא נמצא


# השוואה רגישה לאותיות
a = "abc"
b = "ABC"

# השוואה רגישה לאותיות
print(a == b)  # False

# השוואה לא רגישה לאותיות
print(a.lower() == b.lower())  # True

text = "Phone: 050-1234567"
pattern = r"\d{3}-\d{7}"

match = re.search(pattern, text)
if match:
    print("Found:", match.group())  # נמצא: 050-1234567
print()

# חיפוש תת מחרוזות
text = "Python programming language"
print(text.find("pro"))  # 7 – המיקום הראשון של 'pro'
print(text.find("xyz"))  # -1 – לא נמצא

# Functions
# הגדרת פונקציה – פייתון שומרת בזיכרון אובייקט מסוג function בשם greet
def greet():
    print("Hello, world")  # שורת הדפסה בלבד

# קריאה לפונקציה – נוצר Frame חדש בזיכרון עם שם הפונקציה
greet()  # ברגע שסיימה – ה-Frame נסגר ונמחק

# פונקציה שמקבלת פרמטר אחד
def greet_user(name):
    # name הוא משתנה מקומי שנוצר רק בתוך ה-Frame של הפונקציה
    print(f"Hello {name}!")

# הקריאה מעבירה את הערך 'בנימין' כ-Reference לפרמטר name
greet_user("Beni")  # פלט: שלום בנימין!

# ערך ברירת מחדל נקבע בזמן הגדרת הפונקציה, לא בזמן הקריאה
def greet(name="Guest"):
    print(f"Hello {name}!")

greet()          # משתמש בברירת המחדל → שלום אורח!
greet("Beni")     # משתמש בערך שנשלח → שלום דנה!


# הגדרה לא נכונה – ברירת מחדל היא רשימה (Mutable)
def add_item(item, lst=[]):
    lst.append(item)
    return lst

print(add_item("a"))  # ['a']
print(add_item("b"))  # ['a', 'b'] ← באג! הרשימה נשמרה מהקריאה הקודמת

# הפתרון הנכון – שימוש ב-None כדי ליצור אובייקט חדש בכל קריאה
def add_item(item, lst=None):
    if lst is None:      # נוצרה רק אם לא הועברה רשימה חיצונית
        lst = []         # כל קריאה יוצרת רשימה חדשה בזיכרון
    lst.append(item)
    return lst

print(add_item("a"))  # ['a']
print(add_item("b"))  # ['b']

x = 10  # משתנה גלובלי – נשמר ב-Global Namespace

def show_value():
    x = 5  # משתנה מקומי – נוצר בתוך ה-Frame של הפונקציה
    print("x Local:", x)

show_value()         # מדפיס את הערך המקומי 5
print("x Global ", x)  # מדפיס 10 – לא השתנה

count = 0  # משתנה גלובלי

def increment():
    global count   # אומר לפייתון להשתמש במשתנה מהמרחב הגלובלי
    count += 1     # משנה את count שבחוץ

increment()
print(count)  # 1

def outer():
    x = 5
    def inner():
        nonlocal x  # מתייחס למשתנה מהפונקציה העוטפת (לא גלובלי)
        x += 1
        print("x Inner", x)
    inner()
    print("x Outer: ", x)

outer()
# פלט:
# x הפנימי: 6
# x החיצוני: 6

# *args – מקבל מספר בלתי מוגבל של ארגומנטים כטאפול
def print_numbers(*args):
    print("Got: ", args)
    for n in args:
        print(n)

print_numbers(1, 2, 3)
# פלט:
# קיבלתי: (1, 2, 3)
# 1
# 2
# 3

# **kwargs – מקבל מפתחות וערכים כ-dictionary
def print_user(**kwargs):
    print("User info:")
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_user(name="Beni", age=29, job="Engineer")

# פונקציה רגילה
def square(x):
    return x**2

# פונקציית למבדה – אותה תוצאה בשורה אחת
square_lambda = lambda x: x**2

print(square_lambda(5))  # 25

# שימושים נפוצים – map, filter
nums = [1, 2, 3, 4]
double = list(map(lambda n: n * 2, nums))
print(double)  # [2, 4, 6, 8]

# פונקציה רגילה שמחזירה טקסט
def greet(name):
    return f"Hello {name}"

# פונקציה שמקבלת פונקציה אחרת כפרמטר
def run_function(func, value):
    print("Running function...")
    print(func(value))

# העברת פונקציה כפרמטר – מבלי להריץ אותה (ללא סוגריים)
run_function(greet, "Beni")



#OOP
# הגדרת מחלקה בסיסית
class Chef:
    # פונקציית אתחול (Constructor)
    def __init__(self, name, specialty):
        # self מצביע על האובייקט הנוכחי בזיכרון (this בשפות אחרות)
        self.name = name
        self.specialty = specialty

    # מתודה רגילה – פעולה של האובייקט
    def cook(self, dish):
        print(f"{self.name} מכין {dish} ({self.specialty})")

# יצירת אובייקט (Instance) – נוצר אובייקט חדש בזיכרון מסוג Chef
chef1 = Chef("בנימין", "מנות גורמה")
chef2 = Chef("דנה", "קינוחים")

# קריאת מתודות (פייתון שולחת אוטומטית את self)
chef1.cook("סטייק")
chef2.cook("עוגת שוקולד")

class Restaurant:
    # משתנה מחלקה – משותף לכל האובייקטים
    restaurant_type = "מסעדת שף"

    def __init__(self, name):
        # משתנה מופע – שייך רק לאובייקט הספציפי
        self.name = name

# לכל אובייקט יש שם שונה, אבל סוג זהה
r1 = Restaurant("שף דנה")
r2 = Restaurant("ביסטרו בנימין")

print(r1.restaurant_type)  # "מסעדת שף"
print(r2.restaurant_type)
print(r1.name)             # "שף דנה"
print(r2.name)             # "ביסטרו בנימין"



# מחלקת בסיס
class Chef:
    def __init__(self, name):
        self.name = name

    def cook(self):
        print(f"{self.name} מבשל מנות רגילות.")

# מחלקה יורשת (מומחה)
class PastryChef(Chef):
    def cook(self):
        # דריסה (Override) של מתודה קיימת
        print(f"{self.name} אופה עוגות וקינוחים!")

# מחלקת משנה נוספת
class SushiChef(Chef):
    def cook(self):
        print(f"{self.name} מכין סושי מקצועי!")

# ירושה בפעולה
c1 = PastryChef("דנה")
c2 = SushiChef("בנימין")

c1.cook()  # דריסה – אופה עוגות
c2.cook()  # דריסה – מכין סושי


class AdvancedChef(Chef):
    def __init__(self, name, specialty):
        # super() מפעילה את __init__ של המחלקה האב
        super().__init__(name)
        self.specialty = specialty

    def cook(self):
        # מבצע גם את פעולת האב וגם פעולה חדשה
        super().cook()
        print(f"{self.name} גם מומחה ב-{self.specialty}.")

chef = AdvancedChef("גיא", "בשרים מעושנים")
chef.cook()

# כמה מחלקות עם אותה מתודה בשם cook
class ItalianChef:
    def cook(self):
        print("מכין פסטה")

class JapaneseChef:
    def cook(self):
        print("מכין סושי")

# פונקציה שמקבלת כל שף, בלי לדעת מאיזה סוג
def start_cooking(chef):
    chef.cook()  # קריאה פולימורפית – כל אחד מגיב אחרת

for c in [ItalianChef(), JapaneseChef()]:
    start_cooking(c)

class Employee:
    def __init__(self, name, role):
        self.name = name
        self.role = role

    def work(self):
        print(f"{self.name} עובד כ-{self.role}")

class Chef(Employee):
    def __init__(self, name, specialty):
        super().__init__(name, "שף")
        self.specialty = specialty

    def work(self):
        print(f"{self.name} מבשל {self.specialty}")

class Waiter(Employee):
    def __init__(self, name):
        super().__init__(name, "מלצר")

    def work(self):
        print(f"{self.name} מגיש לשולחנות")

workers = [Chef("דנה", "איטלקי"), Waiter("אור"), Chef("בנימין", "קינוחים")]
for w in workers:
    w.work()  # כל אחד מפעיל גרסה משלו של work()

class Recipe:
    def __init__(self, name, secret_ingredient):
        self.name = name
        self.__secret = secret_ingredient  # מאפיין פרטי (name mangling)

    def reveal_secret(self):
        print(f"המרכיב הסודי של {self.name} הוא {self.__secret}")

cake = Recipe("עוגת שוקולד", "שוקולד בלגי")
cake.reveal_secret()

# ניסיון גישה ישירה ייכשל
# print(cake.__secret)  ❌ AttributeError

# אבל אפשר לגשת בעקיפין (לא מומלץ)
print(cake._Recipe__secret)  # גישה "פרוצה"


from dataclasses import dataclass

@dataclass
class MenuItem:
    name: str
    price: float

item = MenuItem("פיצה", 59.9)
print(item)  # הדפסה נוחה אוטומטית

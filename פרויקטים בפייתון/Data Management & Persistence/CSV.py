import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3 
import csv

# def create_csv():
#     csvfile = 'student.csv'
#     try:
#         with open(csvfile, 'r') as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 print(row['id'], row['name'], row['grade'])
#     except FileNotFoundError:
#         with open('student.csv', 'w', newline='') as f:
#             writer = csv.DictWriter(f, fieldnames=['id', 'name', 'grade'])
#             writer.writeheader()
#             writer.writerow({'id': 1, 'name': 'John', 'grade': random.randint(0, 100)})
#             writer.writerow({'id': 2, 'name': 'Jane', 'grade': random.randint(0, 100)})
#             writer.writerow({'id': 3, 'name': 'Bob', 'grade': random.randint(0, 100)})
# students = []
# def add_student(id, name, grade):
#     try:
#         with open('student.csv', 'r', newline='') as f:
#             fieldnames = ['id', 'name', 'grade']
#             reader = csv.DictReader(f)
#             for row in reader:
#                 students.append(row)
#     except FileNotFoundError:
#         with open('student.csv', 'w', newline='') as f:
#             writer = csv.DictWriter(f, fieldnames=fieldnames)
#             writer.writeheader()
#             for student in students:
#                 writer.writerow(student)
#             writer.writerow({'id': id, 'name': name, 'grade': grade})
# def list_students():
#     for student in students:
#         print(f"ID: {student['id']}, Name: {student['name']}, Grade: {student['grade']}")
# def delete_student(id):
#     try:
#         students.remove(id)
#     except (KeyError, IndexError, TypeError, ValueError):
#         print("student not found")
# def update_student(id , new_garde):
#     try:
#         for student in students:
#             if student['id'] == id:
#                 student['grade'] = new_garde
#     except (KeyError, IndexError, TypeError, ValueError):
#         print("student not found")
#     finally:
#         for student in students:
#             print(f"ID: {student['id']}, Name: {student['name']}, Grade: {student['grade']}")

# csvfile = 'student.csv'
# with open('student.csv', 'w', newline='') as f:
#     writer = csv.DictWriter(f, fieldnames=['id', 'name', 'grade'])
#     writer.writeheader()
#     writer.writerow({'id': 1, 'name': 'John', 'grade': 90})
#     writer.writerow({'id': 2, 'name': 'Jane', 'grade': 85})
#     writer.writerow({'id': 3, 'name': 'Bob', 'grade': 95})

# with open(csvfile, 'r') as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         print(row['id'], row['name'], row['grade'])

# # Change the garde from index
# students = []
# with open(csvfile, 'r', newline='') as f:
#     fieldnames = ['id', 'name', 'grade']
#     reader = csv.DictReader(f)
#     for row in reader:
#         students.append(row)
# for student in students:
#     if student['id'] == '2':
#         student['grade'] = 100


# with open(csvfile, 'w', newline='') as f:
#     writer = csv.DictWriter(f, fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(students)
#     print('\nCSV file updated successfully! (Update one student)')
#     for student in students:
#         print(f"ID: {student['id']}, Name: {student['name']}, Grade: {student['grade']}")

# print('\nCSV file updated successfully! (Remove one student)')
# with open('student.csv', 'r'):
#     students = [student for student in csv.DictReader(open('student.csv'))]
#     students.remove(students[random.randint(0, len(students) - 1)])
#     for student in students:
#         print(f"ID: {student['id']}, Name: {student['name']}, Grade: {student['grade']}")
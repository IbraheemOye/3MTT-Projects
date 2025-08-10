# -*- coding: utf-8 -*-
"""
Created on Sun Aug 10 15:05:26 2025

@author: Fampride
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Database setup
conn = sqlite3.connect('school.db')
c = conn.cursor()

# Create tables if they don't exist
def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 roll_no TEXT UNIQUE,
                 class TEXT,
                 section TEXT,
                 dob DATE,
                 gender TEXT,
                 address TEXT,
                 parent_name TEXT,
                 parent_contact TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS teachers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 emp_id TEXT UNIQUE,
                 subject TEXT,
                 qualification TEXT,
                 dob DATE,
                 gender TEXT,
                 address TEXT,
                 contact TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 class_name TEXT UNIQUE,
                 section TEXT,
                 class_teacher_id INTEGER,
                 room_no TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS subjects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 subject_name TEXT UNIQUE,
                 subject_code TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 student_id INTEGER,
                 date DATE,
                 status TEXT,
                 FOREIGN KEY(student_id) REFERENCES students(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS grades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 student_id INTEGER,
                 subject_id INTEGER,
                 term TEXT,
                 grade TEXT,
                 remarks TEXT,
                 FOREIGN KEY(student_id) REFERENCES students(id),
                 FOREIGN KEY(subject_id) REFERENCES subjects(id))''')
    
    conn.commit()

init_db()

# Page configuration
st.set_page_config(
    page_title="School DBMS",
    page_icon="🏫",
    layout="wide"
)



# Dashboard Page
st.title("🏫 School Management Dashboard")
    
    # Get counts from database
student_count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
teacher_count = c.execute("SELECT COUNT(*) FROM teachers").fetchone()[0]
class_count = c.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
    
    # Display metrics
col1, col2, col3 = st.columns(3)
with col1:
        st.metric("Total Students", student_count)
with col2:
        st.metric("Total Teachers", teacher_count)
with col3:
        st.metric("Total Classes", class_count)
    
    # Recent activity
st.subheader("Recent Activity")
recent_students = pd.read_sql("SELECT name, roll_no, class FROM students ORDER BY id DESC LIMIT 5", conn)
st.dataframe(recent_students)

# Student Management
st.title("👨‍🎓 Student Management")
    
operation = st.selectbox("Select Operation", ["Add Student", "View Students", "Update Student", "Delete Student"])
    
if operation == "Add Student":
    with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name*")
                roll_no = st.text_input("Roll Number*")
                class_name = st.text_input("Class*")
                section = st.text_input("Section")
            with col2:
                dob = st.date_input("Date of Birth", max_value=datetime.now().date())
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                parent_name = st.text_input("Parent/Guardian Name")
                parent_contact = st.text_input("Parent/Guardian Contact")
            
            address = st.text_area("Address")
            
            if st.form_submit_button("Add Student"):
                if name and roll_no and class_name:
                    try:
                        c.execute("INSERT INTO students (name, roll_no, class, section, dob, gender, address, parent_name, parent_contact) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (name, roll_no, class_name, section, dob, gender, address, parent_name, parent_contact))
                        conn.commit()
                        st.success("Student added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Roll number must be unique!")
                else:
                    st.warning("Please fill all required fields (*)")
    
students = pd.read_sql("SELECT * FROM students", conn)
st.dataframe(students)
        
        # Search functionality
st.subheader("Search Students")
search_term = st.text_input("Search by name or roll number")
if search_term:
            search_results = pd.read_sql("SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ?", 
                                        conn, params=(f"%{search_term}%", f"%{search_term}%"))
            st.dataframe(search_results)
    
elif operation == "Update Student":
        students = pd.read_sql("SELECT id, name, roll_no FROM students", conn)
        selected_student = st.selectbox("Select Student", students['name'] + " (" + students['roll_no'] + ")")
        
        if selected_student:
            student_id = students.loc[students['name'] + " (" + students['roll_no'] + ")" == selected_student, 'id'].values[0]
            student_data = c.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
            
            with st.form("update_student_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Full Name*", value=student_data[1])
                    roll_no = st.text_input("Roll Number*", value=student_data[2])
                    class_name = st.text_input("Class*", value=student_data[3])
                    section = st.text_input("Section", value=student_data[4])
                with col2:
                    dob = st.date_input("Date of Birth", value=datetime.strptime(student_data[5], "%Y-%m-%d").date())
                    gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(student_data[6]))
                    parent_name = st.text_input("Parent/Guardian Name", value=student_data[8])
                    parent_contact = st.text_input("Parent/Guardian Contact", value=student_data[9])
                
                address = st.text_area("Address", value=student_data[7])
                
                if st.form_submit_button("Update Student"):
                    c.execute("UPDATE students SET name=?, roll_no=?, class=?, section=?, dob=?, gender=?, address=?, parent_name=?, parent_contact=? WHERE id=?",
                            (name, roll_no, class_name, section, dob, gender, address, parent_name, parent_contact, student_id))
                    conn.commit()
                    st.success("Student updated successfully!")
    
elif operation == "Delete Student":
        students = pd.read_sql("SELECT id, name, roll_no FROM students", conn)
        selected_student = st.selectbox("Select Student to Delete", students['name'] + " (" + students['roll_no'] + ")")
        
        if selected_student and st.button("Delete Student"):
            student_id = students.loc[students['name'] + " (" + students['roll_no'] + ")" == selected_student, 'id'].values[0]
            c.execute("DELETE FROM students WHERE id=?", (student_id,))
            conn.commit()
            st.success("Student deleted successfully!")

# Teacher Management (similar structure as student)

st.title("👨‍🏫 Teacher Management")
    
operation = st.selectbox("Select Operation", ["Add Teacher", "View Teachers", "Update Teacher", "Delete Teacher"])
    
if operation == "Add Teacher":
        with st.form("add_teacher_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name*")
                emp_id = st.text_input("Employee ID*")
                subject = st.text_input("Subject")
                qualification = st.text_input("Qualification")
            with col2:
                dob = st.date_input("Date of Birth", max_value=datetime.now().date())
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                contact = st.text_input("Contact Number")
            
            address = st.text_area("Address")
            
            if st.form_submit_button("Add Teacher"):
                if name and emp_id:
                    try:
                        c.execute("INSERT INTO teachers (name, emp_id, subject, qualification, dob, gender, address, contact) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (name, emp_id, subject, qualification, dob, gender, address, contact))
                        conn.commit()
                        st.success("Teacher added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Employee ID must be unique!")
                else:
                    st.warning("Please fill all required fields (*)")
    
elif operation == "View Teachers":
        teachers = pd.read_sql("SELECT * FROM teachers", conn)
        st.dataframe(teachers)
    
    # Similar update and delete functionality as students
    # ... (implementation similar to student section)

# Class Management
st.title("👥 Class Management")
    
operation = st.selectbox("Select Operation", ["Add Class", "View Classes", "Assign Class Teacher", "Delete Class"])
    
if operation == "Add Class":
        with st.form("add_class_form"):
            class_name = st.text_input("Class Name*")
            section = st.text_input("Section")
            room_no = st.text_input("Room Number")
            
            if st.form_submit_button("Add Class"):
                if class_name:
                    try:
                        c.execute("INSERT INTO classes (class_name, section, room_no) VALUES (?, ?, ?)",
                                (class_name, section, room_no))
                        conn.commit()
                        st.success("Class added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Class name must be unique!")
                else:
                    st.warning("Please fill all required fields (*)")
    
elif operation == "View Classes":
        classes = pd.read_sql("SELECT * FROM classes", conn)
        st.dataframe(classes)
    
elif operation == "Assign Class Teacher":
        classes = pd.read_sql("SELECT id, class_name FROM classes", conn)
        teachers = pd.read_sql("SELECT id, name FROM teachers", conn)
        
        selected_class = st.selectbox("Select Class", classes['class_name'])
        selected_teacher = st.selectbox("Select Teacher", teachers['name'])
        
        if st.button("Assign Teacher"):
            class_id = classes.loc[classes['class_name'] == selected_class, 'id'].values[0]
            teacher_id = teachers.loc[teachers['name'] == selected_teacher, 'id'].values[0]
            
            c.execute("UPDATE classes SET class_teacher_id=? WHERE id=?", (teacher_id, class_id))
            conn.commit()
            st.success(f"Assigned {selected_teacher} as class teacher for {selected_class}")

# Subject Management
st.title("📚 Subject Management")
    
operation = st.selectbox("Select Operation", ["Add Subject", "View Subjects", "Delete Subject"])
    
if operation == "Add Subject":
        with st.form("add_subject_form"):
            subject_name = st.text_input("Subject Name*")
            subject_code = st.text_input("Subject Code")
            
            if st.form_submit_button("Add Subject"):
                if subject_name:
                    try:
                        c.execute("INSERT INTO subjects (subject_name, subject_code) VALUES (?, ?)",
                                (subject_name, subject_code))
                        conn.commit()
                        st.success("Subject added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Subject name must be unique!")
                else:
                    st.warning("Please fill all required fields (*)")
    
elif operation == "View Subjects":
        subjects = pd.read_sql("SELECT * FROM subjects", conn)
        st.dataframe(subjects)

# Attendance Management
st.title("📅 Attendance Management")
    
operation = st.selectbox("Select Operation", ["Mark Attendance", "View Attendance"])
    
if operation == "Mark Attendance":
        date = st.date_input("Select Date", datetime.now().date())
        selected_class = st.selectbox("Select Class", pd.read_sql("SELECT class_name FROM classes", conn)['class_name'])
        
        if date and selected_class:
            students = pd.read_sql("SELECT id, name, roll_no FROM students WHERE class=?", conn, params=(selected_class,))
            
            if not students.empty:
                st.subheader(f"Attendance for {selected_class} on {date}")
                
                attendance_data = []
                for _, student in students.iterrows():
                    status = st.radio(
                        f"{student['name']} ({student['roll_no']})",
                        ["Present", "Absent"],
                        key=f"attendance_{student['id']}"
                    )
                    attendance_data.append({
                        'student_id': student['id'],
                        'date': date,
                        'status': status
                    })
                
                if st.button("Save Attendance"):
                    for record in attendance_data:
                        c.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
                                (record['student_id'], record['date'], record['status']))
                    conn.commit()
                    st.success("Attendance saved successfully!")
            else:
                st.warning("No students found in this class")
elif operation == "View Attendance":
        date = st.date_input("Select Date to View")
        selected_class = st.selectbox("Select Class", pd.read_sql("SELECT class_name FROM classes", conn)['class_name'])
        
        if date and selected_class and st.button("View Attendance"):
            attendance = pd.read_sql('''
                SELECT s.name, s.roll_no, a.status 
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date = ? AND s.class = ?
            ''', conn, params=(date, selected_class))
            
            if not attendance.empty:
                st.dataframe(attendance)
                
                # Attendance summary
                present_count = len(attendance[attendance['status'] == 'Present'])
                absent_count = len(attendance[attendance['status'] == 'Absent'])
                
                col1, col2 = st.columns(2)
                col1.metric("Present Students", present_count)
                col2.metric("Absent Students", absent_count)
            else:
                st.warning("No attendance records found for this date and class")

# Grade Management
st.title("🎓 Grade Management")
operation = st.selectbox("Select Operation", ["Add Grades", "View Grades"])
    
if operation == "Add Grades":
        selected_class = st.selectbox("Select Class", pd.read_sql("SELECT DISTINCT class FROM students", conn)['class'])
        selected_subject = st.selectbox("Select Subject", pd.read_sql("SELECT subject_name FROM subjects", conn)['subject_name'])
        term = st.selectbox("Select Term", ["First Term", "Mid Term", "Final Term"])
        
        students = pd.read_sql("SELECT id, name, roll_no FROM students WHERE class=?", conn, params=(selected_class,))
        
        
        if not students.empty:
            st.subheader(f"Enter Grades for {selected_subject} - {term}")
            
            grades_data = []
            for _, student in students.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{student['name']} ({student['roll_no']})")
                with col2:
                    grade = st.selectbox(
                        "Grade",
                        ["A+", "A", "B+", "B", "C+", "C", "D", "F"],
                        key=f"grade_{student['id']}"
                    )
                
                remarks = st.text_input("Remarks", key=f"remarks_{student['id']}")
                
                grades_data.append({
                    'student_id': student['id'],
                    'subject_id': subject_id,
                    'term': term,
                    'grade': grade,
                    'remarks': remarks
                })
            
            if st.button("Save Grades"):
                for record in grades_data:
                    c.execute('''
                        INSERT INTO grades (student_id, subject_id, term, grade, remarks)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (record['student_id'], record['subject_id'], record['term'], record['grade'], record['remarks']))
                conn.commit()
                st.success("Grades saved successfully!")
    
elif operation == "View Grades":
        selected_class = st.selectbox("Select Class", pd.read_sql("SELECT DISTINCT class FROM students", conn)['class'])
        selected_student = st.selectbox("Select Student", 
                                      pd.read_sql("SELECT name FROM students WHERE class=?", conn, params=(selected_class,))['name'])
        
        if selected_student and st.button("View Grades"):
            grades = pd.read_sql('''
                SELECT g.term, s.subject_name, g.grade, g.remarks
                FROM grades g
                JOIN subjects s ON g.subject_id = s.id
                JOIN students st ON g.student_id = st.id
                WHERE st.name = ?
                ORDER BY g.term
            ''', conn, params=(selected_student,))
            
            if not grades.empty:
                st.dataframe(grades)
            else:
                st.warning("No grades found for this student")

# Close connection when done
conn.close()




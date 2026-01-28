"""
School Management System - Complete Streamlit Application
Author: Senior Full Stack Developer
Version: 1.0.0
Description: A comprehensive school management system with student, teacher, attendance, and salary management
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import os
from io import BytesIO

# ==================== DATABASE CONFIGURATION ====================

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_name='school_management.db'):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.db_name, check_same_thread=False)
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Admin Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Students Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                father_name TEXT NOT NULL,
                class TEXT NOT NULL,
                section TEXT NOT NULL,
                roll_number INTEGER NOT NULL,
                dob DATE NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(class, section, roll_number)
            )
        ''')
        
        # Teachers Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                qualification TEXT NOT NULL,
                assigned_subjects TEXT NOT NULL,
                assigned_class TEXT NOT NULL,
                phone TEXT NOT NULL,
                salary REAL NOT NULL,
                joining_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Subjects Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                class TEXT NOT NULL,
                teacher_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
                UNIQUE(subject_name, class)
            )
        ''')
        
        # Student Attendance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                attendance_date DATE NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                UNIQUE(student_id, attendance_date)
            )
        ''')
        
        # Teacher Attendance Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                attendance_date DATE NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
                UNIQUE(teacher_id, attendance_date)
            )
        ''')
        
        # Student Results Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                exam_type TEXT NOT NULL,
                marks REAL NOT NULL,
                total_marks REAL NOT NULL,
                exam_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
                UNIQUE(student_id, subject_id, exam_type, exam_date)
            )
        ''')
        
        # Salary Records Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salary_records (
                salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                base_salary REAL NOT NULL,
                deductions REAL DEFAULT 0,
                net_salary REAL NOT NULL,
                paid_date DATE,
                status TEXT DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
                UNIQUE(teacher_id, month, year)
            )
        ''')
        
        # Create default admin if not exists
        cursor.execute("SELECT * FROM admins WHERE username='admin'")
        if not cursor.fetchone():
            default_password = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                         ("admin", default_password))
        
        conn.commit()
        conn.close()

# ==================== AUTHENTICATION FUNCTIONS ====================

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    """Verify admin login credentials"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    cursor.execute("SELECT * FROM admins WHERE username=? AND password=?", 
                  (username, hashed_password))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None

# ==================== STUDENT MANAGEMENT FUNCTIONS ====================

def add_student(name, father_name, class_name, section, roll_number, dob, phone, address):
    """Add new student to database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO students (name, father_name, class, section, roll_number, dob, phone, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, father_name, class_name, section, roll_number, dob, phone, address))
        
        conn.commit()
        conn.close()
        return True, "Student added successfully!"
    except sqlite3.IntegrityError:
        return False, "Error: Roll number already exists in this class and section!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_all_students():
    """Retrieve all students from database"""
    db = DatabaseManager()
    conn = db.get_connection()
    df = pd.read_sql_query("SELECT * FROM students ORDER BY student_id DESC", conn)
    conn.close()
    return df

def update_student(student_id, name, father_name, class_name, section, roll_number, dob, phone, address):
    """Update student information"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE students 
            SET name=?, father_name=?, class=?, section=?, roll_number=?, dob=?, phone=?, address=?
            WHERE student_id=?
        ''', (name, father_name, class_name, section, roll_number, dob, phone, address, student_id))
        
        conn.commit()
        conn.close()
        return True, "Student updated successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def delete_student(student_id):
    """Delete student from database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        
        conn.commit()
        conn.close()
        return True, "Student deleted successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def search_students(search_term, search_by):
    """Search students by various criteria"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    if search_by == "Name":
        query = f"SELECT * FROM students WHERE name LIKE '%{search_term}%' ORDER BY name"
    elif search_by == "Class":
        query = f"SELECT * FROM students WHERE class='{search_term}' ORDER BY roll_number"
    elif search_by == "Roll Number":
        query = f"SELECT * FROM students WHERE roll_number={search_term} ORDER BY class"
    else:
        query = "SELECT * FROM students ORDER BY student_id DESC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==================== TEACHER MANAGEMENT FUNCTIONS ====================

def add_teacher(name, qualification, subjects, assigned_class, phone, salary, joining_date):
    """Add new teacher to database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO teachers (name, qualification, assigned_subjects, assigned_class, phone, salary, joining_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, qualification, subjects, assigned_class, phone, salary, joining_date))
        
        conn.commit()
        conn.close()
        return True, "Teacher added successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_all_teachers():
    """Retrieve all teachers from database"""
    db = DatabaseManager()
    conn = db.get_connection()
    df = pd.read_sql_query("SELECT * FROM teachers ORDER BY teacher_id DESC", conn)
    conn.close()
    return df

def update_teacher(teacher_id, name, qualification, subjects, assigned_class, phone, salary, joining_date):
    """Update teacher information"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE teachers 
            SET name=?, qualification=?, assigned_subjects=?, assigned_class=?, phone=?, salary=?, joining_date=?
            WHERE teacher_id=?
        ''', (name, qualification, subjects, assigned_class, phone, salary, joining_date, teacher_id))
        
        conn.commit()
        conn.close()
        return True, "Teacher updated successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def delete_teacher(teacher_id):
    """Delete teacher from database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM teachers WHERE teacher_id=?", (teacher_id,))
        
        conn.commit()
        conn.close()
        return True, "Teacher deleted successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ==================== ATTENDANCE FUNCTIONS ====================

def mark_student_attendance(student_id, attendance_date, status):
    """Mark attendance for a student"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO student_attendance (student_id, attendance_date, status)
            VALUES (?, ?, ?)
        ''', (student_id, attendance_date, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_student_attendance(class_name, section, attendance_date):
    """Get attendance for a specific class and date"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    query = f'''
        SELECT s.student_id, s.name, s.roll_number, 
               COALESCE(sa.status, 'Not Marked') as status
        FROM students s
        LEFT JOIN student_attendance sa 
            ON s.student_id = sa.student_id AND sa.attendance_date = '{attendance_date}'
        WHERE s.class = '{class_name}' AND s.section = '{section}'
        ORDER BY s.roll_number
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def mark_teacher_attendance(teacher_id, attendance_date, status):
    """Mark attendance for a teacher"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO teacher_attendance (teacher_id, attendance_date, status)
            VALUES (?, ?, ?)
        ''', (teacher_id, attendance_date, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_teacher_attendance_report(month, year):
    """Get monthly teacher attendance report"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    query = f'''
        SELECT t.teacher_id, t.name, 
               COUNT(CASE WHEN ta.status='Present' THEN 1 END) as present_days,
               COUNT(CASE WHEN ta.status='Absent' THEN 1 END) as absent_days,
               COUNT(ta.id) as total_days
        FROM teachers t
        LEFT JOIN teacher_attendance ta ON t.teacher_id = ta.teacher_id
        WHERE strftime('%m', ta.attendance_date) = '{month:02d}' 
          AND strftime('%Y', ta.attendance_date) = '{year}'
        GROUP BY t.teacher_id, t.name
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_student_attendance_report(student_id, month, year):
    """Get student attendance report for a specific month"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    query = f'''
        SELECT attendance_date, status
        FROM student_attendance
        WHERE student_id = {student_id}
          AND strftime('%m', attendance_date) = '{month:02d}'
          AND strftime('%Y', attendance_date) = '{year}'
        ORDER BY attendance_date
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==================== SUBJECT MANAGEMENT FUNCTIONS ====================

def add_subject(subject_name, class_name, teacher_id):
    """Add new subject to database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO subjects (subject_name, class, teacher_id)
            VALUES (?, ?, ?)
        ''', (subject_name, class_name, teacher_id))
        
        conn.commit()
        conn.close()
        return True, "Subject added successfully!"
    except sqlite3.IntegrityError:
        return False, "Error: Subject already exists for this class!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_all_subjects():
    """Retrieve all subjects from database"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    query = '''
        SELECT s.subject_id, s.subject_name, s.class, 
               COALESCE(t.name, 'Not Assigned') as teacher_name
        FROM subjects s
        LEFT JOIN teachers t ON s.teacher_id = t.teacher_id
        ORDER BY s.class, s.subject_name
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_subjects_by_class(class_name):
    """Get subjects for a specific class"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    query = f'''
        SELECT subject_id, subject_name
        FROM subjects
        WHERE class = '{class_name}'
        ORDER BY subject_name
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==================== RESULTS MANAGEMENT FUNCTIONS ====================

def add_result(student_id, subject_id, exam_type, marks, total_marks, exam_date):
    """Add student result"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO student_results 
            (student_id, subject_id, exam_type, marks, total_marks, exam_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, subject_id, exam_type, marks, total_marks, exam_date))
        
        conn.commit()
        conn.close()
        return True, "Result added successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_student_results(student_id, exam_type):
    """Get results for a specific student and exam"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    query = f'''
        SELECT s.subject_name, r.marks, r.total_marks, 
               ROUND((r.marks * 100.0 / r.total_marks), 2) as percentage
        FROM student_results r
        JOIN subjects s ON r.subject_id = s.subject_id
        WHERE r.student_id = {student_id} AND r.exam_type = '{exam_type}'
        ORDER BY s.subject_name
    '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def calculate_grade(percentage):
    """Calculate grade based on percentage"""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"

# ==================== SALARY MANAGEMENT FUNCTIONS ====================

def calculate_monthly_salary(teacher_id, month, year):
    """Calculate monthly salary with attendance-based deductions"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get teacher base salary
    cursor.execute("SELECT salary FROM teachers WHERE teacher_id=?", (teacher_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return None, None, None
    
    base_salary = result[0]
    
    # Get attendance data
    cursor.execute(f'''
        SELECT COUNT(*) as total_days,
               COUNT(CASE WHEN status='Present' THEN 1 END) as present_days,
               COUNT(CASE WHEN status='Absent' THEN 1 END) as absent_days
        FROM teacher_attendance
        WHERE teacher_id = ? 
          AND strftime('%m', attendance_date) = ?
          AND strftime('%Y', attendance_date) = ?
    ''', (teacher_id, f'{month:02d}', str(year)))
    
    attendance = cursor.fetchone()
    conn.close()
    
    if attendance[0] == 0:  # No attendance marked
        return base_salary, 0, base_salary
    
    total_days = attendance[0]
    absent_days = attendance[2]
    
    # Calculate deduction (per day deduction = base_salary / 30)
    per_day_salary = base_salary / 30
    deductions = per_day_salary * absent_days
    net_salary = base_salary - deductions
    
    return base_salary, deductions, net_salary

def save_salary_record(teacher_id, month, year, base_salary, deductions, net_salary, status='Pending'):
    """Save salary record to database"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        month_name = month_names[month - 1]
        
        cursor.execute('''
            INSERT OR REPLACE INTO salary_records 
            (teacher_id, month, year, base_salary, deductions, net_salary, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_id, month_name, year, base_salary, deductions, net_salary, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_salary_records(teacher_id=None):
    """Get salary records"""
    db = DatabaseManager()
    conn = db.get_connection()
    
    if teacher_id:
        query = f'''
            SELECT sr.salary_id, t.name, sr.month, sr.year, sr.base_salary, 
                   sr.deductions, sr.net_salary, sr.status, sr.paid_date
            FROM salary_records sr
            JOIN teachers t ON sr.teacher_id = t.teacher_id
            WHERE sr.teacher_id = {teacher_id}
            ORDER BY sr.year DESC, sr.month DESC
        '''
    else:
        query = '''
            SELECT sr.salary_id, t.name, sr.month, sr.year, sr.base_salary, 
                   sr.deductions, sr.net_salary, sr.status, sr.paid_date
            FROM salary_records sr
            JOIN teachers t ON sr.teacher_id = t.teacher_id
            ORDER BY sr.year DESC, sr.month DESC
        '''
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ==================== DASHBOARD FUNCTIONS ====================

def get_dashboard_stats():
    """Get statistics for dashboard"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    
    # Total teachers
    cursor.execute("SELECT COUNT(*) FROM teachers")
    total_teachers = cursor.fetchone()[0]
    
    # Today's student attendance
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute(f'''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN status='Present' THEN 1 END) as present
        FROM student_attendance
        WHERE attendance_date = '{today}'
    ''')
    student_attendance = cursor.fetchone()
    
    # Today's teacher attendance
    cursor.execute(f'''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN status='Present' THEN 1 END) as present
        FROM teacher_attendance
        WHERE attendance_date = '{today}'
    ''')
    teacher_attendance = cursor.fetchone()
    
    # Students by class
    cursor.execute('''
        SELECT class, COUNT(*) as count
        FROM students
        GROUP BY class
        ORDER BY class
    ''')
    class_distribution = cursor.fetchall()
    
    conn.close()
    
    return {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'student_attendance': student_attendance,
        'teacher_attendance': teacher_attendance,
        'class_distribution': class_distribution
    }

# ==================== STREAMLIT UI ====================

def login_page():
    """Display login page"""
    st.title("🏫 School Management System")
    st.subheader("Admin Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username and password:
                    if verify_login(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password!")
                else:
                    st.warning("Please enter both username and password!")
        
        st.info("**Default Credentials:**\n\nUsername: `admin`\n\nPassword: `admin123`")

def dashboard_page():
    """Display dashboard with statistics"""
    st.title("📊 Dashboard")
    
    stats = get_dashboard_stats()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", stats['total_students'])
    
    with col2:
        st.metric("Total Teachers", stats['total_teachers'])
    
    with col3:
        student_present = stats['student_attendance'][1] if stats['student_attendance'][0] > 0 else 0
        st.metric("Students Present Today", student_present)
    
    with col4:
        teacher_present = stats['teacher_attendance'][1] if stats['teacher_attendance'][0] > 0 else 0
        st.metric("Teachers Present Today", teacher_present)
    
    st.divider()
    
    # Class distribution chart
    if stats['class_distribution']:
        st.subheader("Students by Class")
        
        class_data = pd.DataFrame(stats['class_distribution'], columns=['Class', 'Count'])
        st.bar_chart(class_data.set_index('Class'))
    
    # Recent activity
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Add Student", use_container_width=True):
            st.session_state.page = "Student Management"
            st.rerun()
    
    with col2:
        if st.button("✅ Mark Attendance", use_container_width=True):
            st.session_state.page = "Student Attendance"
            st.rerun()
    
    with col3:
        if st.button("📝 Enter Results", use_container_width=True):
            st.session_state.page = "Student Results"
            st.rerun()

def student_management_page():
    """Student management page"""
    st.title("👨‍🎓 Student Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 View Students", "➕ Add Student", "✏️ Edit/Delete"])
    
    with tab1:
        st.subheader("All Students")
        
        # Search functionality
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Search", placeholder="Enter search term")
        with col2:
            search_by = st.selectbox("Search By", ["Name", "Class", "Roll Number"])
        
        if search_term:
            df = search_students(search_term, search_by)
        else:
            df = get_all_students()
        
        if not df.empty:
            # Display without created_at column
            display_df = df.drop(columns=['created_at'], errors='ignore')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Export to CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No students found.")
    
    with tab2:
        st.subheader("Add New Student")
        
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*", placeholder="Enter student name")
                father_name = st.text_input("Father's Name*", placeholder="Enter father's name")
                class_name = st.selectbox("Class*", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
                section = st.selectbox("Section*", ["A", "B", "C", "D", "E"])
            
            with col2:
                roll_number = st.number_input("Roll Number*", min_value=1, step=1)
                dob = st.date_input("Date of Birth*", max_value=date.today())
                phone = st.text_input("Phone Number*", placeholder="+92-XXX-XXXXXXX")
                address = st.text_area("Address*", placeholder="Enter complete address")
            
            submit = st.form_submit_button("Add Student", use_container_width=True)
            
            if submit:
                if all([name, father_name, phone, address]):
                    success, message = add_student(
                        name, father_name, class_name, section, 
                        roll_number, dob, phone, address
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill all required fields!")
    
    with tab3:
        st.subheader("Edit or Delete Student")
        
        df = get_all_students()
        
        if not df.empty:
            # Select student to edit
            student_options = df.apply(
                lambda x: f"{x['student_id']} - {x['name']} (Class {x['class']}-{x['section']})", 
                axis=1
            ).tolist()
            
            selected = st.selectbox("Select Student", student_options)
            
            if selected:
                student_id = int(selected.split(" - ")[0])
                student = df[df['student_id'] == student_id].iloc[0]
                
                with st.form("edit_student_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("Full Name", value=student['name'])
                        father_name = st.text_input("Father's Name", value=student['father_name'])
                        class_name = st.selectbox("Class", 
                            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
                            index=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"].index(student['class'])
                        )
                        section = st.selectbox("Section", ["A", "B", "C", "D", "E"],
                            index=["A", "B", "C", "D", "E"].index(student['section'])
                        )
                    
                    with col2:
                        roll_number = st.number_input("Roll Number", value=int(student['roll_number']), min_value=1)
                        dob = st.date_input("Date of Birth", value=pd.to_datetime(student['dob']).date())
                        phone = st.text_input("Phone Number", value=student['phone'])
                        address = st.text_area("Address", value=student['address'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("Update Student", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("Delete Student", use_container_width=True, type="secondary")
                    
                    if update_btn:
                        success, message = update_student(
                            student_id, name, father_name, class_name, 
                            section, roll_number, dob, phone, address
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        success, message = delete_student(student_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No students found in the database.")

def student_attendance_page():
    """Student attendance page"""
    st.title("✅ Student Attendance")
    
    tab1, tab2 = st.tabs(["📝 Mark Attendance", "📊 Attendance Reports"])
    
    with tab1:
        st.subheader("Mark Daily Attendance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            class_name = st.selectbox("Select Class", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
        
        with col2:
            section = st.selectbox("Select Section", ["A", "B", "C", "D", "E"])
        
        with col3:
            attendance_date = st.date_input("Attendance Date", value=date.today())
        
        if st.button("Load Students"):
            df = get_student_attendance(class_name, section, attendance_date)
            
            if not df.empty:
                st.session_state.attendance_df = df
                st.session_state.attendance_date = attendance_date
                st.rerun()
        
        if 'attendance_df' in st.session_state:
            st.write(f"**Class {class_name}-{section} | Date: {attendance_date}**")
            
            with st.form("attendance_form"):
                attendance_data = []
                
                for idx, row in st.session_state.attendance_df.iterrows():
                    col1, col2, col3 = st.columns([1, 2, 2])
                    
                    with col1:
                        st.write(f"**{row['roll_number']}**")
                    
                    with col2:
                        st.write(row['name'])
                    
                    with col3:
                        current_status = row['status'] if row['status'] != 'Not Marked' else 'Present'
                        status = st.radio(
                            f"Status_{row['student_id']}", 
                            ["Present", "Absent"],
                            index=0 if current_status == 'Present' else 1,
                            horizontal=True,
                            key=f"attendance_{row['student_id']}",
                            label_visibility="collapsed"
                        )
                        attendance_data.append((row['student_id'], status))
                
                submit = st.form_submit_button("Save Attendance", use_container_width=True)
                
                if submit:
                    success_count = 0
                    for student_id, status in attendance_data:
                        if mark_student_attendance(student_id, st.session_state.attendance_date, status):
                            success_count += 1
                    
                    if success_count == len(attendance_data):
                        st.success(f"Attendance marked successfully for {success_count} students!")
                        del st.session_state.attendance_df
                        st.balloons()
                    else:
                        st.warning(f"Attendance marked for {success_count}/{len(attendance_data)} students.")
    
    with tab2:
        st.subheader("Attendance Reports")
        
        # Get all students for selection
        students_df = get_all_students()
        
        if not students_df.empty:
            student_options = students_df.apply(
                lambda x: f"{x['student_id']} - {x['name']} (Class {x['class']}-{x['section']})", 
                axis=1
            ).tolist()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_student = st.selectbox("Select Student", student_options)
            
            with col2:
                month = st.selectbox("Month", range(1, 13), 
                    format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
            
            with col3:
                year = st.selectbox("Year", range(2020, 2030), 
                    index=range(2020, 2030).index(datetime.now().year))
            
            if selected_student:
                student_id = int(selected_student.split(" - ")[0])
                
                attendance_df = get_student_attendance_report(student_id, month, year)
                
                if not attendance_df.empty:
                    # Calculate statistics
                    total_days = len(attendance_df)
                    present_days = len(attendance_df[attendance_df['status'] == 'Present'])
                    absent_days = len(attendance_df[attendance_df['status'] == 'Absent'])
                    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
                    
                    # Display statistics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Days", total_days)
                    col2.metric("Present", present_days)
                    col3.metric("Absent", absent_days)
                    col4.metric("Attendance %", f"{attendance_percentage:.1f}%")
                    
                    # Display attendance table
                    st.dataframe(attendance_df, use_container_width=True, hide_index=True)
                    
                    # Export option
                    csv = attendance_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Report",
                        csv,
                        file_name=f"attendance_report_{student_id}_{month}_{year}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No attendance records found for selected month.")
        else:
            st.info("No students found in the database.")

def teacher_management_page():
    """Teacher management page"""
    st.title("👨‍🏫 Teacher Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 View Teachers", "➕ Add Teacher", "✏️ Edit/Delete"])
    
    with tab1:
        st.subheader("All Teachers")
        
        df = get_all_teachers()
        
        if not df.empty:
            display_df = df.drop(columns=['created_at'], errors='ignore')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Export to CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"teachers_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No teachers found.")
    
    with tab2:
        st.subheader("Add New Teacher")
        
        with st.form("add_teacher_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*", placeholder="Enter teacher name")
                qualification = st.text_input("Qualification*", placeholder="e.g., M.Sc, B.Ed")
                subjects = st.text_input("Assigned Subjects*", placeholder="e.g., Math, Science")
                assigned_class = st.text_input("Assigned Class*", placeholder="e.g., 5-A, 6-B")
            
            with col2:
                phone = st.text_input("Phone Number*", placeholder="+92-XXX-XXXXXXX")
                salary = st.number_input("Monthly Salary (PKR)*", min_value=0.0, step=1000.0)
                joining_date = st.date_input("Joining Date*", value=date.today())
            
            submit = st.form_submit_button("Add Teacher", use_container_width=True)
            
            if submit:
                if all([name, qualification, subjects, assigned_class, phone]) and salary > 0:
                    success, message = add_teacher(
                        name, qualification, subjects, assigned_class, 
                        phone, salary, joining_date
                    )
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill all required fields!")
    
    with tab3:
        st.subheader("Edit or Delete Teacher")
        
        df = get_all_teachers()
        
        if not df.empty:
            teacher_options = df.apply(
                lambda x: f"{x['teacher_id']} - {x['name']} ({x['assigned_subjects']})", 
                axis=1
            ).tolist()
            
            selected = st.selectbox("Select Teacher", teacher_options)
            
            if selected:
                teacher_id = int(selected.split(" - ")[0])
                teacher = df[df['teacher_id'] == teacher_id].iloc[0]
                
                with st.form("edit_teacher_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("Full Name", value=teacher['name'])
                        qualification = st.text_input("Qualification", value=teacher['qualification'])
                        subjects = st.text_input("Assigned Subjects", value=teacher['assigned_subjects'])
                        assigned_class = st.text_input("Assigned Class", value=teacher['assigned_class'])
                    
                    with col2:
                        phone = st.text_input("Phone Number", value=teacher['phone'])
                        salary = st.number_input("Monthly Salary", value=float(teacher['salary']), step=1000.0)
                        joining_date = st.date_input("Joining Date", 
                            value=pd.to_datetime(teacher['joining_date']).date())
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("Update Teacher", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("Delete Teacher", use_container_width=True, type="secondary")
                    
                    if update_btn:
                        success, message = update_teacher(
                            teacher_id, name, qualification, subjects, 
                            assigned_class, phone, salary, joining_date
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        success, message = delete_teacher(teacher_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No teachers found in the database.")

def teacher_attendance_page():
    """Teacher attendance page"""
    st.title("✅ Teacher Attendance")
    
    tab1, tab2 = st.tabs(["📝 Mark Attendance", "📊 Attendance Reports"])
    
    with tab1:
        st.subheader("Mark Daily Attendance")
        
        attendance_date = st.date_input("Attendance Date", value=date.today())
        
        teachers_df = get_all_teachers()
        
        if not teachers_df.empty:
            with st.form("teacher_attendance_form"):
                st.write(f"**Date: {attendance_date}**")
                
                attendance_data = []
                
                for idx, teacher in teachers_df.iterrows():
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    
                    with col1:
                        st.write(f"**{teacher['teacher_id']}**")
                    
                    with col2:
                        st.write(teacher['name'])
                    
                    with col3:
                        st.write(teacher['assigned_subjects'])
                    
                    with col4:
                        status = st.radio(
                            f"Status_{teacher['teacher_id']}", 
                            ["Present", "Absent"],
                            horizontal=True,
                            key=f"teacher_att_{teacher['teacher_id']}",
                            label_visibility="collapsed"
                        )
                        attendance_data.append((teacher['teacher_id'], status))
                
                submit = st.form_submit_button("Save Attendance", use_container_width=True)
                
                if submit:
                    success_count = 0
                    for teacher_id, status in attendance_data:
                        if mark_teacher_attendance(teacher_id, attendance_date, status):
                            success_count += 1
                    
                    if success_count == len(attendance_data):
                        st.success(f"Attendance marked successfully for {success_count} teachers!")
                        st.balloons()
                    else:
                        st.warning(f"Attendance marked for {success_count}/{len(attendance_data)} teachers.")
        else:
            st.info("No teachers found in the database.")
    
    with tab2:
        st.subheader("Monthly Attendance Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            month = st.selectbox("Select Month", range(1, 13), 
                format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
        
        with col2:
            year = st.selectbox("Select Year", range(2020, 2030), 
                index=range(2020, 2030).index(datetime.now().year))
        
        if st.button("Generate Report"):
            report_df = get_teacher_attendance_report(month, year)
            
            if not report_df.empty:
                # Calculate attendance percentage
                report_df['attendance_percentage'] = (
                    report_df['present_days'] / report_df['total_days'] * 100
                ).round(2)
                
                st.dataframe(report_df, use_container_width=True, hide_index=True)
                
                # Export option
                csv = report_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Report",
                    csv,
                    file_name=f"teacher_attendance_{month}_{year}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No attendance records found for selected month.")

def subject_management_page():
    """Subject management page"""
    st.title("📚 Subject Management")
    
    tab1, tab2 = st.tabs(["📋 View Subjects", "➕ Add Subject"])
    
    with tab1:
        st.subheader("All Subjects")
        
        df = get_all_subjects()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No subjects found.")
    
    with tab2:
        st.subheader("Add New Subject")
        
        teachers_df = get_all_teachers()
        
        with st.form("add_subject_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                subject_name = st.text_input("Subject Name*", placeholder="e.g., Mathematics")
                class_name = st.selectbox("Class*", ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
            
            with col2:
                if not teachers_df.empty:
                    teacher_options = ["Not Assigned"] + teachers_df.apply(
                        lambda x: f"{x['teacher_id']} - {x['name']}", axis=1
                    ).tolist()
                    selected_teacher = st.selectbox("Assign Teacher", teacher_options)
                    
                    if selected_teacher != "Not Assigned":
                        teacher_id = int(selected_teacher.split(" - ")[0])
                    else:
                        teacher_id = None
                else:
                    st.info("No teachers available. Please add teachers first.")
                    teacher_id = None
            
            submit = st.form_submit_button("Add Subject", use_container_width=True)
            
            if submit:
                if subject_name:
                    success, message = add_subject(subject_name, class_name, teacher_id)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter subject name!")

def student_results_page():
    """Student results page"""
    st.title("📝 Student Results")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Results", "📊 View Results", "🎓 Result Card"])
    
    with tab1:
        st.subheader("Enter Student Results")
        
        students_df = get_all_students()
        
        if not students_df.empty:
            student_options = students_df.apply(
                lambda x: f"{x['student_id']} - {x['name']} (Class {x['class']}-{x['section']})", 
                axis=1
            ).tolist()
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_student = st.selectbox("Select Student", student_options)
                exam_type = st.selectbox("Exam Type", ["Mid Term", "Final Term", "Monthly Test", "Quiz"])
            
            with col2:
                exam_date = st.date_input("Exam Date", value=date.today())
            
            if selected_student:
                student_id = int(selected_student.split(" - ")[0])
                student = students_df[students_df['student_id'] == student_id].iloc[0]
                class_name = student['class']
                
                # Get subjects for this class
                subjects_df = get_subjects_by_class(class_name)
                
                if not subjects_df.empty:
                    with st.form("results_form"):
                        st.write(f"**Enter marks for {student['name']} - Class {class_name}**")
                        
                        results_data = []
                        
                        for idx, subject in subjects_df.iterrows():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.write(f"**{subject['subject_name']}**")
                            
                            with col2:
                                obtained_marks = st.number_input(
                                    f"Obtained Marks", 
                                    min_value=0.0, 
                                    key=f"obtained_{subject['subject_id']}",
                                    label_visibility="collapsed"
                                )
                            
                            with col3:
                                total_marks = st.number_input(
                                    f"Total Marks", 
                                    min_value=1.0, 
                                    value=100.0,
                                    key=f"total_{subject['subject_id']}",
                                    label_visibility="collapsed"
                                )
                            
                            results_data.append((subject['subject_id'], obtained_marks, total_marks))
                        
                        submit = st.form_submit_button("Save Results", use_container_width=True)
                        
                        if submit:
                            success_count = 0
                            for subject_id, marks, total in results_data:
                                success, message = add_result(
                                    student_id, subject_id, exam_type, marks, total, exam_date
                                )
                                if success:
                                    success_count += 1
                            
                            if success_count == len(results_data):
                                st.success(f"Results saved successfully for all {success_count} subjects!")
                                st.balloons()
                            else:
                                st.warning(f"Results saved for {success_count}/{len(results_data)} subjects.")
                else:
                    st.info(f"No subjects found for Class {class_name}. Please add subjects first.")
        else:
            st.info("No students found in the database.")
    
    with tab2:
        st.subheader("View Student Results")
        
        students_df = get_all_students()
        
        if not students_df.empty:
            student_options = students_df.apply(
                lambda x: f"{x['student_id']} - {x['name']} (Class {x['class']}-{x['section']})", 
                axis=1
            ).tolist()
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_student = st.selectbox("Select Student", student_options, key="view_student")
            
            with col2:
                exam_type = st.selectbox("Exam Type", 
                    ["Mid Term", "Final Term", "Monthly Test", "Quiz"], 
                    key="view_exam")
            
            if selected_student:
                student_id = int(selected_student.split(" - ")[0])
                
                results_df = get_student_results(student_id, exam_type)
                
                if not results_df.empty:
                    st.dataframe(results_df, use_container_width=True, hide_index=True)
                    
                    # Calculate overall statistics
                    total_obtained = results_df['marks'].sum()
                    total_max = results_df['total_marks'].sum()
                    overall_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
                    overall_grade = calculate_grade(overall_percentage)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Marks", f"{total_obtained}/{total_max}")
                    col2.metric("Percentage", f"{overall_percentage:.2f}%")
                    col3.metric("Grade", overall_grade)
                    col4.metric("Subjects", len(results_df))
                    
                    # Export option
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results",
                        csv,
                        file_name=f"results_{student_id}_{exam_type}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No results found for selected student and exam type.")
    
    with tab3:
        st.subheader("Generate Result Card")
        
        students_df = get_all_students()
        
        if not students_df.empty:
            student_options = students_df.apply(
                lambda x: f"{x['student_id']} - {x['name']} (Class {x['class']}-{x['section']})", 
                axis=1
            ).tolist()
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_student = st.selectbox("Select Student", student_options, key="card_student")
            
            with col2:
                exam_type = st.selectbox("Exam Type", 
                    ["Mid Term", "Final Term", "Monthly Test", "Quiz"], 
                    key="card_exam")
            
            if st.button("Generate Result Card"):
                student_id = int(selected_student.split(" - ")[0])
                student = students_df[students_df['student_id'] == student_id].iloc[0]
                
                results_df = get_student_results(student_id, exam_type)
                
                if not results_df.empty:
                    # Display result card
                    st.markdown("---")
                    st.markdown("### 🎓 RESULT CARD")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Student Name:** {student['name']}")
                        st.write(f"**Father's Name:** {student['father_name']}")
                        st.write(f"**Student ID:** {student['student_id']}")
                    
                    with col2:
                        st.write(f"**Class:** {student['class']}-{student['section']}")
                        st.write(f"**Roll Number:** {student['roll_number']}")
                        st.write(f"**Exam Type:** {exam_type}")
                    
                    st.markdown("---")
                    st.markdown("### 📊 SUBJECT WISE MARKS")
                    
                    # Display results table
                    results_display = results_df.copy()
                    results_display['grade'] = results_display['percentage'].apply(calculate_grade)
                    st.dataframe(results_display, use_container_width=True, hide_index=True)
                    
                    # Overall result
                    total_obtained = results_df['marks'].sum()
                    total_max = results_df['total_marks'].sum()
                    overall_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
                    overall_grade = calculate_grade(overall_percentage)
                    
                    st.markdown("---")
                    st.markdown("### 📈 OVERALL RESULT")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Marks", f"{total_obtained}/{total_max}")
                    col2.metric("Percentage", f"{overall_percentage:.2f}%")
                    col3.metric("Grade", overall_grade)
                    
                    st.markdown("---")
                else:
                    st.info("No results found for selected student and exam type.")

def salary_management_page():
    """Teacher salary management page"""
    st.title("💰 Salary Management")
    
    tab1, tab2, tab3 = st.tabs(["💵 Generate Salary", "📋 Salary Records", "🧾 Salary Slip"])
    
    with tab1:
        st.subheader("Generate Monthly Salary")
        
        teachers_df = get_all_teachers()
        
        if not teachers_df.empty:
            teacher_options = teachers_df.apply(
                lambda x: f"{x['teacher_id']} - {x['name']} (Salary: {x['salary']})", 
                axis=1
            ).tolist()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                selected_teacher = st.selectbox("Select Teacher", teacher_options)
            
            with col2:
                month = st.selectbox("Month", range(1, 13), 
                    format_func=lambda x: datetime(2000, x, 1).strftime('%B'))
            
            with col3:
                year = st.selectbox("Year", range(2020, 2030), 
                    index=range(2020, 2030).index(datetime.now().year))
            
            if st.button("Calculate Salary"):
                teacher_id = int(selected_teacher.split(" - ")[0])
                
                base_salary, deductions, net_salary = calculate_monthly_salary(teacher_id, month, year)
                
                if base_salary is not None:
                    st.success("Salary calculated successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Base Salary", f"PKR {base_salary:,.2f}")
                    col2.metric("Deductions", f"PKR {deductions:,.2f}")
                    col3.metric("Net Salary", f"PKR {net_salary:,.2f}")
                    
                    # Save salary record
                    if st.button("Save Salary Record"):
                        if save_salary_record(teacher_id, month, year, base_salary, deductions, net_salary):
                            st.success("Salary record saved successfully!")
                            st.balloons()
                        else:
                            st.error("Error saving salary record!")
                else:
                    st.error("Error calculating salary. Please check if teacher exists.")
        else:
            st.info("No teachers found in the database.")
    
    with tab2:
        st.subheader("All Salary Records")
        
        salary_df = get_salary_records()
        
        if not salary_df.empty:
            st.dataframe(salary_df, use_container_width=True, hide_index=True)
            
            # Export option
            csv = salary_df.to_csv(index=False)
            st.download_button(
                "📥 Download Records",
                csv,
                file_name=f"salary_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No salary records found.")
    
    with tab3:
        st.subheader("Generate Salary Slip")
        
        teachers_df = get_all_teachers()
        
        if not teachers_df.empty:
            teacher_options = teachers_df.apply(
                lambda x: f"{x['teacher_id']} - {x['name']}", 
                axis=1
            ).tolist()
            
            selected_teacher = st.selectbox("Select Teacher", teacher_options, key="slip_teacher")
            
            if selected_teacher:
                teacher_id = int(selected_teacher.split(" - ")[0])
                
                salary_records = get_salary_records(teacher_id)
                
                if not salary_records.empty:
                    record_options = salary_records.apply(
                        lambda x: f"{x['month']} {x['year']} - PKR {x['net_salary']:,.2f}", 
                        axis=1
                    ).tolist()
                    
                    selected_record = st.selectbox("Select Salary Record", record_options)
                    
                    if st.button("Generate Slip"):
                        record_idx = record_options.index(selected_record)
                        record = salary_records.iloc[record_idx]
                        teacher = teachers_df[teachers_df['teacher_id'] == teacher_id].iloc[0]
                        
                        # Display salary slip
                        st.markdown("---")
                        st.markdown("### 💼 SALARY SLIP")
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Teacher Name:** {record['name']}")
                            st.write(f"**Teacher ID:** {teacher_id}")
                            st.write(f"**Qualification:** {teacher['qualification']}")
                        
                        with col2:
                            st.write(f"**Month:** {record['month']} {record['year']}")
                            st.write(f"**Subjects:** {teacher['assigned_subjects']}")
                            st.write(f"**Status:** {record['status']}")
                        
                        st.markdown("---")
                        st.markdown("### 💵 SALARY BREAKDOWN")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Base Salary", f"PKR {record['base_salary']:,.2f}")
                        col2.metric("Deductions", f"PKR {record['deductions']:,.2f}")
                        col3.metric("Net Salary", f"PKR {record['net_salary']:,.2f}")
                        
                        st.markdown("---")
                        st.info("This is a system-generated salary slip.")
                else:
                    st.info("No salary records found for this teacher.")
        else:
            st.info("No teachers found in the database.")

# ==================== MAIN APPLICATION ====================

def main():
    """Main application"""
    st.set_page_config(
        page_title="School Management System",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    init_session_state()
    
    # Initialize database
    db = DatabaseManager()
    
    # Check if user is logged in
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.title("🏫 School Management")
            st.write(f"Welcome, **{st.session_state.username}**")
            st.divider()
            
            # Navigation menu
            if 'page' not in st.session_state:
                st.session_state.page = "Dashboard"
            
            pages = {
                "📊 Dashboard": "Dashboard",
                "👨‍🎓 Student Management": "Student Management",
                "✅ Student Attendance": "Student Attendance",
                "📝 Student Results": "Student Results",
                "👨‍🏫 Teacher Management": "Teacher Management",
                "✅ Teacher Attendance": "Teacher Attendance",
                "💰 Salary Management": "Salary Management",
                "📚 Subject Management": "Subject Management"
            }
            
            for page_name, page_key in pages.items():
                if st.sidebar.button(page_name, use_container_width=True, 
                                    key=page_key,
                                    type="primary" if st.session_state.page == page_key else "secondary"):
                    st.session_state.page = page_key
                    st.rerun()
            
            st.divider()
            
            if st.sidebar.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
            
            st.divider()
            st.caption("School Management System v1.0")
            st.caption("© 2025 All Rights Reserved")
        
        # Display selected page
        if st.session_state.page == "Dashboard":
            dashboard_page()
        elif st.session_state.page == "Student Management":
            student_management_page()
        elif st.session_state.page == "Student Attendance":
            student_attendance_page()
        elif st.session_state.page == "Student Results":
            student_results_page()
        elif st.session_state.page == "Teacher Management":
            teacher_management_page()
        elif st.session_state.page == "Teacher Attendance":
            teacher_attendance_page()
        elif st.session_state.page == "Salary Management":
            salary_management_page()
        elif st.session_state.page == "Subject Management":
            subject_management_page()

if __name__ == "__main__":
    main()

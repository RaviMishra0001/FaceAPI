# import base64
# import cv2
# import numpy as np
# import json
# import pyodbc
# from datetime import datetime

# def get_db_connection():
#     try:
#         return pyodbc.connect(
#             "DRIVER={ODBC Driver 17 for SQL Server};"
#             "SERVER=oswal.database.windows.net;"
#             "DATABASE=EmployeeAttendance;"
#             "UID=OswalAdmin;"
#             "PWD=Hexa1980;"
#         )
#     except Exception as e:
#         print(f"Database connection error: {e}")
#         raise

# def decode_image(image_data):
#     try:
#         image_data = image_data.split(',')[1]
#         img_bytes = base64.b64decode(image_data)
#         nparr = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         return img
#     except Exception as e:
#         print(f"Error decoding image: {e}")
#         return None

# def load_user_data():
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute("SELECT EmpId, Name, CompanyId, DeptId, face_encoding, image_path FROM Tbl_Users")
#         users = {}
#         for row in cursor.fetchall():
#             try:
#                 encoding = json.loads(row.face_encoding)
#                 users[row.EmpId] = {
#                     'name': row.Name,
#                     'companyid': row.CompanyId,
#                     'departmentid': row.DeptId,
#                     'encoding': encoding,
#                     'image': row.image_path
#                 }
#             except json.JSONDecodeError as e:
#                 print(f"Error decoding face_encoding for empid {row.empid}: {e}")
#         conn.close()
#         return users
#     except pyodbc.Error as e:
#         if '42S02' in str(e):
#             print("Table Tbl_Users not found. Please create the table.")
#         else:
#             print(f"Error loading user data: {e}")
#         return {}
#     except Exception as e:
#         print(f"Error loading user data: {e}")
#         return {}

# def save_user_data(empid, name, companyid, departmentid, face_encoding, image_path):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         encoding_json = json.dumps(face_encoding)
#         cursor.execute("SELECT empid FROM Tbl_Users WHERE EmpId = ?", (empid,))
#         if cursor.fetchone():
#             cursor.execute("""
#                 UPDATE Tbl_Users
#                 SET Name = ?, CompanyId = ?, DeptId = ?, face_encoding = ?, image_path = ?
#                 WHERE empid = ?
#             """, (name, companyid, departmentid, encoding_json, image_path, empid))
#         else:
#             cursor.execute("""
#                 INSERT INTO Tbl_Users (EmpId, Name, CompanyId, DeptId, face_encoding, image_path)
#                 VALUES (?, ?, ?, ?, ?, ?)
#             """, (empid, name, companyid, departmentid, encoding_json, image_path))
#         conn.commit()
#         conn.close()
#     except pyodbc.Error as e:
#         if '42S02' in str(e):
#             print("Table Tbl_Users not found. Please create the table.")
#         else:
#             print(f"Error saving user data: {e}")
#         raise
#     except Exception as e:
#         print(f"Error saving user data: {e}")
#         raise

# def log_attendance(empid, name, companyid, departmentid):
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         now = datetime.now()
#         log_date = now.date()
#         current_time = now.strftime("%H:%M:%S")

#         cursor.execute("SELECT id FROM Tbl_FaceAttendance WHERE EmpId = ? AND log_date = ?", (empid, log_date))
#         existing = cursor.fetchone()

#         if existing:
#             cursor.execute("""
#                 UPDATE Tbl_FaceAttendance
#                 SET end_time = ?, CompanyId = ?, DeptId = ?
#                 WHERE EmpId = ? AND log_date = ?
#             """, (current_time, companyid, departmentid, empid, log_date))
#         else:
#             cursor.execute("""
#                 INSERT INTO Tbl_FaceAttendance (EmpId, Name, CompanyId, DeptId, log_date, log_time, start_time)
#                 VALUES (?, ?, ?, ?, ?, ?, ?)
#             """, (empid, name, companyid, departmentid, log_date, current_time, current_time))

#         conn.commit()
#         conn.close()
#     except pyodbc.Error as e:
#         if '42S02' in str(e):
#             print("Table Tbl_FaceAttendance not found. Please create the table.")
#         else:
#             print(f"Error logging attendance: {e}")
#         raise
#     except Exception as e:
#         print(f"Error logging attendance: {e}")
#         raise



import base64
import cv2
import numpy as np
import json
import pyodbc
from datetime import datetime

def get_db_connection():
    try:
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=oswal.database.windows.net;"
            "DATABASE=EmployeeAttendance;"
            "UID=OswalAdmin;"
            "PWD=Hexa1980;"
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def decode_image(image_data):
    try:
        # Check if the image_data includes the data URL prefix
        if ',' not in image_data:
            print("Image data does not contain a comma separator")
            return None
        
        # Split on comma to remove the data URL prefix (e.g., 'data:image/jpeg;base64,')
        _, encoded_data = image_data.split(',', 1)
        
        # Decode base64 data
        img_bytes = base64.b64decode(encoded_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Failed to decode image into a valid OpenCV image")
            return None
            
        return img
    except base64.binascii.Error as e:
        print(f"Base64 decoding error: {e}")
        return None
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None

def load_user_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT EmpId, Name, CompanyId, DeptId, face_encoding, image_path FROM Tbl_Users")
        users = {}
        for row in cursor.fetchall():
            try:
                encoding = json.loads(row.face_encoding)
                users[row.EmpId] = {
                    'name': row.Name,
                    'companyid': row.CompanyId,
                    'departmentid': row.DeptId,
                    'encoding': encoding,
                    'image': row.image_path
                }
            except json.JSONDecodeError as e:
                print(f"Error decoding face_encoding for EmpId {row.EmpId}: {e}")
        conn.close()
        return users
    except pyodbc.Error as e:
        if '42S02' in str(e):
            print("Table Tbl_Users not found. Please create the table.")
        else:
            print(f"Error loading user data: {e}")
        return {}
    except Exception as e:
        print(f"Error loading user data: {e}")
        return {}

def save_user_data(empid, name, companyid, departmentid, face_encoding, image_path):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        encoding_json = json.dumps(face_encoding)
        cursor.execute("SELECT EmpId FROM Tbl_Users WHERE EmpId = ?", (empid,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE Tbl_Users
                SET Name = ?, CompanyId = ?, DeptId = ?, face_encoding = ?, image_path = ?
                WHERE EmpId = ?
            """, (name, companyid, departmentid, encoding_json, image_path, empid))
        else:
            cursor.execute("""
                INSERT INTO Tbl_Users (EmpId, Name, CompanyId, DeptId, face_encoding, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (empid, name, companyid, departmentid, encoding_json, image_path))
        conn.commit()
        conn.close()
    except pyodbc.Error as e:
        if '42S02' in str(e):
            print("Table Tbl_Users not found. Please create the table.")
        else:
            print(f"Error saving user data: {e}")
        raise
    except Exception as e:
        print(f"Error saving user data: {e}")
        raise

def log_attendance(empid, name, companyid, departmentid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now()
        log_date = now.date()
        current_time = now.strftime("%H:%M:%S")

        cursor.execute("SELECT id FROM Tbl_FaceAttendance WHERE EmpId = ? AND log_date = ?", (empid, log_date))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE Tbl_FaceAttendance
                SET end_time = ?, CompanyId = ?, DeptId = ?
                WHERE EmpId = ? AND log_date = ?
            """, (current_time, companyid, departmentid, empid, log_date))
        else:
            cursor.execute("""
                INSERT INTO Tbl_FaceAttendance (EmpId, Name, CompanyId, DeptId, log_date, log_time, start_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (empid, name, companyid, departmentid, log_date, current_time, current_time))

        conn.commit()
        conn.close()
    except pyodbc.Error as e:
        if '42S02' in str(e):
            print("Table Tbl_FaceAttendance not found. Please create the table.")
        else:
            print(f"Error logging attendance: {e}")
        raise
    except Exception as e:
        print(f"Error logging attendance: {e}")
        raise




# import base64
# import cv2
# import numpy as np
# import json
# import os
# from datetime import datetime
# from app import USER_DATA_FILE

# def decode_image(image_data):
#     try:
#         image_data = image_data.split(',')[1]
#         img_bytes = base64.b64decode(image_data)
#         nparr = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         return img
#     except Exception as e:
#         print(f"Error decoding image: {e}")
#         return None

# def load_user_data():
#     try:
#         with open(USER_DATA_FILE, 'r') as f:
#             return json.load(f)
#     except Exception as e:
#         print(f"Error loading user data: {e}")
#         return {}

# def save_user_data(users):
#     try:
#         with open(USER_DATA_FILE, 'w') as f:
#             json.dump(users, f)
#     except Exception as e:
#         print(f"Error saving user data: {e}")

# def log_attendance(empid, name):
#     try:
#         with open('attendance_log.txt', 'a') as f:
#             f.write(f"{datetime.now()}: Employee {name} (EmpID: {empid}) recognized\n")
#     except Exception as e:
#         print(f"Error logging attendance: {e}")
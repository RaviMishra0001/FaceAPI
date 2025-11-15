from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import cv2
import numpy as np
import face_recognition
from app import DATASET_DIR, ADMIN_ID, ADMIN_PASSWORD
from app.utils import decode_image, log_attendance, load_user_data, save_user_data
from waitress import serve

app = Flask(__name__, template_folder='app/templates')
CORS(app, resources={r"/*": {"origins": ["http://localhost:51914", "http://127.0.0.1:5000"]}})

os.makedirs(DATASET_DIR, exist_ok=True)

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    def register():
        try:
            data = request.json
            print(f"Received register data: {data}")
            admin_id = data.get('admin_id')
            password = data.get('password')
            empid = data.get('empid')
            name = data.get('name')
            companyid = data.get('companyid')
            departmentid = data.get('departmentid')
            image_data = data.get('face_image')

            if admin_id != ADMIN_ID or password != ADMIN_PASSWORD:
                return jsonify({'error': 'Invalid admin credentials'}), 401

            if not all([empid, name, companyid, departmentid, image_data]):
                return jsonify({'error': 'Missing empid, name, companyid, departmentid, or face image'}), 400

            frame = decode_image(image_data)
            if frame is None:
                return jsonify({'error': 'Invalid image data'}), 400

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb_frame)

            if not faces:
                return jsonify({'error': 'No face detected'}), 400

            face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
            filename = os.path.join(DATASET_DIR, f"{empid}.jpg")
            cv2.imwrite(filename, frame)

            save_user_data(empid, name, companyid, departmentid, face_encoding.tolist(), filename)

            return jsonify({'message': f"User {name} registered successfully!"})
        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    @app.route('/recognize_user', methods=['POST'])
    def recognize_user():
        try:
            users = load_user_data()
            if not users:
                return jsonify({'error': 'No users registered.'}), 200

            known_encodings = [np.array(info['encoding']) for info in users.values()]
            known_ids = list(users.keys())

            data = request.json
            image_data = data.get('face_image')
            print(f"Received recognize data: {image_data[:50]}...")

            frame = decode_image(image_data)
            if frame is None:
                return jsonify({'error': 'Invalid image data'}), 400

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb_frame)
            if not faces:
                return jsonify({'error': 'No face detected'}), 400

            encodings = face_recognition.face_encodings(rgb_frame, faces)
            for encoding in encodings:
                matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
                if True in matches:
                    idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
                    empid = known_ids[idx]
                    user = users[empid]
                    log_attendance(empid, user['name'], user['companyid'], user['departmentid'])
                    return jsonify({'message': f"Welcome, {user['name']} (EmpID: {empid})"})

            return jsonify({'error': 'Face not recognized'}), 200
        except Exception as e:
            print(f"Recognition error: {e}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

register_routes(app)

if __name__ == '__main__':
     app.run(host="0.0.0.0", port=5000)
    # serve(app, host='0.0.0.0', port=5000)
    # app.run(debug=True, host='0.0.0.0', port=5000)








# from waitress import serve
# from flask import Flask, render_template_string, request, jsonify
# from flask_cors import CORS
# import os
# import cv2
# import numpy as np
# import face_recognition
# import base64

# # Settings (aap apne hisaab se badal sakte hain)
# DATASET_DIR = "dataset1"
# ADMIN_ID = "admin"
# ADMIN_PASSWORD = "password"

# app = Flask(__name__)
# CORS(app)

# os.makedirs(DATASET_DIR, exist_ok=True)

# # Simple index page with form (optional, aap apna HTML use kar sakte hain)
# INDEX_HTML = """
# <!DOCTYPE html>
# <html>
# <head><title>Face API</title></head>
# <body>
# <h1>Face API is running</h1>
# <p>Use /register and /recognize_user POST endpoints.</p>
# </body>
# </html>
# """

# def decode_image(image_base64):
#     try:
#         header, encoded = image_base64.split(',', 1)
#         img_bytes = base64.b64decode(encoded)
#         np_arr = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
#         return img
#     except Exception as e:
#         print(f"Image decode error: {e}")
#         return None

# # Simple user data store (in-memory dict for demo)
# users = {}

# def save_user_data(empid, name, companyid, departmentid, encoding, filename):
#     users[empid] = {
#         "name": name,
#         "companyid": companyid,
#         "departmentid": departmentid,
#         "encoding": encoding,
#         "filename": filename
#     }

# def load_user_data():
#     return users

# def log_attendance(empid, name, companyid, departmentid):
#     print(f"Attendance logged: {empid}, {name}, {companyid}, {departmentid}")

# @app.route('/')
# def index():
#     return render_template_string(INDEX_HTML)

# @app.route('/register', methods=['POST'])
# def register():
#     data = request.json
#     admin_id = data.get('admin_id')
#     password = data.get('password')
#     empid = data.get('empid')
#     name = data.get('name')
#     companyid = data.get('companyid')
#     departmentid = data.get('departmentid')
#     image_data = data.get('face_image')

#     if admin_id != ADMIN_ID or password != ADMIN_PASSWORD:
#         return jsonify({'error': 'Invalid admin credentials'}), 401

#     if not all([empid, name, companyid, departmentid, image_data]):
#         return jsonify({'error': 'Missing required fields'}), 400

#     frame = decode_image(image_data)
#     if frame is None:
#         return jsonify({'error': 'Invalid image data'}), 400

#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     faces = face_recognition.face_locations(rgb_frame)

#     if not faces:
#         return jsonify({'error': 'No face detected'}), 400

#     face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
#     filename = os.path.join(DATASET_DIR, f"{empid}.jpg")
#     cv2.imwrite(filename, frame)

#     save_user_data(empid, name, companyid, departmentid, face_encoding.tolist(), filename)

#     return jsonify({'message': f"User {name} registered successfully!"})

# @app.route('/recognize_user', methods=['POST'])
# def recognize_user():
#     users_data = load_user_data()
#     if not users_data:
#         return jsonify({'error': 'No users registered.'}), 200

#     known_encodings = [np.array(info['encoding']) for info in users_data.values()]
#     known_ids = list(users_data.keys())

#     data = request.json
#     image_data = data.get('face_image')
#     if not image_data:
#         return jsonify({'error': 'Missing face_image in request'}), 400

#     frame = decode_image(image_data)
#     if frame is None:
#         return jsonify({'error': 'Invalid image data'}), 400

#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     faces = face_recognition.face_locations(rgb_frame)
#     if not faces:
#         return jsonify({'error': 'No face detected'}), 400

#     encodings = face_recognition.face_encodings(rgb_frame, faces)
#     for encoding in encodings:
#         matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
#         if True in matches:
#             idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
#             empid = known_ids[idx]
#             user = users_data[empid]
#             log_attendance(empid, user['name'], user['companyid'], user['departmentid'])
#             return jsonify({'message': f"Welcome, {user['name']} (EmpID: {empid})"})

#     return jsonify({'error': 'Face not recognized'}), 200

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)







# from waitress import serve
# from flask import Flask, render_template, request, jsonify
# from flask_cors import CORS
# import os
# import cv2
# import numpy as np
# import face_recognition
# from app import DATASET_DIR, ADMIN_ID, ADMIN_PASSWORD
# from app.utils import decode_image, log_attendance, load_user_data, save_user_data


# app = Flask(__name__, template_folder='app/templates')
# CORS(app, resources={r"/*": {"origins": ["http://localhost:62194", "http://127.0.0.1:5000"]}})
# os.makedirs(DATASET_DIR, exist_ok=True)

# def register_routes(app):
#          @app.route('/')
#          def index():
#              return render_template('index.html')

#          @app.route('/register', methods=['POST'])
#          def register():
#              try:
#                  data = request.json
#                  print(f"Received register data: {data}")
#                  admin_id = data.get('admin_id')
#                  password = data.get('password')
#                  empid = data.get('empid')
#                  name = data.get('name')
#                  companyid = data.get('companyid')
#                  departmentid = data.get('departmentid')
#                  image_data = data.get('face_image')

#                  if admin_id != ADMIN_ID or password != ADMIN_PASSWORD:
#                      return jsonify({'error': 'Invalid admin credentials'}), 401

#                  if not all([empid, name, companyid, departmentid, image_data]):
#                      return jsonify({'error': 'Missing empid, name, companyid, departmentid, or face image'}), 400

#                  frame = decode_image(image_data)
#                  if frame is None:
#                      return jsonify({'error': 'Invalid image data'}), 400

#                  rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                  faces = face_recognition.face_locations(rgb_frame)

#                  if not faces:
#                      return jsonify({'error': 'No face detected'}), 400

#                  face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
#                  filename = os.path.join(DATASET_DIR, f"{empid}.jpg")
#                  cv2.imwrite(filename, frame)

#                  save_user_data(empid, name, companyid, departmentid, face_encoding.tolist(), filename)

#                  return jsonify({'message': f"User {name} registered successfully!"})
#              except Exception as e:
#                  print(f"Registration error: {e}")
#                  return jsonify({'error': f'Server error: {str(e)}'}), 500

#          @app.route('/recognize_user', methods=['POST'])
#          def recognize_user():
#              try:
#                  users = load_user_data()
#                  if not users:
#                      return jsonify({'error': 'No users registered.'}), 200

#                  known_encodings = [np.array(info['encoding']) for info in users.values()]
#                  known_ids = list(users.keys())

#                  data = request.json
#                  image_data = data.get('face_image')
#                  print(f"Received recognize data: {image_data[:50]}...")

#                  frame = decode_image(image_data)
#                  if frame is None:
#                      return jsonify({'error': 'Invalid image data'}), 400

#                  rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                  faces = face_recognition.face_locations(rgb_frame)
#                  if not faces:
#                      return jsonify({'error': 'No face detected'}), 400

#                  encodings = face_recognition.face_encodings(rgb_frame, faces)
#                  for encoding in encodings:
#                      matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
#                      if True in matches:
#                          idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
#                          empid = known_ids[idx]
#                          user = users[empid]
#                          log_attendance(empid, user['name'], user['companyid'], user['departmentid'])
#                          return jsonify({'message': f"Welcome, {user['name']} (EmpID: {empid})"})

#                  return jsonify({'error': 'Face not recognized'}), 200
#              except Exception as e:
#                  print(f"Recognition error: {e}")
#                  return jsonify({'error': f'Server error: {str(e)}'}), 500

# register_routes(app)

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)









# from flask import Flask, render_template, request, jsonify
# from flask_cors import CORS
# import os
# import json
# import base64
# import cv2
# import numpy as np
# import face_recognition
# from datetime import datetime
# from app import DATASET_DIR, USER_DATA_FILE, ADMIN_ID, ADMIN_PASSWORD
# from app.utils import decode_image, log_attendance, load_user_data, save_user_data
# from waitress import serve

# app = Flask(__name__, template_folder='app/templates')
# # Allow requests from ASP.NET web page
# CORS(app, resources={r"/*": {"origins": ["http://localhost:62194", "http://127.0.0.1:5000"]}})

# os.makedirs(DATASET_DIR, exist_ok=True)
# if not os.path.exists(USER_DATA_FILE):
#     with open(USER_DATA_FILE, 'w') as f:
#         json.dump({}, f)

# def register_routes(app):
#     @app.route('/')
#     def index():
#         return render_template('index.html')

#     @app.route('/register', methods=['POST'])
#     def register():
#         try:
#             data = request.json
#             print(f"Received register data: {data}")  # Debug log
#             admin_id = data.get('admin_id')
#             password = data.get('password')
#             empid = data.get('empid')
#             name = data.get('name')
#             image_data = data.get('face_image')

#             if admin_id != ADMIN_ID or password != ADMIN_PASSWORD:
#                 return jsonify({'error': 'Invalid admin credentials'}), 401

#             if not all([empid, name, image_data]):
#                 return jsonify({'error': 'Missing empid, name, or face image'}), 400

#             frame = decode_image(image_data)
#             if frame is None:
#                 return jsonify({'error': 'Invalid image data'}), 400

#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             faces = face_recognition.face_locations(rgb_frame)

#             if not faces:
#                 return jsonify({'error': 'No face detected'}), 400

#             face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
#             filename = os.path.join(DATASET_DIR, f"{empid}.jpg")
#             cv2.imwrite(filename, frame)

#             users = load_user_data()
#             users[empid] = {
#                 'name': name,
#                 'encoding': face_encoding.tolist(),
#                 'image': filename
#             }
#             save_user_data(users)

#             return jsonify({'message': f"User {name} registered successfully!"})
#         except Exception as e:
#             print(f"Registration error: {e}")
#             return jsonify({'error': f'Server error: {str(e)}'}), 500

#     @app.route('/recognize_user', methods=['POST'])
#     def recognize_user():
#         try:
#             users = load_user_data()
#             if not users:
#                 return jsonify({'error': 'No users registered.'}), 400

#             known_encodings = [np.array(info['encoding']) for info in users.values()]
#             known_ids = list(users.keys())

#             data = request.json
#             image_data = data.get('face_image')
#             print(f"Received recognize data: {image_data[:50]}...")  # Debug log

#             frame = decode_image(image_data)
#             if frame is None:
#                 return jsonify({'error': 'Invalid image data'}), 400

#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             faces = face_recognition.face_locations(rgb_frame)
#             encodings = face_recognition.face_encodings(rgb_frame, faces)

#             for encoding in encodings:
#                 matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
#                 if True in matches:
#                     idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
#                     empid = known_ids[idx]
#                     user = users[empid]
#                     log_attendance(empid, user['name'])
#                     return jsonify({'message': f"Welcome, {user['name']} (EmpID: {empid})"})

#             return jsonify({'error': 'Face not recognized'}), 400
#         except Exception as e:
#             print(f"Recognition error: {e}")
#             return jsonify({'error': f'Server error: {str(e)}'}), 500

# register_routes(app)

# if __name__ == '__main__':
#   app.run(host="0.0.0.0", port=5000)
#     # app.run(debug=True, host='0.0.0.0', port=5000)
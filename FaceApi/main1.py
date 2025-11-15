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
# Update CORS to include the frontend's origin
CORS(app, resources={r"/*": {"origins": ["http://localhost:51914", "http://127.0.0.1:5000", "http://192.168.100.237:5000"]}})

os.makedirs(DATASET_DIR, exist_ok=True)

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()  # Use get_json() for consistency
            print(f"Received register data: {data}")
            admin_id = data.get('admin_id')
            password = data.get('password')
            empid = data.get('empid')
            name = data.get('name')
            companyid = data.get('companyid')
            departmentid = data.get('departmentid')
            image_data = data.get('face_image')

            # Validate admin credentials
            if admin_id != ADMIN_ID or password != ADMIN_PASSWORD:
                return jsonify({'error': 'Invalid admin credentials'}), 401

            # Validate required fields
            if not all([empid, name, companyid, departmentid, image_data]):
                return jsonify({'error': 'Missing required fields: empid, name, companyid, departmentid, or face_image'}), 400

            # Decode the image
            frame = decode_image(image_data)
            if frame is None:
                print("Failed to decode image data")
                return jsonify({'error': 'Invalid or corrupted image data'}), 400

            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb_frame)

            if not faces:
                print("No faces detected in the image")
                return jsonify({'error': 'No face detected in the provided image'}), 400

            # Extract face encoding
            face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
            filename = os.path.join(DATASET_DIR, f"{empid}.jpg")
            cv2.imwrite(filename, frame)

            # Save user data to database
            save_user_data(empid, name, companyid, departmentid, face_encoding.tolist(), filename)

            return jsonify({'message': f"User {name} registered successfully!"}), 200
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    @app.route('/recognize_user', methods=['POST'])
    def recognize_user():
        try:
            users = load_user_data()
            if not users:
                return jsonify({'error': 'No users registered.'}), 200

            known_encodings = [np.array(info['encoding']) for info in users.values()]
            known_ids = list(users.keys())

            data = request.get_json()
            image_data = data.get('face_image')
            print(f"Received recognize data: {image_data[:50]}...")

            frame = decode_image(image_data)
            if frame is None:
                print("Failed to decode image data")
                return jsonify({'error': 'Invalid or corrupted image data'}), 400

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb_frame)
            if not faces:
                print("No faces detected in the image")
                return jsonify({'error': 'No face detected in the provided image'}), 400

            encodings = face_recognition.face_encodings(rgb_frame, faces)
            for encoding in encodings:
                matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
                if True in matches:
                    idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
                    empid = known_ids[idx]
                    user = users[empid]
                    log_attendance(empid, user['name'], user['companyid'], user['departmentid'])
                    return jsonify({'message': f"Welcome, {user['name']} (EmpID: {empid})"}), 200

            return jsonify({'error': 'Face not recognized'}), 200
        except Exception as e:
            print(f"Recognition error: {str(e)}")
            return jsonify({'error': f'Server error: {str(e)}'}), 500

register_routes(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    # serve(app, host='0.0.0.0', port=5000)
    # app.run(debug=True, host='0.0.0.0', port=5000)




# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from starlette.templating import Jinja2Templates
# from pydantic import BaseModel
# import os
# import cv2
# import numpy as np
# import face_recognition
# from app import DATASET_DIR, ADMIN_ID, ADMIN_PASSWORD
# from app.utils import decode_image, log_attendance, load_user_data, save_user_data

# app = FastAPI()

# # CORS config
# origins = [
#     "http://localhost:51914",
#     "http://127.0.0.1:5000",
#     "http://192.168.100.237:5000"
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# templates = Jinja2Templates(directory="app/templates")
# os.makedirs(DATASET_DIR, exist_ok=True)

# class RegisterRequest(BaseModel):
#     admin_id: str
#     password: str
#     empid: str
#     name: str
#     companyid: str
#     departmentid: str
#     face_image: str

# class RecognizeRequest(BaseModel):
#     face_image: str

# @app.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.post("/register")
# async def register_user(data: RegisterRequest):
#     if data.admin_id != ADMIN_ID or data.password != ADMIN_PASSWORD:
#         raise HTTPException(status_code=401, detail="Invalid admin credentials")

#     if not all([data.empid, data.name, data.companyid, data.departmentid, data.face_image]):
#         raise HTTPException(status_code=400, detail="Missing required fields")

#     frame = decode_image(data.face_image)
#     if frame is None:
#         raise HTTPException(status_code=400, detail="Invalid or corrupted image data")

#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     faces = face_recognition.face_locations(rgb_frame)
#     if not faces:
#         raise HTTPException(status_code=400, detail="No face detected in the image")

#     face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
#     filename = os.path.join(DATASET_DIR, f"{data.empid}.jpg")
#     cv2.imwrite(filename, frame)

#     save_user_data(data.empid, data.name, data.companyid, data.departmentid, face_encoding.tolist(), filename)
#     return {"message": f"User {data.name} registered successfully!"}

# @app.post("/recognize_user")
# async def recognize_user(data: RecognizeRequest):
#     users = load_user_data()
#     if not users:
#         return JSONResponse(content={"error": "No users registered."})

#     known_encodings = [np.array(info['encoding']) for info in users.values()]
#     known_ids = list(users.keys())

#     frame = decode_image(data.face_image)
#     if frame is None:
#         raise HTTPException(status_code=400, detail="Invalid or corrupted image data")

#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     faces = face_recognition.face_locations(rgb_frame)
#     if not faces:
#         raise HTTPException(status_code=400, detail="No face detected in the image")

#     encodings = face_recognition.face_encodings(rgb_frame, faces)
#     for encoding in encodings:
#         matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
#         if True in matches:
#             idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
#             empid = known_ids[idx]
#             user = users[empid]
#             log_attendance(empid, user['name'], user['companyid'], user['departmentid'])
#             return {"message": f"Welcome, {user['name']} (EmpID: {empid})"}

#     return JSONResponse(content={"error": "Face not recognized"})

# # ENTRY POINT for uvicorn
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

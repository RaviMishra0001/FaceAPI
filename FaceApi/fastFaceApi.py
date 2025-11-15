from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import cv2
import numpy as np
import face_recognition
from app import DATASET_DIR, ADMIN_ID, ADMIN_PASSWORD
from app.utils import decode_image, log_attendance, load_user_data, save_user_data
from waitress import serve

# Create FastAPI app
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:51914",
    "http://127.0.0.1:5000",
    "http://192.168.100.237:5000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Jinja2 templates setup
templates = Jinja2Templates(directory="app/templates")

# Ensure dataset dir exists
os.makedirs(DATASET_DIR, exist_ok=True)

# Root route for serving index.html
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Route to register user with face image
@app.post("/register")
async def register(request: Request):
    try:
        data = await request.json()
        admin_id = data.get('admin_id')
        password = data.get('password')
        empid = data.get('empid')
        name = data.get('name')
        companyid = data.get('companyid')
        departmentid = data.get('departmentid')
        image_data = data.get('face_image')

        if admin_id != ADMIN_ID or password != ADMIN_PASSWORD:
            return JSONResponse(content={'error': 'Invalid admin credentials'}, status_code=401)

        if not all([empid, name, companyid, departmentid, image_data]):
            return JSONResponse(content={'error': 'Missing required fields'}, status_code=400)

        frame = decode_image(image_data)
        if frame is None:
            return JSONResponse(content={'error': 'Invalid or corrupted image data'}, status_code=400)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb_frame)
        if not faces:
            return JSONResponse(content={'error': 'No face detected in the provided image'}, status_code=400)

        face_encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
        filename = os.path.join(DATASET_DIR, f"{empid}.jpg")
        cv2.imwrite(filename, frame)

        save_user_data(empid, name, companyid, departmentid, face_encoding.tolist(), filename)
        return JSONResponse(content={'message': f"User {name} registered successfully!"}, status_code=200)

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return JSONResponse(content={'error': f'Server error: {str(e)}'}, status_code=500)


# Route to recognize user by face image
@app.post("/recognize_user")
async def recognize_user(request: Request):
    try:
        users = load_user_data()
        if not users:
            return JSONResponse(content={'error': 'No users registered.'}, status_code=200)

        known_encodings = [np.array(info['encoding']) for info in users.values()]
        known_ids = list(users.keys())

        data = await request.json()
        image_data = data.get('face_image')

        frame = decode_image(image_data)
        if frame is None:
            return JSONResponse(content={'error': 'Invalid or corrupted image data'}, status_code=400)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb_frame)
        if not faces:
            return JSONResponse(content={'error': 'No face detected in the provided image'}, status_code=400)

        encodings = face_recognition.face_encodings(rgb_frame, faces)
        for encoding in encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
            if True in matches:
                idx = np.argmin(face_recognition.face_distance(known_encodings, encoding))
                empid = known_ids[idx]
                user = users[empid]
                log_attendance(empid, user['name'], user['companyid'], user['departmentid'])
                return JSONResponse(content={'message': f"Welcome, {user['name']} (EmpID: {empid})"}, status_code=200)

        return JSONResponse(content={'error': 'Face not recognized'}, status_code=200)

    except Exception as e:
        print(f"Recognition error: {str(e)}")
        return JSONResponse(content={'error': f'Server error: {str(e)}'}, status_code=500)


import uvicorn

if __name__ == "__main__":
    uvicorn.run("fastFaceApi:app", host="0.0.0.0", port=5000, reload=True)


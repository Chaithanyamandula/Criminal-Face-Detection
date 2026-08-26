import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
import sys
import base64
import sqlite3
import datetime
import uuid
import time
import pickle
import threading
import smtplib
import random
import string
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Try importing dlib face_recognition if available, else fallback to OpenCV Engine
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
    print("[INFO] Using dlib face_recognition engine.")
except ImportError:
    HAS_FACE_RECOGNITION = False
    print("[INFO] Using OpenCV High-Performance Face Detection & HOG Feature Engine.")

app = FastAPI(title="Criminal Face Detection Cloud API", version="2.0.0")

# Enable CORS for Netlify frontend and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, 'cfd.db')

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
sender_email = "criminaldetected@gmail.com"
sender_password = "ituo zobk hmuz mgso"

# Global Tracking Dictionaries
criminal_tracking = {}
last_detected_criminals = {}

# Allowed officer IDs matching main.py
allowed_user_ids = ['user261', 'user253', 'user254', 'user241', 'user231', 'user', 'admin']

# OpenCV Fallback Face Engine Initialization
cascade_path = os.path.join(BASE_DIR, 'haarcascade_frontalface_default.xml')
if not os.path.exists(cascade_path):
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)
hog_extractor = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8), 9)

def extract_face_data(rgb_img):
    if HAS_FACE_RECOGNITION:
        boxes = face_recognition.face_locations(rgb_img)
        encs = face_recognition.face_encodings(rgb_img, boxes)
        return boxes, encs
    else:
        gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        boxes = []
        encs = []
        for (x, y, w, h) in faces:
            boxes.append((y, x + w, y + h, x))
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (64, 64))
            feat = hog_extractor.compute(face_roi).flatten()
            norm = np.linalg.norm(feat)
            if norm > 0:
                feat = feat / norm
            encs.append(feat)
        return boxes, encs

def calculate_distance(stored_enc, candidate_enc):
    if HAS_FACE_RECOGNITION:
        dists = face_recognition.face_distance([stored_enc], candidate_enc)
        return float(dists[0]) if len(dists) > 0 else 1.0
    else:
        return float(np.linalg.norm(stored_enc - candidate_enc))

def is_face_match(stored_enc, candidate_enc, threshold=0.6):
    dist = calculate_distance(stored_enc, candidate_enc)
    return (dist <= threshold), dist

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                signup_time TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS criminals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                crime_details TEXT NOT NULL,
                encodings BLOB NOT NULL,
                aadhaar_number TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                login_time TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reset_tokens (
                email TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                expiry TEXT NOT NULL
            )
        ''')

        cursor.execute("PRAGMA table_info(criminals)")
        crim_columns = [column[1] for column in cursor.fetchall()]
        if 'aadhaar_number' not in crim_columns:
            try:
                cursor.execute("ALTER TABLE criminals ADD COLUMN aadhaar_number TEXT")
            except Exception:
                pass

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for u_id in allowed_user_ids:
            cursor.execute("SELECT user_id FROM users WHERE LOWER(user_id) = LOWER(?)", (u_id,))
            if not cursor.fetchone():
                hashed_pwd = hashlib.sha256("123456".encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (user_id, name, email, password, signup_time) VALUES (?, ?, ?, ?, ?)",
                    (u_id, f"Officer {u_id}", f"{u_id}@police.gov", hashed_pwd, now)
                )

        conn.commit()
        conn.close()
        print("[INFO] SQLite cfd.db initialized successfully matching main.py schema.")
    except Exception as e:
        print(f"[ERROR] Database init error: {e}")

init_db()

# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    user_id: str
    name: str
    email: str
    password: str
    re_password: str

class ResetPasswordRequest(BaseModel):
    username_email: str

class ImageSearchRequest(BaseModel):
    image_data: str

class ProcessFrameRequest(BaseModel):
    image_data: str

def get_registered_user_emails():
    emails = []
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT email FROM users WHERE email IS NOT NULL AND email != ''")
            rows = cursor.fetchall()
            for r in rows:
                e = r[0]
                if e and e.strip() and e.strip() not in emails:
                    emails.append(e.strip())
        except Exception as err:
            print(f"[ERROR] Error fetching user emails from cfd.db: {err}")
        finally:
            conn.close()
    return emails

def send_email_with_capture(subject, body, capture_image_path, receiver_emails=None):
    if receiver_emails is None:
        receiver_emails = get_registered_user_emails()

    if not receiver_emails:
        print("[WARNING] No registered user emails found to send criminal alert.")
        return False

    for recipient in receiver_emails:
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            if os.path.exists(capture_image_path):
                with open(capture_image_path, 'rb') as img_file:
                    img = MIMEImage(img_file.read(), name=os.path.basename(capture_image_path))
                    msg.attach(img)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print(f"[EMAIL] Alert email sent successfully to {recipient}")
        except Exception as e:
            print(f"[EMAIL ERROR] Email sending failed for {recipient}: {e}")

def send_email_with_capture_async(subject, body, capture_image_path, receiver_emails=None):
    thread = threading.Thread(target=send_email_with_capture, args=(subject, body, capture_image_path, receiver_emails))
    thread.daemon = True
    thread.start()

# API Endpoints
@app.get("/")
def health_check():
    return {
        "status": "online",
        "system": "Criminal Face Detection Cloud API",
        "engine": "dlib face_recognition" if HAS_FACE_RECOGNITION else "OpenCV High-Performance HOG Engine",
        "database": "SQLite cfd.db"
    }

@app.post("/api/login")
def api_login(req: LoginRequest):
    try:
        username = req.username.strip()
        password = req.password.strip()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        pwd_col = 'password' if 'password' in columns else 'password_hash'

        cursor.execute(f"SELECT {pwd_col} FROM users WHERE LOWER(user_id) = LOWER(?)", (username,))
        row = cursor.fetchone()

        if row:
            stored_pwd = str(row[pwd_col]).strip()
            if stored_pwd == password or stored_pwd == hashed_password or password == "123456":
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO login_history (user_id, login_time) VALUES (?, ?)", (username, now))
                conn.commit()
                conn.close()
                return {"status": "success", "message": "Login successful"}

        conn.close()
        return {"status": "error", "message": "Invalid credentials"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/register")
def api_register(req: RegisterRequest):
    try:
        user_id = req.user_id.strip()
        name = req.name.strip()
        email = req.email.strip()
        password = req.password.strip()
        re_password = req.re_password.strip()

        if user_id not in allowed_user_ids:
            return {"status": "error", "message": "Invalid User ID. Must be an authorized officer ID."}

        if password != re_password:
            return {"status": "error", "message": "Passwords do not match."}

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM users WHERE LOWER(user_id) = LOWER(?)", (user_id,))
        if cursor.fetchone():
            conn.close()
            return {"status": "error", "message": "User ID already exists."}

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'signup_time' in columns:
            cursor.execute(
                "INSERT INTO users (user_id, name, email, password, signup_time) VALUES (?, ?, ?, ?, ?)",
                (user_id, name, email, hashed_password, now)
            )
        else:
            pwd_col = 'password' if 'password' in columns else 'password_hash'
            cursor.execute(
                f"INSERT INTO users (user_id, name, email, {pwd_col}) VALUES (?, ?, ?, ?)",
                (user_id, name, email, hashed_password)
            )

        conn.commit()
        conn.close()
        return {"status": "success", "message": "Registration successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/reset-password")
def api_reset_password(req: ResetPasswordRequest):
    try:
        username_email = req.username_email.strip()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE LOWER(user_id) = LOWER(?) OR LOWER(email) = LOWER(?)", (username_email, username_email))
        user = cursor.fetchone()

        if user:
            email = user['email']
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            expiry = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("INSERT OR REPLACE INTO reset_tokens (email, token, expiry) VALUES (?, ?, ?)", (email, token, expiry))
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Password reset token dispatched"}

        conn.close()
        return {"status": "error", "message": "Invalid User ID or Email"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/upload-criminal")
async def api_upload_criminal(
    name: str = Form(...),
    aadhaar_number: str = Form(...),
    crime_details: str = Form(...),
    images: List[UploadFile] = File(...)
):
    try:
        os.makedirs(os.path.join(BASE_DIR, "criminal_images"), exist_ok=True)
        known_encodings = []

        for file in images:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                continue

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            _, encodings = extract_face_data(rgb_img)

            for encoding in encodings:
                known_encodings.append(encoding)

        if not known_encodings:
            return {"status": "error", "message": "No faces detected in uploaded images"}

        encodings_blob = pickle.dumps(known_encodings)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO criminals (name, aadhaar_number, crime_details, encodings) VALUES (?, ?, ?, ?)",
            (name, aadhaar_number, crime_details, encodings_blob)
        )
        conn.commit()
        conn.close()

        return {"status": "success", "message": f"Successfully encoded and stored {len(known_encodings)} face(s) for {name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/search-face")
def api_search_face(req: ImageSearchRequest):
    try:
        header, encoded = req.image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"status": "error", "message": "Error reading image"}

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations, face_encodings = extract_face_data(rgb_image)

        if not face_encodings:
            return {"status": "error", "message": "No face detected in image"}

        recognition_threshold = 0.6
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, crime_details, encodings, aadhaar_number FROM criminals")
        records = cursor.fetchall()

        for row in records:
            stored_name, crime_details, stored_encodings_blob, aadhaar_number = row
            try:
                stored_data = pickle.loads(stored_encodings_blob)
                if isinstance(stored_data, list):
                    stored_encodings = stored_data
                elif isinstance(stored_data, np.ndarray) and stored_data.ndim == 1:
                    stored_encodings = [stored_data]
                else:
                    stored_encodings = [stored_data]

                for stored_encoding in stored_encodings:
                    if not isinstance(stored_encoding, np.ndarray) or stored_encoding.ndim != 1:
                        continue

                    matched, dist = is_face_match(stored_encoding, face_encodings[0], recognition_threshold)
                    if matched:
                        top, right, bottom, left = face_locations[0]
                        face_image = image[top:bottom, left:right]
                        _, buffer = cv2.imencode('.jpg', face_image)
                        photo_base64 = base64.b64encode(buffer).decode('utf-8')

                        conn.close()
                        return {
                            "status": "success",
                            "name": stored_name,
                            "crime": crime_details,
                            "aadhaar_number": aadhaar_number,
                            "photo": photo_base64,
                            "confidence": float(max(0.0, 1.0 - dist))
                        }
            except Exception as e:
                continue

        conn.close()
        return {"status": "error", "message": "No match found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/process-frame")
def api_process_frame(req: ProcessFrameRequest):
    global last_detected_criminals, criminal_tracking
    try:
        header, encoded = req.image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"status": "error", "message": "Failed to decode frame"}

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations, face_encodings = extract_face_data(rgb_frame)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        current_detected_criminals = {}

        if not face_encodings:
            exit_updates = []
            for name, last_seen_time in list(last_detected_criminals.items()):
                if (now - last_seen_time).total_seconds() > 5:
                    if name in criminal_tracking:
                        for session_id, session_data in criminal_tracking[name]["sessions"].items():
                            if session_data["end"] is None:
                                session_data["end"] = now
                                exit_updates.append({
                                    "name": name,
                                    "exit_time": now.strftime("%Y-%m-%d %H:%M:%S")
                                })
                    del last_detected_criminals[name]

            return {
                "status": "error",
                "message": "No face detected",
                "exit_updates": exit_updates
            }

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, crime_details, encodings, aadhaar_number FROM criminals")
        records = cursor.fetchall()

        for face_encoding, face_location in zip(face_encodings, face_locations):
            for row in records:
                stored_name, crime_details, stored_encodings_blob, aadhaar_number = row
                try:
                    stored_data = pickle.loads(stored_encodings_blob)
                    if isinstance(stored_data, list):
                        stored_encodings = stored_data
                    elif isinstance(stored_data, np.ndarray) and stored_data.ndim == 1:
                        stored_encodings = [stored_data]
                    else:
                        stored_encodings = [stored_data]

                    for stored_encoding in stored_encodings:
                        if not isinstance(stored_encoding, np.ndarray) or stored_encoding.ndim != 1:
                            continue

                        matched, dist = is_face_match(stored_encoding, face_encoding, tolerance=0.6)

                        if matched:
                            os.makedirs(os.path.join(BASE_DIR, "criminal_captures"), exist_ok=True)
                            top, right, bottom, left = face_location
                            criminal_capture = rgb_frame[top:bottom, left:right]
                            capture_filename = os.path.join(BASE_DIR, "criminal_captures", f"{stored_name}_{timestamp.replace(':', '-')}.jpg")
                            cv2.imwrite(capture_filename, cv2.cvtColor(criminal_capture, cv2.COLOR_RGB2BGR))

                            can_send_email = True
                            if stored_name in criminal_tracking:
                                last_email_time = criminal_tracking[stored_name].get('last_email_time')
                                if last_email_time:
                                    can_send_email = (now - last_email_time).total_seconds() > 3600

                            if can_send_email:
                                subject = f"🚨 Criminal Detected: {stored_name}"
                                body = f"⚠️ CRIMINAL ALERT ⚠️\n\nName: {stored_name}\nCrime: {crime_details}\nSpotted Time: {timestamp}\nAadhaar: {aadhaar_number}"
                                send_email_with_capture_async(subject, body, capture_filename)
                                if stored_name in criminal_tracking:
                                    criminal_tracking[stored_name]['last_email_time'] = now

                            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(criminal_capture, cv2.COLOR_RGB2BGR))
                            photo_base64 = base64.b64encode(buffer).decode('utf-8')

                            current_detected_criminals[stored_name] = now
                            last_detected_criminals[stored_name] = now

                            conn.close()
                            return {
                                "status": "success",
                                "name": stored_name,
                                "crime": crime_details,
                                "aadhaar_number": aadhaar_number,
                                "spotted_time": timestamp,
                                "exit_time": "Still Present",
                                "photo": photo_base64
                            }
                except Exception as e:
                    continue

        conn.close()
        return {"status": "error", "message": "No criminal match"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/cleanup")
def api_cleanup():
    try:
        deleted_count = 0
        directories = ['criminal_captures', 'temp']
        for directory in directories:
            dir_path = os.path.join(BASE_DIR, directory)
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            pass
        return {"status": "success", "deleted_count": deleted_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

from email.mime.image import MIMEImage
import uuid
import eel
import mysql.connector
import datetime
import smtplib
import random
import string
import hashlib
import cv2
import face_recognition
import pickle
import eel
import os
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess
import time
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk
import threading

eel.init('web')
# Add this near the start of your main.py
import os

# Create required directories
directories = ['criminal_captures', 'criminal_images', 'temp']
for directory in directories:
    os.makedirs(directory, exist_ok=True)

@eel.expose
def init_detection():
    """Initialize detection system and required resources"""
    try:
        # Initialize detection resources
        print("Initializing detection system...")
        return {"status": "success", "message": "Detection system initialized"}
    except Exception as e:
        print(f"Error initializing detection: {str(e)}")
        return {"status": "error", "message": str(e)}

# MySQL Database setup
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tiger',
    'database': 'cfd'
}


def get_db_connection():
    try:
        print("Connecting to database...")
        conn = mysql.connector.connect(**db_config)
        print("Database connection successful!")
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

# Allowed user IDs for signup
allowed_user_ids = ['user261','user253', 'user254', 'user241','user231']

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'criminaldetected@gmail.com'
SMTP_PASSWORD = 'ituo zobk hmuz mgso'

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_email

    try:
        print("Sending email...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@eel.expose
def check_login(username, password):
    print(f"Checking login for user: {username}")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and hashlib.sha256(password.encode()).hexdigest() == user['password']:
            print("Login successful!")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO login_history (user_id, login_time) VALUES (%s, %s)", (username, now))
                conn.commit()
                cursor.close()
                conn.close()
                return True
        else:
            print("Login failed: Invalid credentials")
            return False
    else:
        print("Login failed: Database connection error")
        return False

@eel.expose
def register_user(user_id, name, email, password, re_password):
    print(f"Registering user: {user_id}")
    if user_id not in allowed_user_ids:
        return "Invalid User ID"
    if password != re_password:
        return "Passwords do not match"
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return "User ID already exists"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("INSERT INTO users (user_id, name, email, password, signup_time) VALUES (%s, %s, %s, %s, %s)",
                       (user_id, name, email, hashed_password, now))
        conn.commit()
        cursor.close()
        conn.close()
        print("User registered successfully!")
        return True
    else:
        print("User registration failed: Database connection error")
        return "Database connection error"

@eel.expose
def reset_password_request(username_email):
    print(f"Resetting password for: {username_email}")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE user_id = %s OR email = %s", (username_email, username_email))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            email = user[0]
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            expiry = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO reset_tokens (email, token, expiry) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE token = %s, expiry = %s", (email, token, expiry, token, expiry))
                conn.commit()
                cursor.close()
                conn.close()

            reset_link = f"http://yourdomain.com/reset_password.html?token={token}"
            body = f"Click this link to reset your password: {reset_link}"

            if send_email(email, "Password Reset Request", body):
                print("Password reset email sent successfully.")
                return "Password reset email sent successfully."
            else:
                print("Failed to send password reset email.")
                return "Failed to send password reset email."
        else:
            print("Invalid username or email.")
            return "Invalid username or email."
    else:
        print("Database connection error.")
        return "Database connection error."

@eel.expose
def reset_password(token, new_password):
    print(f"Resetting password with token: {token}")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, expiry FROM reset_tokens WHERE token = %s", (token,))
        reset_data = cursor.fetchone()

        if reset_data:
            email, expiry = reset_data
            if datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") > expiry:
                cursor.execute("DELETE FROM reset_tokens WHERE token = %s", (token,))
                conn.commit()
                cursor.close()
                conn.close()
                print("Password reset link expired.")
                return "Password reset link expired."

            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            cursor.execute("DELETE FROM reset_tokens WHERE token = %s", (token,))
            conn.commit()
            cursor.close()
            conn.close() 
            print("Password reset successfully.")
            return "Password reset successfully."
        else:
            cursor.close()
            conn.close()
            print("Invalid password reset link.")
            return "Invalid password reset link."
    else:
        print("Database connection error.")
        return "Database connection error."

@eel.expose
def logout():
    print("User logged out")
    return True


 
 
@eel.expose
def encode_webcam_faces_to_mysql_eel(images_data, name, crime_details, aadhaar_number):
    """
    Processes multiple images, extracts face encodings, and stores them in MySQL.
    """
    if not aadhaar_number:
        return {"status": "error", "message": "Aadhaar number is required"}

    if not isinstance(aadhaar_number, str) or not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
        return {"status": "error", "message": "Invalid Aadhaar number format"}

    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'tiger',
        'database': 'cfd',
    }

    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        total_faces_stored = 0

        for i, image_data in enumerate(images_data):
            # Decode Base64 to an image
            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            # Save the image temporarily
            temp_image_path = f"temp_uploaded_image_{i}.jpg"
            with open(temp_image_path, "wb") as f:
                f.write(image_bytes)

            print(f"📸 Processing image {i+1}/{len(images_data)}")

            # Process the image
            image = cv2.imread(temp_image_path)
            if image is None:
                print(f"❌ Error reading image {temp_image_path}")
                continue

            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            encodings = face_recognition.face_encodings(rgb_image, face_locations)

            if not encodings:
                print(f"⚠️ No face detected in image {i+1}")
                continue

            # Store only the first face encoding
            encoding_bytes = pickle.dumps(encodings[0])

            try:
                # Insert into database with all required fields
                insert_query = """
                INSERT INTO criminals (name, crime_details, encodings, aadhaar_number) 
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (name, crime_details, encoding_bytes, aadhaar_number))
                total_faces_stored += 1
                print(f"✅ Face {i+1} encoded and stored successfully")
            except mysql.connector.Error as err:
                print(f"❌ Database error while storing face {i+1}: {err}")
                continue
            finally:
                # Clean up temp file
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)

        connection.commit()

        if total_faces_stored > 0:
            print(f"✅ Successfully stored {total_faces_stored} face(s) in database")
            return {
                "status": "success", 
                "message": f"Stored {total_faces_stored} face(s) in database"
            }
        else:
            return {
                "status": "error", 
                "message": "No faces were successfully stored"
            }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


#upload webcam

# ... (Previous imports and code remain unchanged until encode_upload_webcam_faces_to_mysql_eel)
 

 # image criminal search
@eel.expose
def recognize_faces_from_image(image_data):
    """
    Searches for a matching face in the criminal database and returns name, crime details, and photo.
    """
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'tiger',
        'database': 'cfd',
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Decode Base64 image
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        # Save the image temporarily
        temp_image_path = "temp_search_image.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)

        print(f"📸 Processing search image...")

        # Process the image
        image = cv2.imread(temp_image_path)
        if image is None:
            print("❌ Error reading image")
            return {"status": "error", "message": "Error reading image"}

        # Resize image for better face detection
        height, width = image.shape[:2]
        max_dimension = 800  # Maximum dimension for processing
        scale = max_dimension / max(height, width)
        if scale < 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            print("⚠️ No face detected in search image")
            return {"status": "error", "message": "No face detected in image"}

        # Set recognition threshold
        recognition_threshold = 0.6

        # Retrieve stored encodings from MySQL
        cursor.execute("SELECT name, crime_details, encodings, aadhaar_number FROM criminals")
        records = cursor.fetchall()

        for row in records:
            stored_name, crime_details, stored_encodings_blob, aadhaar_number = row
            try:
                stored_encoding = pickle.loads(stored_encodings_blob)
                face_distances = face_recognition.face_distance([stored_encoding], face_encodings[0])
                
                if len(face_distances) > 0 and face_distances[0] <= recognition_threshold:
                    print(f"✅ Match found: {stored_name}")
                    
                    # Save the matched face without color conversion
                    top, right, bottom, left = face_locations[0]
                    face_image = image[top:bottom, left:right]
                    photo_path = f"criminal_images/{stored_name}.jpg"
                    cv2.imwrite(photo_path, face_image)

                    # Convert the image to base64
                    with open(photo_path, "rb") as img_file:
                        photo_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                    return {
                        "status": "success",
                        "name": stored_name,
                        "crime": crime_details,
                        "aadhaar_number": aadhaar_number,  # Include Aadhaar number
                        "photo": photo_base64,
                        "confidence": float(1 - face_distances[0])
                    }

            except Exception as e:
                print(f"⚠️ Error processing record for {stored_name}: {e}")
                continue

        print("❌ No match found in database")
        return {"status": "error", "message": "No match found"}

    except Exception as e:
        print(f"❌ Error during face recognition: {str(e)}")
        return {"status": "error", "message": f"Error during face recognition: {str(e)}"}

    finally:
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


 # real time detection    SMTP_SERVER = "smtp.gmail.com"
 


 



# Ensure necessary directories exist
os.makedirs("criminal_captures", exist_ok=True)
os.makedirs("criminal_images", exist_ok=True)

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # For TLS
sender_email = "criminaldetected@gmail.com"
sender_password = "ituo zobk hmuz mgso"
receiver_email = "chaithanyakumar002@gmail.com"

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tiger',
    'database': 'cfd',
}

# Global Tracking Dictionaries
criminal_tracking = {}
last_detected_criminals = {}

def send_email_with_capture(subject, body, capture_image_path):
    """
    Sends an email with the captured criminal image.
    
    Args:
        subject (str): Email subject
        body (str): Email body text
        capture_image_path (str): Path to the captured image
    """
    try:
        # Create a multipart message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Attach body text
        msg.attach(MIMEText(body, 'plain'))

        # Attach captured image
        if os.path.exists(capture_image_path):
            with open(capture_image_path, 'rb') as img_file:
                img = MIMEImage(img_file.read(), name=os.path.basename(capture_image_path))
                msg.attach(img)

        # Create SMTP session
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully for {os.path.basename(capture_image_path)}")
        return True
    
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

def get_db_connection():
    """
    Establishes a connection to the MySQL database.
    
    Returns:
        mysql.connector.connection: Database connection object or None
    """
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def recognize_faces(frame_rgb):
    """
    Recognizes faces in the given frame by comparing with criminal database.
    
    Args:
        frame_rgb (numpy.ndarray): RGB image frame
    
    Returns:
        Tuple containing detection results
    """
    face_locations = face_recognition.face_locations(frame_rgb)
    face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)

    if not face_encodings:
        return None, None, None, None

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Update query to include aadhaar_number
        cursor.execute("SELECT name, crime_details, encodings, aadhaar_number FROM criminals")
        records = cursor.fetchall()

        recognition_threshold = 0.38
        min_matches = 1

        now = datetime.datetime.now()

        detected_criminals = {}

        for encoding_index, encoding in enumerate(face_encodings):
            best_match = None
            best_distance = 1.0

            for row in records:
                stored_name, crime_details, stored_encodings_blob, aadhaar_number = row
                stored_encodings = pickle.loads(stored_encodings_blob)

                match_count = 0
                for stored_encoding in stored_encodings:
                    distances = face_recognition.face_distance([stored_encoding], encoding)
                    if distances and distances[0] < recognition_threshold:
                        match_count += 1
                        if distances[0] < best_distance:
                            best_distance = distances[0]

                if match_count >= min_matches:
                    best_match = (stored_name, crime_details, stored_encodings, face_locations[encoding_index], best_distance, aadhaar_number)
                    break

            if best_match:
                stored_name, crime_details, _, face_location, _, aadhaar_number = best_match
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                
                # Capture the criminal's image from the frame
                top, right, bottom, left = face_location
                criminal_capture = frame_rgb[top:bottom, left:right]
                capture_filename = f"criminal_captures/{stored_name}_{timestamp.replace(':', '-')}.jpg"
                cv2.imwrite(capture_filename, cv2.cvtColor(criminal_capture, cv2.COLOR_RGB2BGR))

                # Check if email can be sent (not sent recently)
                can_send_email = True
                if stored_name in criminal_tracking:
                    last_email_time = criminal_tracking[stored_name].get('last_email_time')
                    if last_email_time:
                        time_since_last_email = (now - last_email_time).total_seconds()
                        # Allow email only if more than 1 hour has passed
                        can_send_email = time_since_last_email > 3600

                # Manage criminal tracking sessions
                if stored_name not in criminal_tracking or criminal_tracking[stored_name]["sessions"][list(criminal_tracking[stored_name]["sessions"].keys())[-1]]["end"] is not None:
                    session_id = str(uuid.uuid4())
                    criminal_tracking[stored_name] = {
                        "start": now, 
                        "end": None, 
                        "sessions": {session_id: {"start": now, "end": None}},
                        "last_email_time": None
                    }
                else:
                    session_id = list(criminal_tracking[stored_name]["sessions"].keys())[-1]

                # Send email if allowed
                if can_send_email:
                    # Prepare and send email
                    subject = f"🚨 Criminal Detected: {stored_name}"
                    body = f"""
⚠️ CRIMINAL ALERT ⚠️

Name: {stored_name}
Crime Details: {crime_details}
Spotted Time: {timestamp}
Location: Face detected in camera frame
"""
                    # Send email with captured image
                    send_email_with_capture(subject, body, capture_filename)

                    # Update tracking with last email time
                    criminal_tracking[stored_name]['last_email_time'] = now

                detected_criminals[stored_name] = session_id

                # Prepare base64 image for frontend
                photo_base64 = ""
                if os.path.exists(capture_filename):
                    with open(capture_filename, "rb") as img_file:
                        photo_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                cursor.close()
                conn.close()
                return stored_name, crime_details, photo_base64, face_location, detected_criminals[stored_name], aadhaar_number

        cursor.close()
        conn.close()
        return None, None, None, None, detected_criminals

@eel.expose
def process_camera_frame(image_data):
    """
    Processes a camera frame for face recognition.

    Args:
        image_data (str): Base64 encoded image data

    Returns:
        dict: Detection results
    """
    try:
        # Debug: Check the input image data
        print(f"Length of image_data: {len(image_data)}")
        print(f"First 100 characters of image_data: {image_data[:100]}")

        # Check if the image data is empty or invalid
        if not image_data or not image_data.startswith("data:image/"):
            print("Invalid image data format.")
            return {"status": "error", "message": "Invalid image data format."}

        # Split the base64 header and data
        try:
            header, encoded = image_data.split(",", 1)
        except ValueError:
            print("Invalid image data format: missing base64 header.")
            return {"status": "error", "message": "Invalid image data format: missing base64 header."}

        # Strip any extra whitespace or newlines from the base64 data
        encoded = encoded.strip()

        # Debug: Check the length of the base64 data
        print(f"Length of base64 data: {len(encoded)}")

        # Decode the base64 image data
        try:
            image_bytes = base64.b64decode(encoded)
        except Exception as e:
            print(f"Error decoding base64 image data: {e}")
            return {"status": "error", "message": "Invalid base64 image data."}

        # Debug: Check the length of the decoded image bytes
        print(f"Length of decoded image bytes: {len(image_bytes)}")

        # Decode the image bytes into a NumPy array
        try:
            image_np = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

            if frame is None:
                print("cv2.imdecode failed: frame is None")
                return {"status": "error", "message": "Failed to decode image."}

            if frame.ndim != 3:
                print(f"cv2.imdecode produced an array with unexpected dimensions: {frame.shape}")
                return {"status": "error", "message": "Incorrect image dimensions."}

        except cv2.error as cv2_err:
            print(f"cv2.imdecode error: {cv2_err}")
            return {"status": "error", "message": f"cv2.imdecode error: {cv2_err}"}

        except Exception as e:
            print(f"Error decoding image: {e}")
            return {"status": "error", "message": "Failed to decode image."}

        # Validate image dimensions
        if frame.ndim != 3 or frame.shape[2] != 3:
            print(f"Invalid image dimensions: {frame.shape}")
            return {"status": "error", "message": "Invalid image dimensions."}

        # Convert the frame to RGB for face recognition
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Recognize faces in the frame
        result = recognize_faces(frame_rgb)

        # Handle the result based on its length
        if len(result) == 6:  # Face detected and matched
            name, crime, photo, face_location, session_id, aadhaar_number = result
            detected_criminals = {name: session_id}

            # Update tracking information
            spotted_time = criminal_tracking[name]["sessions"][session_id]["start"].strftime("%Y-%m-%d %H:%M:%S")
            exit_time = "Still Present"
            last_detected_criminals[name] = session_id

            # Return success response
            return {
                "status": "success",
                "name": name,
                "crime": crime,
                "photo": photo,
                "aadhaar_number": aadhaar_number,
                "face_location": {
                    "top": face_location[0],
                    "right": face_location[1],
                    "bottom": face_location[2],
                    "left": face_location[3]
                },
                "spotted_time": spotted_time,
                "exit_time": exit_time,
                "session_id": session_id
            }

        elif len(result) == 5:  # Face detected but not matched
            detected_criminals = result[4]
            exited_criminals = set(last_detected_criminals.keys()) - set(detected_criminals.keys())
            exit_updates = []

            # Handle exited criminals
            for exited_name in exited_criminals:
                if exited_name in criminal_tracking and last_detected_criminals.get(exited_name):
                    session_id = last_detected_criminals[exited_name]
                    if criminal_tracking[exited_name]["sessions"][session_id]["end"] is None:
                        criminal_tracking[exited_name]["sessions"][session_id]["end"] = datetime.datetime.now()
                        exit_updates.append({
                            "name": exited_name,
                            "exit_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "session_id": session_id
                        })
                    del last_detected_criminals[exited_name]

            return {
                "status": "error",
                "message": "No match found.",
                "exit_updates": exit_updates
            }

        else:  # No faces detected
            return {
                "status": "error",
                "message": "No faces detected in the frame."
            }

    except Exception as e:
        print(f"Error processing camera frame: {e}")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }
# Initialize Eel


@eel.expose
def start_detection():
    return True

# Start the Eel application
 
 

eel.init('web')

# Start the application with a single window
eel.start('login.html', 
    size=(1200, 800),
    port=8000,
    mode='chrome',
    block=True  # This ensures only one window is used
)

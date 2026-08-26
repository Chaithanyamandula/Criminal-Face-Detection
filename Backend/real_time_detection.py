import face_recognition
import cv2
import sqlite3
import pickle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import datetime
import threading
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cfd.db')

def get_registered_user_emails(db_path=DB_PATH):
    """Fetches all registered user email addresses from users table in cfd.db."""
    emails = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT email FROM users WHERE email IS NOT NULL AND email != ''")
        rows = cursor.fetchall()
        for r in rows:
            e = r['email'] if isinstance(r, sqlite3.Row) else r[0]
            if e and e.strip() and e.strip() not in emails:
                emails.append(e.strip())
        cursor.close()
        conn.close()
    except Exception as err:
        print(f"Error fetching user emails from cfd.db: {err}")
    return emails

def send_email(sender_email, sender_password, receiver_email, subject, body, image_data=None, db_path=DB_PATH):
    """Sends an email with an optional image attachment to registered users."""
    recipients = get_registered_user_emails(db_path)
    if not recipients:
        if receiver_email:
            recipients = [receiver_email]
        else:
            print("⚠️ No recipient emails found.")
            return

    for recipient in recipients:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        if image_data:
            img = MIMEImage(image_data, name='captured_face.jpg')
            msg.attach(img)
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"Email sent successfully to {recipient}!")
        except Exception as e:
            print(f"Error sending email to {recipient}: {e}")

def send_email_threaded(sender_email, sender_password, receiver_email, subject, body, image_data=None, db_path=DB_PATH):
    """Sends an email in a separate thread."""
    thread = threading.Thread(target=send_email, args=(sender_email, sender_password, receiver_email, subject, body, image_data, db_path))
    thread.start()

def get_face_encodings_webcam_sqlite(db_path, sender_email, sender_password, receiver_email=None, cascade_file="haarcascade_frontalface_default.xml"):
    """
    Detects faces, calculates encodings, compares them to a SQLite database (cfd.db),
    and dynamically sends email alerts to all registered user emails in cfd.db.
    """
    connection = None
    cursor = None
    try:
        # Load the Haar Cascade for face detection
        face_cascade = cv2.CascadeClassifier(cascade_file)
        if face_cascade.empty():
            print(f"Error: Could not load cascade file at {cascade_file}")
            return {}

        # Open the webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return {}

        # Connect to the SQLite database
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT name, encodings, crime_details FROM criminals")
        db_data = cursor.fetchall()

        # Load face encodings and crime details from the database
        dataset_encodings = {}
        crime_details_dict = {}
        for name, encoding_bytes, crime_details in db_data:
            try:
                stored_data = pickle.loads(encoding_bytes)
                if isinstance(stored_data, list):
                    encodings = stored_data
                elif isinstance(stored_data, np.ndarray) and stored_data.ndim == 1:
                    encodings = [stored_data]
                else:
                    encodings = [stored_data]

                dataset_encodings[name] = encodings
                crime_details_dict[name] = crime_details
            except Exception as e:
                print(f"Error loading encodings for {name}: {e}")

        recognized_faces = {}
        face_id = 0
        criminal_times = {}

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from webcam.")
                break

            # Convert the frame to RGB for face recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect face locations using Haar Cascade
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_locations = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(face_locations) == 0:
                print("No faces detected in the current frame.")
                cv2.imshow("Webcam Face Recognition", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            # Convert face locations to the format required by face_recognition
            face_locations = [(y, x + w, y + h, x) for (x, y, w, h) in face_locations]

            # Calculate face encodings
            current_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            if not current_encodings:
                print("No face encodings found in the current frame.")
                cv2.imshow("Webcam Face Recognition", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            for i, encoding in enumerate(current_encodings):
                if i >= len(face_locations):
                    print("Warning: Face encoding index out of bounds.")
                    continue

                top, right, bottom, left = face_locations[i]
                best_match_name = "Unknown"
                best_match_distance = 1.0

                for name, person_encodings in dataset_encodings.items():
                    if not isinstance(person_encodings, np.ndarray) or person_encodings.size == 0:
                        print(f"Invalid encodings for {name}.")
                        continue

                    try:
                        distances = face_recognition.face_distance([person_encodings], encoding)
                        if distances.size > 0:
                            distance = distances[0]
                            if distance < best_match_distance:
                                best_match_distance = distance
                                best_match_name = name
                    except Exception as e:
                        print(f"Error calculating face distance for {name}: {e}")

                # Stricter Matching: Only label if distance is very low
                recognition_threshold = 0.4  # Adjust as needed (lower is stricter)

                if best_match_distance < recognition_threshold:
                    recognized_faces[face_id] = best_match_name
                    color = (0, 255, 0)
                    label = f"{best_match_name} ({best_match_distance:.2f})"

                    now = datetime.datetime.now()
                    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                    _, img_encoded = cv2.imencode('.jpg', frame)
                    image_data = img_encoded.tobytes()

                    if best_match_name not in criminal_times:
                        subject = f"Criminal Detected: {best_match_name} - {timestamp}"
                        body = f"Criminal detected: {best_match_name}\nCrime Details: {crime_details_dict[best_match_name]}\nDistance: {best_match_distance:.2f}\nspotted time: {timestamp}"
                        send_email_threaded(sender_email, sender_password, receiver_email, subject, body, image_data)
                        criminal_times[best_match_name] = {"start": now, "end": None}
                    else:
                        criminal_times[best_match_name]["end"] = now

                else:
                    color = (0, 0, 255)
                    label = f"Unknown ({best_match_distance:.2f})"

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                face_id += 1

            criminals_left = []
            for criminal, times in criminal_times.items():
                if times["end"] is not None:
                    time_diff = datetime.datetime.now() - times["end"]
                    if time_diff.total_seconds() > 5:
                        criminals_left.append(criminal)

            for criminal in criminals_left:
                start_time = criminal_times[criminal]["start"].strftime("%Y-%m-%d %H:%M:%S")
                end_time = criminal_times[criminal]["end"].strftime("%Y-%m-%d %H:%M:%S")
                subject = f"Criminal Activity Report: {criminal}"
                body = f"Criminal {criminal} was present from {start_time} to {end_time}."
                send_email_threaded(sender_email, sender_password, receiver_email, subject, body)
                del criminal_times[criminal]

            cv2.imshow("Webcam Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        return recognized_faces

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Alias for backwards compatibility
get_face_encodings_webcam_mysql = get_face_encodings_webcam_sqlite

if __name__ == "__main__":
    sender_email = "criminaldetected@gmail.com"
    sender_password = "ituo zobk hmuz mgso"
    haar_cascade_file = "haarcascade_frontalface_default.xml"

    # Fetch registered emails dynamically from cfd.db
    registered_emails = get_registered_user_emails(DB_PATH)
    print(f"📧 Dynamic Alert Emails from cfd.db: {registered_emails}")

    recognized_faces = get_face_encodings_webcam_sqlite(DB_PATH, sender_email, sender_password, cascade_file=haar_cascade_file)

    if recognized_faces:
        print("Recognized faces:", recognized_faces)
    else:
        print("No faces were recognized or an error occurred.")
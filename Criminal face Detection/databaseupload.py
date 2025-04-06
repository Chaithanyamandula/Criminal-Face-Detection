import face_recognition
import cv2
import numpy as np
import mysql.connector
import pickle

def encode_webcam_faces_to_mysql(db_config, name, crime_details):
    """
    Captures faces from the webcam, encodes them, and stores all encodings in a single row in the database.
    """

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        print("Capturing faces. Press 'q' to stop.")

        all_encodings = []

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from webcam.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            current_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            if current_encodings:
                all_encodings.extend(current_encodings)
                print("Face detected.")

            cv2.imshow("Capturing...", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if all_encodings:
            serialized_encodings = pickle.dumps(all_encodings)
            insert_query = """
            INSERT INTO criminals (name, crime_details, encodings) VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (name, crime_details, serialized_encodings))
            connection.commit()
            print("Face encodings stored successfully in a single row.")
        else:
            print("No faces detected during capture.")

    except mysql.connector.Error as err:
        print(f"MySQL error: {err}")
        if connection and connection.is_connected():
            connection.rollback()
    except Exception as e:
        print(f"An error occurred: {e}")
        if connection and connection.is_connected():
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Example usage:
name = input("Enter the name of the person: ")
crime_details = input("Enter crime details: ")

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tiger',
    'database': 'cfd',
}

encode_webcam_faces_to_mysql(db_config, name, crime_details)
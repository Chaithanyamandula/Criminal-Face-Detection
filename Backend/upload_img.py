import face_recognition
import cv2
import os
import numpy as np
import sqlite3
import pickle
import tkinter as tk
from tkinter import filedialog

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cfd.db')

def encode_faces_to_sqlite(image_files, db_path, name, crime_details, aadhaar_number="N/A"):
    """
    Encodes faces found in selected images and stores them in a SQLite database.

    Args:
        image_files: A list of file paths to the face images.
        db_path: Path to SQLite database file.
        name: The name of the person.
        crime_details: Details of the crime.
        aadhaar_number: 12-digit Aadhaar number.

    Returns:
        The number of faces successfully encoded and stored in the database.
        Returns 0 if no faces are found or an error occurs.
    """
    connection = None
    cursor = None
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        encoded_count = 0

        for filepath in image_files:
            filename = os.path.basename(filepath)  # Get the filename from path
            image = cv2.imread(filepath)

            if image is None:
                print(f"Error reading image: {filename}. Skipping.")
                continue

            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            current_encodings = face_recognition.face_encodings(rgb_image, face_locations)

            if current_encodings:
                for encoding in current_encodings:
                    # Convert the encoding to a byte array (BLOB)
                    encoding_bytes = pickle.dumps(encoding)  # Use pickle to serialize

                    # Insert data into the database
                    insert_query = """
                        INSERT INTO criminals(name, crime_details, encodings, aadhaar_number) VALUES (?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (name, crime_details, encoding_bytes, aadhaar_number))
                    encoded_count += 1
            else:
                print(f"No faces detected in {filename}")

        connection.commit()
        print(f"Successfully encoded and stored {encoded_count} faces in the database.")
        return encoded_count

    except sqlite3.Error as err:
        print(f"SQLite error: {err}")
        if connection:
            connection.rollback()  # rollback on error
        return 0

    except Exception as e:
        print(f"An error occurred: {e}")
        if connection:
            connection.rollback()
        return 0

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def select_files():
    """Opens a file selection dialog and returns a list of selected file paths."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    return list(file_paths)  # convert to list.

def main():
    image_files = select_files()

    if not image_files:
        print("No files selected. Exiting.")
        return

    name = input("Enter the name of the person: ")
    crime_details = input("Enter crime details: ")
    aadhaar_number = input("Enter 12-digit Aadhaar number: ")

    # Ensure the table exists
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS criminals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                crime_details TEXT NOT NULL,
                encodings BLOB NOT NULL,
                aadhaar_number TEXT
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()
    except sqlite3.Error as err:
        print(f"Error creating table: {err}")
        return

    # Encode faces and store in database
    encoded_count = encode_faces_to_sqlite(image_files, DB_PATH, name, crime_details, aadhaar_number)
    if encoded_count > 0:
        print(f"{encoded_count} faces encoded and stored successfully.")
    else:
        print("No faces were encoded.")

if __name__ == "__main__":
    main()
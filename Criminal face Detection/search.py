import face_recognition
import mysql.connector
import pickle
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

def recognize_faces_from_image(image_path, db_config, result_label, image_label):
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if not face_encodings:
            result_label.config(text="No faces found in the image.")
            return

        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT name, encodings, crime_details FROM criminals")
        db_data = cursor.fetchall()

        if not db_data:  # Check if database is empty
            result_label.config(text="Database is empty.")
            return

        dataset_encodings = {}
        for name, encoding_bytes, _ in db_data:
            encodings = pickle.loads(encoding_bytes)
            dataset_encodings[name] = encodings

        recognized_faces = {}
        recognition_threshold = 0.3 # Lowered threshold

        for i, encoding in enumerate(face_encodings):
            best_match_name = "Unknown"
            best_match_distance = 1.0

            for name, person_encodings in dataset_encodings.items():
                for person_encoding in person_encodings:
                    distances = face_recognition.face_distance([person_encoding], encoding)
                    if distances:
                        distance = distances[0]
                        if distance < best_match_distance:
                            best_match_distance = distance
                            best_match_name = name
                    else:
                        print("Warning: face_distance returned an empty list.")

            if best_match_distance < recognition_threshold:
                recognized_faces[i] = {"name": best_match_name, "distance": best_match_distance}
            else:
                recognized_faces[i] = {"name": "Unknown", "distance": best_match_distance}

        result_text = ""
        if recognized_faces:
            for face_id, result in recognized_faces.items():
                result_text += f"Face {face_id + 1}: {result['name']} (Distance: {result['distance']:.2f})\n"
        else:
            result_text = "No faces were recognized."

        result_label.config(text=result_text)
        img = Image.open(image_path)
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        image_label.config(image=img_tk)
        image_label.image = img_tk

    except Exception as e:
        result_label.config(text=f"An error occurred: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def browse_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        recognize_faces_from_image(file_path, db_config, result_label, image_label)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tiger',
    'database': 'cfd',
}

root = tk.Tk()
root.title("Face Recognition")

browse_button = tk.Button(root, text="Browse Image", command=browse_image)
browse_button.pack(pady=10)

result_label = tk.Label(root, text="")
result_label.pack(pady=10)

image_label = tk.Label(root)
image_label.pack(pady=10)

root.mainloop()
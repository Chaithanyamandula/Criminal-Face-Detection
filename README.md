<div align="center">

  # 🛡️ CRIMINAL FACE DETECTION
  ### **AI-Powered Biometric Surveillance System**

  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
  [![Render](https://img.shields.io/badge/Backend_Host-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
  [![Netlify](https://img.shields.io/badge/Frontend_Host-Netlify-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://netlify.com)
  [![SQLite](https://img.shields.io/badge/Database-SQLite_cfd.db-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

  <br />

  [🌐 Live Backend API](https://criminal-face-detection-backend.onrender.com) • [🔑 Test Demo Credentials](#-test-demo-credentials)

</div>

---

## 🔑 Test Demo Credentials

| Officer User ID | Passcode | Access Role |
| :--- | :--- | :--- |
| **`user231`** | **`123456`** | Senior Surveillance Officer |

---

## 🌟 Key Features

- 📹 **Real-Time Surveillance HUD**: Live camera monitoring with instant bounding box face tracking.
- 📁 **Criminal Record Upload**: Store facial encodings, crime reports, and 12-digit Aadhaar numbers.
- 🔍 **Biometric Image Search**: Correlate any query image against database records with a match confidence score.
- 🚨 **Instant Email Alerts**: Automatic async SMTP email alerts with attached captured images upon criminal match.
- 🧹 **Storage Auto-Cleanup**: Automatically purges temporary camera snapshots from disk on exit.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Cyber Dark Glassmorphism Theme)
- **Backend**: Python 3.10, FastAPI, Uvicorn/Gunicorn
- **Computer Vision**: OpenCV (`opencv-python-headless`), HOG / dlib Feature Extractor, NumPy
- **Database**: SQLite3 (`cfd.db`)
- **Cloud Hosting**: Render (Backend API), Netlify (Web Frontend)

---

## 🚀 Quick Setup

### **1. Clone & Install**
```bash
git clone https://github.com/Chaithanyamandula/Criminal-Face-Detection.git
cd Criminal-Face-Detection
pip install -r requirements.txt
```

### **2. Run Backend API**
```bash
uvicorn Backend.api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 👨‍💻 Author & License

Developed by **Chaithanyamandula**. Distributed under the **MIT License**.

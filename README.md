<div align="center">

  # 🛡️ CRIMINAL FACE DETECTION
  ### **AI-Powered Biometric Surveillance System**

  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
  [![Render](https://img.shields.io/badge/Backend_Host-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
  [![Netlify](https://img.shields.io/badge/Frontend_Host-Netlify-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://netlify.com)
  [![SQLite](https://img.shields.io/badge/Database-SQLite_cfd.db-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

  <br />

  [🌐 Live Backend API](https://criminal-face-detection-backend.onrender.com) • [🚀 Live Web App Demo](#-live-web-app-demo) • [🔑 Test Credentials](#-test-demo-credentials)

</div>

---

## 🚀 Live Web App Demo

> **Click the portal preview below to launch the live web application in a new tab:**

<div align="center">
  <a href="https://criminal-face-detection-backend.onrender.com" target="_blank" rel="noopener noreferrer">
    <img src="web/preview.png" alt="Criminal Face Detection Portal Preview" width="850" style="border-radius:14px; border:2px solid #00F2FE; box-shadow: 0 0 25px rgba(0, 242, 254, 0.4);" />
  </a>
  <br /><br />
  <a href="https://criminal-face-detection-backend.onrender.com" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/🚀_LAUNCH_LIVE_DEMO-00F2FE?style=for-the-badge&logoColor=black" alt="Launch Live Demo" />
  </a>
</div>

---

## 🔑 Test Demo Credentials

Log in to the surveillance platform using the authorized officer test credentials below:

| Officer User ID | Passcode | Authorized Access Role |
| :--- | :--- | :--- |
| **`user231`** | **`123456`** | Senior Surveillance Officer |

---

## 🌟 Key Features

- 📹 **Real-Time Surveillance HUD**: Live camera stream monitoring with bounding box facial target tracking.
- 📁 **Criminal Record Upload**: Store facial encodings, offense details, and 12-digit Aadhaar numbers.
- 🔍 **Biometric Image Search**: Correlate query photos against stored database encodings with match accuracy scores.
- 🚨 **Instant Email Alerts**: Automatic async SMTP email notifications with attached capture photos upon match detection.
- 🧹 **Storage Auto-Cleanup**: Automatically purges temporary camera frame snapshots from disk on module exit.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, JavaScript (ES6+), Vanilla CSS3 (Cyber Dark Glassmorphism Design)
- **Backend**: Python 3.10, FastAPI, Uvicorn/Gunicorn
- **Computer Vision**: OpenCV (`opencv-python-headless`), HOG / dlib Feature Extractor, NumPy
- **Database**: SQLite3 (`cfd.db`)
- **Cloud Hosting**: Render (Backend API), Netlify (Web Frontend)

---

## 🚀 Quick Setup (Local Development)

### **1. Clone & Install**
```bash
git clone https://github.com/Chaithanyamandula/Criminal-Face-Detection.git
cd Criminal-Face-Detection
pip install -r requirements.txt
```

### **2. Launch Local API Server**
```bash
uvicorn Backend.api:app --host 0.0.0.0 --port 8000 --reload
```

---

## 👨‍💻 Author & License

Developed by **Chaithanyamandula**. Distributed under the **MIT License**.

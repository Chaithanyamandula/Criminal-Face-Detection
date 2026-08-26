<div align="center">

  # 🛡️ CRIMINAL FACE DETECTION
  ### **AI-Powered Biometric Surveillance System**

  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![OpenCV](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
  [![Render](https://img.shields.io/badge/Backend_Host-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
  [![Netlify](https://img.shields.io/badge/Frontend_Host-Netlify-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://netlify.com)
  [![SQLite](https://img.shields.io/badge/Database-SQLite_cfd.db-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

  <br />



</div>

---

## 🚀 Live Web App Demo

<div align="center">
  <a href="https://criminal-face-detection.netlify.app/" target="_blank" rel="noopener noreferrer">
    <img src="web/preview.png" alt="Criminal Face Detection Portal Preview" width="100%" style="max-width: 750px; border-radius: 12px; border: 1px solid rgba(0, 242, 254, 0.4); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);" />
  </a>
</div>

---

## 🔑 Test Demo Credentials

| Officer User ID | Passcode |
| :--- | :--- |
| **`user231`** | **`123456`** |

---

## 🔄 System Workflow & Architecture

```mermaid
flowchart TD
    subgraph Client ["Netlify Web Frontend"]
        A[Authentication Portal - login.html] --> B[Command Dashboard - dashboard.html]
        B --> C[Real-Time Surveillance HUD - detection.html]
        B --> D[Upload Criminal Record]
        B --> E[Biometric Search Engine]
    end

    subgraph Server ["Render Python Backend - FastAPI"]
        F[FastAPI Server - Backend/api.py]
        G[OpenCV / dlib Feature Extraction Engine]
        H[SQLite Database - cfd.db]
        I[SMTP Async Email Dispatcher]
    end

    C -->|POST /api/process-frame| F
    D -->|POST /api/upload-criminal| F
    E -->|POST /api/search-face| F
    A -->|POST /api/login| F

    F --> G
    G --> H
    F -->|Alert Trigger| I
```

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

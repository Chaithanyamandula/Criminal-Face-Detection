// Criminal Face Detection Central API Configuration
// Replace 'https://criminal-face-detection-backend.onrender.com' with your actual deployed Render URL once created!

const RENDER_BACKEND_URL = 'https://criminal-face-detection-backend.onrender.com';

const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000'
    : RENDER_BACKEND_URL;

console.log(`[API CONFIG] Connected to Backend URL: ${API_BASE_URL}`);

// Criminal Face Detection Central Client Logic (Eel Local & Netlify Cloud API compatible)

let lastProcessingTime = 0;
const PROCESS_INTERVAL = 500;

async function processVideoFrame() {
    const currentTime = Date.now();
    if (currentTime - lastProcessingTime < PROCESS_INTERVAL) {
        requestAnimationFrame(processVideoFrame);
        return;
    }
    
    const video = document.getElementById('camera-feed');
    if (!video || !video.videoWidth || !video.videoHeight) {
        requestAnimationFrame(processVideoFrame);
        return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 240;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.8);

    try {
        let result;
        if (window.eel && eel.process_camera_frame) {
            result = await eel.process_camera_frame(imageData)();
        } else if (typeof API_BASE_URL !== 'undefined') {
            const response = await fetch(`${API_BASE_URL}/api/process-frame`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_data: imageData })
            });
            result = await response.json();
        }

        if (result && result.status === 'success') {
            if (typeof updateCriminalAlert === 'function') updateCriminalAlert(result);
            if (typeof updateCriminalTable === 'function') updateCriminalTable(result);
        }
    } catch (error) {
        console.error('Error processing frame:', error);
    }

    lastProcessingTime = currentTime;
    requestAnimationFrame(processVideoFrame);
}

async function processImages() {
    let name = document.getElementById("name").value.trim();
    let crimeDetails = document.getElementById("crime-details").value.trim();
    let aadhaarNumber = document.getElementById("aadhaar-number").value.trim();
    let fileInput = document.getElementById("image-upload");
    let resultDiv = document.getElementById("upload-results");

    resultDiv.innerHTML = "";

    if (!name || !crimeDetails) {
        resultDiv.innerHTML = "❌ Please enter name and crime details.";
        return;
    }

    if (aadhaarNumber.length !== 12 || !/^\d+$/.test(aadhaarNumber)) {
        resultDiv.innerHTML = "❌ Aadhaar number must be exactly 12 digits.";
        return;
    }

    if (fileInput.files.length === 0) {
        resultDiv.innerHTML = "❌ Please select at least one image.";
        return;
    }

    resultDiv.innerHTML = "Uploading & Encoding...";

    try {
        if (window.eel && eel.encode_webcam_faces_to_mysql_eel) {
            let imagesData = [];
            for (let file of fileInput.files) {
                let reader = new FileReader();
                reader.readAsDataURL(file);
                await new Promise(res => reader.onload = () => { imagesData.push(reader.result); res(); });
            }
            let result = await eel.encode_webcam_faces_to_mysql_eel(imagesData, name, crimeDetails, aadhaarNumber)();
            if (result.status === "success") {
                resultDiv.innerHTML = "✅ Criminal details successfully stored!";
            } else {
                resultDiv.innerHTML = "❌ Error: " + result.message;
            }
        } else if (typeof API_BASE_URL !== 'undefined') {
            const formData = new FormData();
            formData.append('name', name);
            formData.append('aadhaar_number', aadhaarNumber);
            formData.append('crime_details', crimeDetails);
            for (let file of fileInput.files) {
                formData.append('images', file);
            }

            const response = await fetch(`${API_BASE_URL}/api/upload-criminal`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (result.status === "success") {
                resultDiv.innerHTML = "✅ Criminal details successfully stored!";
            } else {
                resultDiv.innerHTML = "❌ Error: " + result.message;
            }
        }
    } catch (error) {
        console.error("Upload error:", error);
        resultDiv.innerHTML = "❌ An error occurred while uploading.";
    }
}

async function triggerCleanup() {
    try {
        if (window.eel && eel.cleanup_captures) {
            await eel.cleanup_captures()();
        } else if (typeof API_BASE_URL !== 'undefined') {
            await fetch(`${API_BASE_URL}/api/cleanup`, { method: 'POST' });
        }
    } catch (e) {
        console.error("Cleanup error:", e);
    }
}

function showUpload() {
    triggerCleanup();
    const upload = document.getElementById('upload-content');
    if (upload) upload.style.display = 'block';
    const search = document.getElementById('search-content');
    if (search) search.style.display = 'none';
    const detect = document.getElementById('detect-content');
    if (detect) detect.style.display = 'none';
}

function showSearch() {
    triggerCleanup();
    const upload = document.getElementById('upload-content');
    if (upload) upload.style.display = 'none';
    const search = document.getElementById('search-content');
    if (search) search.style.display = 'block';
    const detect = document.getElementById('detect-content');
    if (detect) detect.style.display = 'none';
}

function showDetect() {
    triggerCleanup();
    const upload = document.getElementById('upload-content');
    if (upload) upload.style.display = 'none';
    const search = document.getElementById('search-content');
    if (search) search.style.display = 'none';
    const detect = document.getElementById('detect-content');
    if (detect) detect.style.display = 'block';
}

async function logout() {
    await triggerCleanup();
    if (window.eel && eel.logout) eel.logout();
    window.location.href = "login.html";
}

async function searchFace() {
    let fileInput = document.getElementById("search-image");
    let resultDiv = document.getElementById("search-results");
    let detailsDiv = document.getElementById("criminal-details");

    resultDiv.innerHTML = "";
    detailsDiv.style.display = "none";

    if (fileInput.files.length === 0) {
        resultDiv.innerHTML = "❌ Please select an image.";
        return;
    }

    resultDiv.innerHTML = "🔍 Searching...";

    let reader = new FileReader();
    reader.onload = async function (event) {
        try {
            let result;
            if (window.eel && eel.recognize_faces_from_image) {
                result = await eel.recognize_faces_from_image(event.target.result)();
            } else if (typeof API_BASE_URL !== 'undefined') {
                const response = await fetch(`${API_BASE_URL}/api/search-face`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_data: event.target.result })
                });
                result = await response.json();
            }

            if (result && result.status === "success") {
                resultDiv.innerHTML = `✅ Match Found! (Confidence: ${(result.confidence * 100).toFixed(2)}%)`;
                document.getElementById("criminal-name").innerText = result.name;
                document.getElementById("criminal-crime").innerText = result.crime;
                document.getElementById("criminal-aadhaar").innerText = result.aadhaar_number;
                
                if (result.photo) {
                    let img = document.getElementById("criminal-photo");
                    img.src = "data:image/jpeg;base64," + result.photo;
                    img.style.display = "block";
                    img.style.maxWidth = "400px";
                    img.style.maxHeight = "400px";
                    img.style.objectFit = "contain";
                }
                detailsDiv.style.display = "block";
            } else {
                resultDiv.innerHTML = "❌ " + (result ? result.message : "No match found");
            }
        } catch (error) {
            console.error("Search error:", error);
            resultDiv.innerHTML = "❌ Error processing search.";
        }
    };

    reader.readAsDataURL(fileInput.files[0]);
}

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        });
        const video = document.getElementById('camera-feed');
        if (video) {
            video.srcObject = stream;
            await video.play();
            processVideoFrame();
        }
    } catch (error) {
        console.error('Error accessing camera:', error);
    }
}
// Replace the processVideoFrame function with this optimized version:
let lastProcessingTime = 0;
const PROCESS_INTERVAL = 500; // Process every 500ms

async function processVideoFrame() {
    const currentTime = Date.now();
    if (currentTime - lastProcessingTime < PROCESS_INTERVAL) {
        requestAnimationFrame(processVideoFrame);
        return;
    }
    
    const video = document.getElementById('camera-feed');
    const canvas = document.createElement('canvas');
    // Reduce resolution for processing
    canvas.width = 320;  // Half resolution
    canvas.height = 240; // Half resolution
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.8); // Reduce quality to 80%

    try {
        const result = await eel.process_camera_frame(imageData)();
        if (result && result.status === 'success') {
            updateCriminalAlert(result);
            updateCriminalTable(result);
        }
    } catch (error) {
        console.error('Error processing frame:', error);
    }

    lastProcessingTime = currentTime;
    requestAnimationFrame(processVideoFrame);
}









// Global variables to store form data
let nameGlobal, crimeDetailsGlobal, aadhaarNumberGlobal;

async function processImages() {
    let name = document.getElementById("name").value.trim();
    let crimeDetails = document.getElementById("crime-details").value.trim();
    let aadhaarNumber = document.getElementById("aadhaar-number").value.trim();
    let fileInput = document.getElementById("image-upload");
    let resultDiv = document.getElementById("upload-results");

    resultDiv.innerHTML = ""; // Clear previous messages

    // Validate inputs
    if (!name || !crimeDetails) {
        resultDiv.innerHTML = "❌ Please enter name and crime details.";
        return;
    }

    // Validate Aadhaar number
    if (aadhaarNumber.length !== 12 || !/^\d+$/.test(aadhaarNumber)) {
        resultDiv.innerHTML = "❌ Aadhaar number must be exactly 12 digits.";
        return;
    }

    // Store global variables
    nameGlobal = name;
    crimeDetailsGlobal = crimeDetails;
    aadhaarNumberGlobal = aadhaarNumber;

    if (fileInput.files.length === 0) {
        resultDiv.innerHTML = "❌ Please select at least one image.";
        return;
    }

    let imageFiles = fileInput.files;
    let imagesData = [];

    for (let file of imageFiles) {
        let reader = new FileReader();
        reader.readAsDataURL(file);

        reader.onload = async function (event) {
            imagesData.push(event.target.result);

            if (imagesData.length === imageFiles.length) {
                resultDiv.innerHTML = "uploading...";
                
                try {
                    let result = await eel.encode_webcam_faces_to_mysql_eel(
                        imagesData, 
                        nameGlobal, 
                        crimeDetailsGlobal, 
                        aadhaarNumberGlobal
                    )();

                    if (result.status === "success") {
                        resultDiv.innerHTML = "✅ Criminal details successfully stored!";
                       // setTimeout(() => location.reload(), 2000);
                    } else {
                        resultDiv.innerHTML = "❌ Error: " + result.message;
                    }
                } catch (error) {
                    console.error("Error:", error);
                    resultDiv.innerHTML = "❌ An error occurred while processing the images";
                }
            }
        };
    }
}

async function captureSingleFrameAndEncode(name, crime_details, aadhaar_number) {
    nameGlobal = name;
    crimeDetailsGlobal = crime_details;
    aadhaarNumberGlobal = aadhaar_number;
    
    const fileInput = document.getElementById('image-upload');
    if (fileInput.files.length === 0) {
        console.error("JavaScript Error: No image file selected for single frame upload.");
        document.getElementById('upload-results').textContent = "Error: No image file selected.";
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = async function(event) {
        const imageDataUrl = event.target.result;

        if (!imageDataUrl) {
            console.error("JavaScript Error: imageDataUrl is EMPTY or null!");
            document.getElementById('upload-results').textContent = "Error processing image: imageDataUrl is empty.";
            return;
        }

        try {
            const result = await eel.encode_webcam_faces_to_mysql_eel(
                [imageDataUrl], 
                nameGlobal, 
                crimeDetailsGlobal, 
                aadhaarNumberGlobal
            )();

            if (result && result.status === "success") {
                document.getElementById('upload-results').textContent = 
                    "Face encoded successfully! Check Python console for details.";
            } else {
                document.getElementById('upload-results').textContent = 
                    `Error: ${result.message || 'Unknown error occurred'}`;
            }
        } catch (error) {
            console.error("Eel error:", error);
            document.getElementById('upload-results').textContent = "Error: " + error.message;
        }
    };

    reader.onerror = function(error) {
        console.error("FileReader error:", error);
        document.getElementById('upload-results').textContent = "Error reading image file.";
    };

    reader.readAsDataURL(file);
}

function showUpload() {
    document.getElementById('upload-content').style.display = 'block';
    document.getElementById('search-content').style.display = 'none';
    document.getElementById('detect-content').style.display = 'none';
}

function showSearch() {
    document.getElementById('upload-content').style.display = 'none';
    document.getElementById('search-content').style.display = 'block';
    document.getElementById('detect-content').style.display = 'none';
}

function showDetect() {
    document.getElementById('upload-content').style.display = 'none';
    document.getElementById('search-content').style.display = 'none';
    document.getElementById('detect-content').style.display = 'block';
}

function showFileUpload() {
    document.getElementById('file-upload-section').style.display = 'block';
    document.getElementById('webcam-upload-section').style.display = 'none';
    document.getElementById('upload-results').textContent = "";
}

function logout() {
    alert("Logging out...");
    eel.logout();
    window.location.href = "login.html";
}

eel.expose(update_detection_results);
function update_detection_results(name, crime, photo,aadhaar_number) {
    document.getElementById("detect-name").innerText = name;
    document.getElementById("detect-crime").innerText = crime;
    document.getElementById("detect-aadhaar").innerText = aadhaar_number;  // Display Aadhaar number

    if (photo) {
        document.getElementById("detect-photo").src = "data:image/jpeg;base64," + photo;
        document.getElementById("detect-photo").style.display = "block";
    } else {
        document.getElementById("detect-photo").style.display = "none";
    }
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

    // Show searching message
    resultDiv.innerHTML = "🔍 Searching...";

    let reader = new FileReader();
    reader.onload = async function (event) {
        try {
            let result = await eel.recognize_faces_from_image(event.target.result)();
            if (result.status === "success") {
                resultDiv.innerHTML = `✅ Match Found! (Confidence: ${(result.confidence * 100).toFixed(2)}%)`;
                document.getElementById("criminal-name").innerText = result.name;
                document.getElementById("criminal-crime").innerText = result.crime;
                document.getElementById("criminal-aadhaar").innerText = result.aadhaar_number;  // Display Aadhaar number
                
                if (result.photo) {
                    let img = document.getElementById("criminal-photo");
                    img.src = "data:image/jpeg;base64," + result.photo;
                    img.style.display = "block";
                    // Add max-width and max-height to control image size
                    img.style.maxWidth = "400px";
                    img.style.maxHeight = "400px";
                    img.style.objectFit = "contain";
                }
                detailsDiv.style.display = "block";
            } else {
                resultDiv.innerHTML = "❌ " + result.message;
            }
        } catch (error) {
            console.error("Search error:", error);
            resultDiv.innerHTML = "❌ Error processing search.";
        }
    };

    reader.readAsDataURL(fileInput.files[0]);
}





function showCriminalAlert() {
    const alert = document.getElementById('criminal-alert');
    alert.classList.add('show');
}





async function startDetection() {
    const video = document.getElementById("camera-feed");
    const resultDiv = document.getElementById("detect-results");
    const detailsDiv = document.getElementById("detect-details");

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();

        async function processFrame() {
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext("2d").drawImage(video, 0, 0);

            try {
                const result = await eel.process_camera_frame(canvas.toDataURL("image/jpeg"))();
                if (result.status === "success") {
                    update_detection_results(result.name, result.crime, result.photo,result.aadhaar_number);
                    detailsDiv.style.display = "block";
                }
            } catch (error) {
                console.error("Frame processing error:", error);
            }

            requestAnimationFrame(processFrame);
        }

        video.onloadedmetadata = () => {
            processFrame();
        };
    } catch (error) {
        console.error("Camera access error:", error);
        resultDiv.innerHTML = "❌ Error accessing camera.";
    }
}


 
 




// Add these functions before the startCamera function:
function updateStatus(message, isError = false) {
    const statusElement = document.getElementById('detection-status');
    statusElement.textContent = message;
    statusElement.style.color = isError ? 'red' : 'green';
}

// Modify the startCamera function:
async function startCamera() {
    try {
        updateStatus('Initializing camera...');
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        });
        const video = document.getElementById('camera-feed');
        video.srcObject = stream;
        await video.play();
        updateStatus('Camera active, detection running');
        processVideoFrame();
        console.log("Camera started successfully");
    } catch (error) {
        console.error('Error accessing camera:', error);
        updateStatus('Camera access error: ' + error.message, true);
        alert('Error accessing camera. Please ensure camera permissions are granted.');
    }
}
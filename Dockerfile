FROM python:3.10-slim

# Set environment flags to prevent multi-threaded compiler memory spikes
ENV MAKEFLAGS="-j1"
ENV MAX_JOBS=1

# Install system dependencies AND precompiled python3-dlib from Debian repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libglib2.0-0 \
    python3-dlib \
    && rm -rf /var/lib/apt-get/lists/*

WORKDIR /app

COPY requirements.txt .

# Install python packages without compiling dlib from scratch
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn Backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]

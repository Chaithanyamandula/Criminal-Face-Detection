FROM python:3.10-slim

# Prevent compiler memory spikes by turning off heavy link-time optimization (LTO)
ENV CFLAGS="-O0"
ENV CXXFLAGS="-O0"
ENV MAKEFLAGS="-j1"
ENV MAX_JOBS=1

# Install standard system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    g++ \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt-get/lists/*

WORKDIR /app

COPY requirements.txt .

# Install python packages with low memory compiler settings
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn Backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]

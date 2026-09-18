FROM python:3.12-slim

# System dependencies: ffmpeg (Whisper audio decoding), tesseract-ocr (lab report OCR),
# default-libmysqlclient-dev + build tools (PyMySQL/cryptography wheels), libgl1 (OpenCV).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads/images /app/uploads/voice /app/uploads/lab_reports /app/uploads/articles /app/uploads/reports \
    && mkdir -p /app/app/ml_artifacts/faiss_index

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

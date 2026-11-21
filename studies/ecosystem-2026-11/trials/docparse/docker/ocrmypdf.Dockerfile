FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-tra ghostscript poppler-utils && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir ocrmypdf && (pip list 2>/dev/null | grep -i ocrmypdf; tesseract --version 2>&1 | head -1) > /versions.txt

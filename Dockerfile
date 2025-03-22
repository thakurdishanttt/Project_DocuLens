# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TESSERACT_PATH=/usr/bin/tesseract \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    tesseract-ocr \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install basic tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install dependencies in smaller batches with fallback mirrors
RUN pip install --no-cache-dir fastapi==0.115.8 uvicorn==0.34.0 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple fastapi==0.115.8 uvicorn==0.34.0

RUN pip install --no-cache-dir pydantic==2.10.6 pydantic-settings==2.7.1 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple pydantic==2.10.6 pydantic-settings==2.7.1

RUN pip install --no-cache-dir supabase==2.12.0 httpx==0.28.1 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple supabase==2.12.0 httpx==0.28.1

RUN pip install --no-cache-dir python-jose==3.3.0 passlib==1.7.4 bcrypt==4.1.2 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple python-jose==3.3.0 passlib==1.7.4 bcrypt==4.1.2

RUN pip install --no-cache-dir llama-extract==0.1.1 llama-parse==0.5.20 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple llama-extract==0.1.1 llama-parse==0.5.20

RUN pip install --no-cache-dir llama-index-core==0.11.23 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple llama-index-core==0.11.23

RUN pip install --no-cache-dir google-generativeai==0.8.4 google-api-python-client==2.160.0 protobuf==5.29.3 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple google-generativeai==0.8.4 google-api-python-client==2.160.0 protobuf==5.29.3

RUN pip install --no-cache-dir transformers==4.40.0 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple transformers==4.40.0

RUN pip install --no-cache-dir torch==2.3.0 || \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.0

RUN pip install --no-cache-dir sentence-transformers==2.7.0 || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple sentence-transformers==2.7.0

RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
